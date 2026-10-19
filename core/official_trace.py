"""Bounded read-only official-reference checking; never infer eligibility."""
import hashlib
import json
import os
import tempfile
import time
from contextlib import contextmanager
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from .collector import RequestBudget, SourcePaused, USER_AGENT, classify_exception, budgeted_read
from .config import load_sources
from .models import Evidence, utc_now
from .pipeline import Pipeline
from .verifier import VerificationEngine


def validate_public_reference(url: str, hosts: set[str]) -> bool:
    try:
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or parsed.hostname not in hosts or parsed.username or parsed.password:
            return False
        if parsed.port not in (None, 443) or parsed.query or parsed.fragment:
            return False
        path = parsed.path
        for _ in range(3):
            path = urllib.parse.unquote(path)
        if '%' in path or '..' in path.split('/'):
            return False
        return not re.search(r'/(login|signin|signup|oauth|authorize|checkout|redeem)(/|$)', path, re.I)
    except ValueError:
        return False


def fetch_public_page(url: str, hosts: set[str], budget: RequestBudget | None = None) -> bytes:
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'text/html'})
    # All reference paths share redirect checks, proxy isolation, and pinned DNS.
    payload = budgeted_read(request, budget, 1_000_000,
                            lambda target: validate_public_reference(target, hosts))
    code = VerificationEngine.classify_fetch_failure(200, payload[:65536].decode('utf-8', errors='replace'))
    if code == 'CAPTCHA_REQUIRED':
        raise SourcePaused(code)
    return payload


