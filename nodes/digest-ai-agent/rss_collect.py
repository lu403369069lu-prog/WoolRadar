"""Invoke the installed upstream RSS provider with explicit failure reporting."""
import json
import logging
import sys
from pathlib import Path
import httpx
from unittest.mock import patch

from newsbrief.sources.rss import RSSProvider
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from core.verifier import VerificationEngine
from core.collector import RequestBudget, SourcePaused


class CaptureWarnings(logging.Handler):
    def __init__(self):
        super().__init__(logging.WARNING)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    capture = CaptureWarnings()
    logging.getLogger('newsbrief.sources.rss').addHandler(capture)
    barrier = {}
    budget = RequestBudget(Path(sys.argv[2]) / 'data' / 'source-state') if len(sys.argv) > 2 else None
    original_client = httpx.Client
    class GuardedClient(original_client):
        def send(self, request, *args, **kwargs):
            if budget is not None:
                try:
                    if not budget.acquire_http(str(request.url)):
                        raise SourcePaused('REQUEST_BUDGET')
                except SourcePaused as exc:
                    barrier['error_code'] = str(exc)
                    raise RuntimeError(str(exc)) from None
            kwargs['follow_redirects'] = False
            response = super().send(request, *args, **kwargs)
            if response.is_redirect:
                barrier['error_code'] = 'RSS_REDIRECT_REQUIRES_REVIEW'
                raise RuntimeError(barrier['error_code'])
            return response
        def get(self, *args, **kwargs):
            response = super().get(*args, **kwargs)
            sample = response.text[:65536].lower()
            if VerificationEngine.classify_fetch_failure(response.status_code, sample) == 'CAPTCHA_REQUIRED':
                barrier['error_code'] = 'CAPTCHA_REQUIRED'
            elif response.status_code in (403, 429):
                barrier['error_code'] = 'BLOCKED_403' if response.status_code == 403 else 'RATE_LIMITED_429'
                try:
                    barrier['retry_seconds'] = max(1800, int(response.headers.get('Retry-After', '1800')))
                except ValueError:
                    barrier['retry_seconds'] = 3600
            if barrier:
                raise RuntimeError(barrier['error_code'])
            return response
    with patch('newsbrief.sources.rss.httpx.Client', GuardedClient):
        articles = list(RSSProvider().fetch({'url': sys.argv[1], 'category': 'developer-perks'}, limit=100))
    rows = [{'title': item.title, 'url': item.url, 'summary': item.snippet,
             'published_at': item.published_at.isoformat() if item.published_at else ''}
            for item in articles]
    # Never pass upstream exception bodies or redirects to logs.
    error = barrier or ({'error_code': 'UPSTREAM_RSS_FAILED'} if capture.messages and not rows else {})
    print(json.dumps({'rows': rows, 'error': error}, ensure_ascii=False))
    return 2 if error else 0


if __name__ == '__main__':
    raise SystemExit(main())
