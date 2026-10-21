"""Automatic processing must retain explicit terminal campaign decisions."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from core.models import Candidate, Evidence, Status
from core.pipeline import Pipeline
from core.report import ReportGenerator


def candidate() -> Candidate:
    return Candidate('synthetic', 'fixture', 'Synthetic public developer grant',
                     'https://offer.example/program-2026', source_kind='official',
                     metadata={'evidence_claims': {'open': True, 'public': True}})


def proof() -> Evidence:
    return Evidence('official', 'https://offer.example/terms-2026', 'offer-official',
                    claims={'open': True, 'public': True})


class PipelineTerminalMonotonicTests(unittest.TestCase):
    def test_apply_evidence_does_not_reopen_terminal_or_emit_verified_notice(self):
        for terminal in (Status.REDEEMED, Status.EXPIRED, Status.FAILED, Status.CONFLICTED):
            with self.subTest(terminal=terminal), tempfile.TemporaryDirectory() as td:
                pipeline = Pipeline(Path(td))
                event_id = pipeline.db.upsert_candidate(candidate()).event_id
                pipeline.db.set_status(event_id, terminal, 'manual close')
                with pipeline.db.connect() as conn:
                    count_before = conn.execute('SELECT count(*) FROM status_history').fetchone()[0]
                result = pipeline.apply_evidence(event_id, [proof()])
                self.assertEqual(result['status'], terminal.value)
                self.assertEqual(pipeline.db.get_event(event_id)['status'], terminal.value)
                self.assertEqual(pipeline.db.get_event(event_id)['claim_scope'], 'NONE')
                with pipeline.db.connect() as conn:
                    self.assertEqual(conn.execute('SELECT count(*) FROM status_history').fetchone()[0], count_before)
                    self.assertEqual(conn.execute("SELECT count(*) FROM notifications WHERE channel='local-verified'").fetchone()[0], 0)

    def test_repeat_ingest_does_not_reopen_terminal_or_emit_verified_notice(self):
        for terminal in (Status.REDEEMED, Status.EXPIRED, Status.FAILED, Status.CONFLICTED):
            with self.subTest(terminal=terminal), tempfile.TemporaryDirectory() as td:
                root = Path(td)
                pipeline = Pipeline(root)
                event_id = pipeline.db.upsert_candidate(candidate()).event_id
                pipeline.db.set_status(event_id, terminal, 'manual close')
                inbox = root / 'data' / 'inbox'
                inbox.mkdir(parents=True, exist_ok=True)
                (inbox / 'synthetic.jsonl').write_text(json.dumps(candidate().to_dict()) + '\n', encoding='utf-8')
                result = pipeline.ingest_node('synthetic')
                self.assertEqual(result['ingested'], 1)
                self.assertEqual(pipeline.db.get_event(event_id)['status'], terminal.value)
                self.assertEqual(pipeline.db.get_event(event_id)['claim_scope'], 'NONE')
                with pipeline.db.connect() as conn:
                    self.assertEqual(conn.execute("SELECT count(*) FROM notifications WHERE channel='local-verified'").fetchone()[0], 0)

    def test_nonterminal_can_be_promoted_and_manual_reopening_is_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            pipeline = Pipeline(Path(td))
            event_id = pipeline.db.upsert_candidate(candidate()).event_id
            self.assertEqual(pipeline.apply_evidence(event_id, [proof()])['status'], 'CLAIMABLE')
            pipeline.db.set_status(event_id, Status.REDEEMED, 'manual redeemed')
            pipeline.db.set_status(event_id, Status.UNKNOWN, 'manual reopen')
            self.assertEqual(pipeline.apply_evidence(event_id, [proof()])['status'], 'CLAIMABLE')

    def test_report_uses_retained_terminal_when_automatic_refresh_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pipeline = Pipeline(root)
            event_id = pipeline.db.upsert_candidate(candidate()).event_id
            pipeline.db.add_evidence(event_id, proof())
            pipeline.db.set_status(event_id, Status.CLAIMABLE, 'stale scope', 'STALE')
            real_set_status = pipeline.db.set_status

            def manual_close_before_refresh(event_id, status, reason, claim_scope='NONE', *, automatic=False):
                if automatic:
                    real_set_status(event_id, Status.EXPIRED, 'manual expiry')
                return real_set_status(event_id, status, reason, claim_scope, automatic=automatic)

            event = pipeline.db.get_event(event_id)
            date = datetime.fromisoformat(event['first_seen'].replace('Z', '+00:00')).astimezone(
                timezone(timedelta(hours=8))).date().isoformat()
            with patch.object(pipeline.db, 'set_status', side_effect=manual_close_before_refresh):
                output = ReportGenerator(pipeline.db, root / 'reports').generate(date)
            payload = json.loads(output.json.read_text(encoding='utf-8'))
            actual = next(e for e in payload['events'] if e['id'] == event_id)
            self.assertEqual((actual['status'], actual['claim_scope']), ('EXPIRED', 'NONE'))
            self.assertEqual(pipeline.db.get_event(event_id)['status'], 'EXPIRED')


if __name__ == '__main__':
    unittest.main()
