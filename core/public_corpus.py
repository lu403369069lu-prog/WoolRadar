"""Keep bounded, unauthenticated samples for independent recall review."""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import utc_now

MAX_BYTES = 8_000_000

# Only structured public resource selectors are retained. Unknown selectors
# may change activity identity, so dropping one makes the row ineligible for a
# new blind denominator. Known transport trackers do not change identity.
_FUNCTIONAL_QUERY = {'batch','offer','ref','utm_campaign','program','plan',
                     'campaign','edition','round','page','id','lang','locale',
                     'category','region','product','event','promo','coupon','sku'}
_TRACKING_QUERY = {'utm_source','utm_medium','utm_term','utm_content','fbclid',
                   'gclid','msclkid','mc_cid','mc_eid'}
_PRIVATE_VALUE = re.compile(r'(?i)(?:@|\d{13,}|token|secret|bearer|password|session)')

def _semantic_query(query: str) -> tuple[str, bool]:
    kept = {}
    preserved = True
    for original_key, value in parse_qsl(query, keep_blank_values=True, max_num_fields=64):
        key = original_key.lower()
        if key in _TRACKING_QUERY:
            continue
        # Application selectors may be case-sensitive at the origin. We may
        # redact/normalize their display, but may not certify URL identity.
        if original_key != key:
            preserved = False
        if (key not in _FUNCTIONAL_QUERY or not re.fullmatch(r'[A-Za-z0-9._~-]{1,80}', value)
                or _PRIVATE_VALUE.search(value)):
            preserved = False
            continue
        # Repeated selector keys may have server-specific array/first/last
        # semantics, even if their values match. Never collapse them as gold.
        if key in kept:
            preserved = False
        else:
            kept[key] = value
    return urlencode(sorted(kept.items())), preserved

def _clean_url_identity(value: str) -> tuple[str, bool]:
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
            return '', False
        # Port access validates malformed ports without making a network request.
        parsed.port
        query, preserved = _semantic_query(parsed.query)
        if parsed.username is not None or parsed.password is not None:
            preserved = False
        fragment = ''
        if parsed.fragment:
            route, separator, fragment_query = parsed.fragment.partition('?')
            if re.fullmatch(r'(?:/|!/)[A-Za-z0-9/_~.\-]*', route):
                clean_query, route_preserved = _semantic_query(fragment_query)
                if route_preserved:
                    fragment = route + ('?' + clean_query if clean_query else '')
                else:
                    preserved = False
            else:
                preserved = False
        return urlunsplit((parsed.scheme, parsed.netloc.rsplit('@',1)[-1], parsed.path, query, fragment)), preserved
    except (ValueError, UnicodeError):
        return '[invalid URL redacted]', False

def _clean_url(value: str) -> str:
    return _clean_url_identity(value)[0]

def _clean_text(value: str) -> str:
    return re.sub(r'https?://[^\s<>"\']+', lambda match: _clean_url(match.group(0)), value, flags=re.I)


def record_public_sample(root: Path, node: str, source: dict, rows: list[dict], accepted: list[bool]) -> Path | None:
    if source.get('auth') not in {'public_feed', 'public_page', 'public_api'} or source.get('kind') not in {'rss', 'html', 'hn_api'}:
        return None
    source_id = source.get('id', '')
    if not isinstance(source_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', source_id):
        return None
    if len(rows) != len(accepted):
        raise ValueError('CORPUS_DECISION_COUNT_MISMATCH')
    directory = Path(root) / 'data/public-corpus'
    if not directory.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('CORPUS_PATH_OUTSIDE_ROOT')
    directory.mkdir(parents=True, exist_ok=True)
    sample_rows = []
    for index, row in enumerate(rows[:500]):
        original = str(row.get('url', ''))
        url, identity_preserved = _clean_url_identity(original)
        title, summary = str(row.get('title', '')), str(row.get('summary', ''))
        clean_title, clean_summary = _clean_text(title), _clean_text(summary)
        sample_rows.append({'index': index, 'title': clean_title[:512], 'url': url[:2048],
                            'summary': clean_summary[:20000], 'published_at': str(row.get('published_at', ''))[:80],
                            'accepted': bool(accepted[index]), 'url_sanitized': url[:2048] != original,
                            'url_identity_preserved': identity_preserved and len(url) <= 2048,
                            'text_url_redacted': clean_title != title or clean_summary != summary,
                            'content_truncated': len(clean_title) > 512 or len(clean_summary) > 20000 or len(url) > 2048})
    payload = {'schema_version': 1, 'sampled_at': utc_now(), 'node': str(node)[:64], 'source_id': source_id,
               'platform': str(source.get('platform', ''))[:128], 'public_only': True,
               'fetched_count': len(rows), 'stored_count': len(sample_rows), 'rows_truncated': len(rows) > 500,
               'rows': sample_rows, 'max_utf8_bytes': MAX_BYTES,
               'limits': 'Latest bounded public sample only; redactions/truncations marked; not a full platform or time-window denominator'}
    while True:
        encoded = json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')
        if len(encoded) <= MAX_BYTES:
            break
        keep = max(0, min(len(payload['rows'])-1, int(len(payload['rows'])*MAX_BYTES/len(encoded))-1))
        payload['rows'] = payload['rows'][:keep]
        payload['stored_count'] = keep
        payload['rows_truncated'] = True
    target = directory / (source_id + '.json')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='wb', dir=directory,
                                         prefix=source_id + '-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(encoded)
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return target
