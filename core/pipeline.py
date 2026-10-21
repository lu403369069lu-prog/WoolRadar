from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit

from .db import Database
from .dedup import canonical_key, reviewed_campaign_url
from .models import Candidate, Evidence
from .verifier import VerificationEngine
from .notify import NotificationQueue


class Pipeline:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.db = Database(self.root / 'data' / 'woolradar.db')
        self.verifier = VerificationEngine()
        self.notifications = NotificationQueue(self.db)

    def notification_policy(self) -> dict:
        path = self.root / 'config' / 'security-policy.json'
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

    def queue_verified(self, event_id: int, status: str):
        if status != 'CLAIMABLE':
            return
        event = self.db.get_event(event_id)
        message = f"【官方证据支持公开申请，非个人资格保证】{event['title']}\n{event['primary_url']}\n范围：{event['claim_scope']}"
        self.notifications.enqueue(event_id, event['batch_id'], 'local-verified', message)
        if self.notification_policy().get('telegram_send_enabled', False):
            self.notifications.enqueue(event_id, event['batch_id'], 'telegram-verified', message)

    def ingest_node(self, node: str) -> dict:
        items_path = self.root / 'data' / 'inbox' / f'{node}.jsonl'
        status_path = self.root / 'data' / 'status' / f'{node}.json'
        candidates: list[Candidate] = []
        if items_path.exists():
            for line in items_path.read_text(encoding='utf-8').splitlines():
                if line.strip():
                    candidates.append(Candidate.from_dict(json.loads(line)))

        notify_count = 0
        # Pin identity while ingest still holds the SQLite writer reservation.
        official_events = {}
        trace_errors = []
        for candidate in candidates:
            # Reserve the writer through every event-ID reference; upsert alone
            # cannot stop a concurrent reindex deleting its returned event.
            with self.db.candidate_transaction():
                stored = self.db.upsert_candidate(candidate)
                if stored.notify:
                    self.notifications.enqueue(stored.event_id, candidate.batch_id, 'local-discovery',
                        f"【新发现，尚未核实】{candidate.title}\n{candidate.url}")
                provenance = candidate.metadata.get('provenance_key') or 'unverified-campaign:' + canonical_key(candidate)
                reviewed = reviewed_campaign_url(candidate.metadata.get('campaign_review'), candidate.url, candidate.title)
                if reviewed:
                    provenance = 'reviewed-campaign:' + reviewed
                claims = candidate.metadata.get('evidence_claims', {})
                self.db.add_evidence(stored.event_id, Evidence(
                    candidate.source_kind, candidate.url, provenance, excerpt=candidate.summary[:1000], claims=claims))
                evidence = self.db.get_evidence(stored.event_id)
                result = self.verifier.evaluate(candidate, evidence)
                effective = self.db.set_status(stored.event_id, result.status, result.reason,
                                               result.claim_scope, automatic=True)
                self.queue_verified(stored.event_id, effective.value)
                if candidate.source_kind == 'official':
                    official_snapshot = self.db.get_event(stored.event_id)
            if stored.notify:
                notify_count += 1
            if candidate.source_kind == 'official':
                official_events.setdefault(stored.event_id, official_snapshot)

        trace_config = self.root / 'config' / 'official-trace.json'
        if trace_config.exists():
            trace_policy = json.loads(trace_config.read_text(encoding='utf-8'))
            if trace_policy.get('enabled', False) and official_events:
                from .official_trace import OfficialTracer
                tracer = OfficialTracer(self.root)
                for event_id, snapshot in list(official_events.items())[:max(0, min(2, int(trace_policy.get('max_per_node_run', 1))))]:
                    trace_result = tracer.trace(event_id, expected_event=snapshot)
                    if isinstance(trace_result, dict) and trace_result.get('status') == 'STALE_EVENT_ID':
                        trace_errors.append({'source': f'official-trace:{event_id}',
                            'status': 'FAILED', 'error_code': 'STALE_EVENT_ID'})

        source_statuses = []
        if status_path.exists():
            source_statuses = json.loads(status_path.read_text(encoding='utf-8')).get('sources', [])
        # The official trace can lose its old event ID to a concurrent reviewed
        # campaign merge. Do not report the whole node as OK in that case.
        source_statuses.extend(trace_errors)
        failed = [item for item in source_statuses if item.get('status') == 'FAILED']
        paused = [item for item in source_statuses if item.get('status') == 'PAUSED']
        if (failed or paused) and candidates:
            run_status = 'PARTIAL'
        elif failed:
            run_status = 'FAILED'
        elif paused and not candidates:
            run_status = 'PAUSED'
        elif source_statuses and all(item.get('status') == 'SKIPPED' for item in source_statuses):
            run_status = 'SKIPPED'
        else:
            run_status = 'OK'
        error_code = ','.join(sorted({item.get('error_code', '') for item in failed + paused if item.get('error_code')}))
        self.db.record_node_run(node, run_status, len(candidates), error_code,
                                json.dumps(source_statuses, ensure_ascii=False)[:4000])
        self.notifications.record_health(node, run_status, error_code)
        self.notifications.flush(self.notification_policy(), local_dir=self.root / 'reports' / 'notifications')
        return {'node': node, 'ingested': len(candidates), 'notify': notify_count,
                'status': run_status, 'error_code': error_code}

    def apply_evidence(self, event_id: int, evidence_items: list[Evidence],
                       expected_event: dict | None = None) -> dict:
        # This path runs after official-page fetching as well as from direct
        # evidence updates. A concurrent campaign reindex can otherwise merge
        # away event_id between get_event(), add_evidence() and queue_verified().
        # Keep only local SQLite operations under the same writer reservation;
        # network fetches and actual notification sending remain outside.
        with self.db.candidate_transaction():
            event = self.db.get_event(event_id)
            # A deleted INTEGER PRIMARY KEY can be reused for another campaign.
            # Refuse evidence if the row no longer matches the ingestion snapshot.
            identity_fields = ('canonical_key', 'batch_id', 'primary_url', 'first_seen')
            if expected_event is not None and any(
                    event[field] != expected_event[field] for field in identity_fields):
                raise KeyError(event_id)
            for item in evidence_items:
                self.db.add_evidence(event_id, item)
            candidate = Candidate(
                node=event['node'], source=event['source'], title=event['title'],
                url=event['primary_url'], published_at=event['published_at'] or '',
                batch_id=event['batch_id'] or '',
            )
            result = self.verifier.evaluate(candidate, self.db.get_evidence(event_id))
            effective = self.db.set_status(event_id, result.status, result.reason,
                                           result.claim_scope, automatic=True)
            self.queue_verified(event_id, effective.value)
            retained = effective != result.status
            return {
                'event_id': event_id,
                'status': effective.value,
                'reason': '终态已锁定，自动证据只记录、不变更状态' if retained else result.reason,
                'claim_scope': self.db.get_event(event_id)['claim_scope'],
                'independent_evidence_count': result.independent_evidence_count,
                'unknown_capacity': result.unknown_capacity,
            }