@contextmanager
def _trace_publication_lock(path: Path):
    # A kernel-owned lock works without hard-link privileges. Keep the stable
    # lock file: deleting it could let concurrent writers lock different inodes.
    with path.open('a+b') as guard:
        guard.seek(0, os.SEEK_END)
        if guard.tell() == 0:
            guard.write(b'0')
            guard.flush()
        deadline = time.monotonic() + 5
        while True:
            guard.seek(0)
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(guard.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(guard.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise OSError('TRACE_AUDIT_PUBLICATION_BUSY')
                time.sleep(.01)
        try:
            yield
        finally:
            guard.seek(0)
            if os.name == 'nt':
                msvcrt.locking(guard.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(guard.fileno(), fcntl.LOCK_UN)


class OfficialTracer:
    def __init__(self, root: Path, hosts: set[str] | None = None):
        self.root = Path(root)
        self.pipeline = Pipeline(self.root)
        if hosts is None:
            config = json.loads((self.root / 'config' / 'official-trace.json').read_text(encoding='utf-8'))
            hosts = set(config['allowed_hosts'])
        self.hosts = hosts
        self.budget = RequestBudget(self.root / 'data' / 'source-state')
        sources_path = self.root / 'config' / 'sources.yaml'
        if sources_path.exists():
            self.budget.sync_host_pauses(load_sources(sources_path))

    def _write_record(self, event_id: int, record: dict) -> None:
        destination = self.root / 'evidence' / 'official-trace'
        destination.mkdir(parents=True, exist_ok=True)
        serialized = json.dumps(record, ensure_ascii=False, indent=2)
        # This integer event ID can be recycled after a campaign merge. Keep
        # an immutable content-addressed audit copy for every distinct result;
        # retain the original event-id filename as the latest-result view.
        history = destination / 'history'
        history.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
        archived = history / f'{event_id}-{digest}.json'
        # Publish complete bytes, never an open-but-unwritten history file.
        # Serialize the immutable existence check and atomic publication under
        # a kernel lock; no hard-link privileges or partial archive reads.
        fd, temporary = tempfile.mkstemp(prefix='.trace-', suffix='.tmp', dir=history)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8', newline='') as output:
                output.write(serialized)
                output.flush()
                os.fsync(output.fileno())
            with _trace_publication_lock(destination / '.publish.lock'):
                if archived.exists():
                    if archived.read_text(encoding='utf-8') != serialized:
                        raise ValueError('OFFICIAL_TRACE_AUDIT_HASH_COLLISION')
                else:
                    os.replace(temporary, archived)
            # The mutable latest view also publishes a complete temporary file.
            # Use its own temporary inode, separate from immutable history.
            latest_fd, latest_temp = tempfile.mkstemp(prefix='.trace-', suffix='.tmp', dir=destination)
            try:
                with os.fdopen(latest_fd, 'w', encoding='utf-8', newline='') as output:
                    output.write(serialized)
                    output.flush()
                    os.fsync(output.fileno())
                os.replace(latest_temp, destination / f'{event_id}.json')
            finally:
                Path(latest_temp).unlink(missing_ok=True)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def trace(self, event_id: int, expected_event: dict | None = None) -> dict:
        # Ingest releases its candidate transaction before network tracing.
        # A concurrent reindex may have merged this ID in the meantime.
        try:
            event = self.pipeline.db.get_event(event_id)
        except KeyError:
            record = {'checked_at': utc_now(), 'event_id': event_id,
                      'references': [], 'status': 'STALE_EVENT_ID',
                      'error_code': 'EVENT_MERGED_OR_REMOVED'}
            self._write_record(event_id, record)
            return record
        # A merge may delete this numeric ID and the next insert can recycle
        # it. The upstream ingestion snapshot is authoritative for identity.
        identity_fields = ('canonical_key', 'batch_id', 'primary_url', 'first_seen')
        if expected_event is not None and any(
                event[field] != expected_event[field] for field in identity_fields):
            record = {'checked_at': utc_now(), 'event_id': event_id,
                      'references': [], 'status': 'STALE_EVENT_ID',
                      'error_code': 'EVENT_MERGED_OR_REMOVED'}
            self._write_record(event_id, record)
            return record
        metadata = json.loads(event['metadata_json'])
        references = list(metadata.get('official_references', []))
        direct_official = bool(metadata.get('official'))
        direct_urls = {item.url for item in self.pipeline.db.get_evidence(event_id) if item.kind == 'official'}
        if direct_official:
            direct_urls.add(event['primary_url'])
        references = sorted(direct_urls) + references
        results = []
        stale_during_apply = False
        for url in list(dict.fromkeys(references))[:2]:
            if not validate_public_reference(url, self.hosts):
                results.append({'status': 'SKIPPED', 'error_code': 'UNAPPROVED_REFERENCE_URL'})
                continue
            source = {'id': 'official-trace:' + hashlib.sha256(url.encode()).hexdigest()[:24],
                      'endpoint': url, 'interval_minutes': 1440}
            requested = False
            try:
                if not self.budget.acquire(source):
                    results.append({'url': url, 'status': 'SKIPPED', 'error_code': 'REQUEST_BUDGET'})
                    continue
                requested = True
                payload = fetch_public_page(url, self.hosts, self.budget)
                text = payload.decode('utf-8', errors='replace')
                visible = re.sub(r'<(script|style)\b[^>]*>.*?</\1\s*>', '', text, flags=re.S | re.I)
                visible = ' '.join(re.sub(r'<[^>]+>', ' ', visible).split())
                if len(visible) < 20:
                    raise ValueError('OFFICIAL_PAGE_EMPTY_OR_LAYOUT_CHANGED')
                # A community referral does not prove this page concerns the same
                # campaign. Only already trusted direct source pages are official.
                kind = 'official' if url in direct_urls else 'official_reference'
                evidence = Evidence(kind, url, 'official-page:' + url,
                    excerpt=visible[:4000], claims={'open': 'unknown', 'public': 'unknown',
                    'remaining': 'unknown', 'region': 'unknown', 'eligibility': 'unknown',
                    'card_required': 'unknown', 'auto_renew': 'unknown',
                    'body_sha256': hashlib.sha256(payload).hexdigest(),
                    'method': 'public_reference_fetch', 'requires_campaign_review': kind == 'official_reference'})
                try:
                    verified = self.pipeline.apply_evidence(event_id, [evidence],
                                                            expected_event=event)
                except KeyError:
                    # The page may have been read successfully just as a
                    # review merged away the old event ID. It is not a fetch
                    # failure, and none of this proof reached a live event.
                    stale_during_apply = True
                    results.append({'url': url, 'status': 'STALE_EVENT_ID',
                                    'error_code': 'EVENT_MERGED_OR_REMOVED'})
                    break
                results.append({'url': url, 'status': 'FETCHED', 'classification': verified['status']})
            except (SourcePaused, urllib.error.HTTPError) as exc:
                code = str(exc) if isinstance(exc, SourcePaused) else VerificationEngine.classify_fetch_failure(exc.code, '')
                if code == 'REQUEST_BUDGET':
                    results.append({'url': url, 'status': 'SKIPPED', 'error_code': code})
                    continue
                barrier = isinstance(exc, SourcePaused) or code in ('BLOCKED_403', 'RATE_LIMITED_429', 'CAPTCHA_REQUIRED')
                if barrier and requested:
                    retry = 3600 if code == 'RATE_LIMITED_429' else None
                    self.budget.pause(source, code, retry)
                results.append({'url': url, 'status': 'PAUSED' if barrier else 'FAILED', 'error_code': code})
                if isinstance(exc, urllib.error.HTTPError):
                    exc.close()
            except Exception as exc:
                results.append({'url': url, 'status': 'FAILED', 'error_code': classify_exception(exc)})
        # A campaign may also merge the event after a permitted page fetch or
        # after apply_evidence() commits. Never present a missing event as
        # verified, and keep an auditable result instead of crashing ingest.
        if stale_during_apply:
            current_status = 'STALE_EVENT_ID'
        else:
            try:
                current = self.pipeline.db.get_event(event_id)
                current_status = (current['status'] if all(
                    current[field] == event[field] for field in identity_fields)
                    else 'STALE_EVENT_ID')
            except KeyError:
                current_status = 'STALE_EVENT_ID'
        record = {'checked_at': utc_now(), 'event_id': event_id,
                  'references': results, 'status': current_status}
        if current_status == 'STALE_EVENT_ID':
            record['error_code'] = 'EVENT_MERGED_OR_REMOVED'
        self._write_record(event_id, record)
        return record
