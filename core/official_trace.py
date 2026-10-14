"""Bounded read-only official-reference checking; never infer eligibility."""
import hashlib
import json
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
    if budget is not None:
        request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'text/html'})
        return budgeted_read(request, budget, 1_000_000, lambda target: validate_public_reference(target, hosts))
    class CheckedRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            if not validate_public_reference(newurl, hosts):
                raise SourcePaused('UNAPPROVED_REFERENCE_REDIRECT')
            return super().redirect_request(req, fp, code, msg, headers, newurl)
    if not validate_public_reference(url, hosts):
        raise SourcePaused('UNAPPROVED_REFERENCE_URL')
    opener = urllib.request.build_opener(CheckedRedirect())
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'text/html'})
    with opener.open(request, timeout=20) as response:
        payload = response.read(1_000_000)
    code = VerificationEngine.classify_fetch_failure(200, payload[:65536].decode('utf-8', errors='replace'))
    if code == 'CAPTCHA_REQUIRED':
        raise SourcePaused(code)
    return payload


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

    def trace(self, event_id: int) -> dict:
        event = self.pipeline.db.get_event(event_id)
        metadata = json.loads(event['metadata_json'])
        references = list(metadata.get('official_references', []))
        direct_official = bool(metadata.get('official'))
        direct_urls = {item.url for item in self.pipeline.db.get_evidence(event_id) if item.kind == 'official'}
        if direct_official:
            direct_urls.add(event['primary_url'])
        references = sorted(direct_urls) + references
        results = []
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
                verified = self.pipeline.apply_evidence(event_id, [evidence])
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
        record = {'checked_at': utc_now(), 'event_id': event_id, 'references': results,
                  'status': self.pipeline.db.get_event(event_id)['status']}
        destination = self.root / 'evidence' / 'official-trace'
        destination.mkdir(parents=True, exist_ok=True)
        (destination / f'{event_id}.json').write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        return record
