"""Produce a local-only, fail-closed preview of WoolRadar's daily JSON.

Not a publisher: no network, secrets, account reads, or implicit filesystem paths.
The resulting file is NOT verified current availability and MUST be reviewed
before anyone shares it with a ChatGPT task or outside the machine.
"""
from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import math
import os
import re
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

MAX_INPUT = 10 * 1024 * 1024
BAD_TEXT = re.compile(r"(?i)(?:\b[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}\b|\b(?:bearer|secret|token|password|api[_-]?key|session|cookie)\b|\b\d{13,19}\b|\b1[3-9]\d{9}\b)")
BAD_SEGMENT = re.compile(r"(?i)(?:^|[-_])(auth|callback|token|secret|reset|password|login|checkout|invoice|payment|session|account)(?:$|[-_])")
# Public previews must not expose opaque identifiers under credential/account
# collections. Those routes often put a bearer token or personal ID in the
# following path segment, even when no query string is present.
BAD_PRIVATE_COLLECTION = frozenset({
    'tokens', 'secrets', 'sessions', 'accounts', 'users', 'credentials',
    'passwords', 'api-keys', 'api_keys', 'apikeys',
})
# Browser URL parsers accept legacy shortened, octal and hexadecimal IPv4
# addresses that Python's ipaddress module rejects. Fail closed on a hostname
# made entirely of numeric IPv4-style components, even when malformed.
NUMERIC_IPV4_COMPONENT = re.compile(r'(?:[0-9]+|0x[0-9a-f]+)\Z')
ALLOWED_STATUS = {'DISCOVERED', 'CROSS_CHECKED', 'OFFICIAL_VERIFIED', 'CLAIMABLE', 'UNKNOWN', 'CONFLICTED', 'EXPIRED', 'FAILED', 'REDEEMED'}
BOOL_FIELDS = ('public', 'open', 'card_required', 'account_required', 'auto_renew')
REGIONS = {'CN', 'US', 'EU', 'GLOBAL', 'MAINLAND_CHINA', 'UNKNOWN'}


def public_url(raw: object) -> str | None:
    if not isinstance(raw, str) or not raw or len(raw) > 512 or re.search(r'\s|[\\<>]', raw):
        return None
    try:
        raw.encode('utf-8')  # unpaired surrogates are not a publishable URL
        parts = urlsplit(raw)
        if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password or parts.port not in (None, 443):
            return None
        host = parts.hostname.lower().rstrip('.')
        if host in ('localhost', 'local') or '.' not in host or BAD_TEXT.search(host):
            return None
        if all(NUMERIC_IPV4_COMPONENT.fullmatch(piece) for piece in host.split('.')):
            return None
        try:
            ipaddress.ip_address(host)
            return None
        except ValueError:
            pass
        # Inspect the decoded route, including nested encoding. Fail closed when
        # more decoding would be needed; never inspect only its encoded spelling.
        route = parts.path
        for _ in range(3):
            decoded = unquote(route, errors='strict')
            if decoded == route:
                break
            route = decoded
        if ('%' in route or re.search(r'\s|[\\<>]', route)
            or any(unicodedata.category(ch) in {'Cc', 'Cf', 'Cs', 'Zl', 'Zp'}
                   for ch in route)):
            return None
        if parts.query or parts.fragment or BAD_TEXT.search(route):
            return None
        if any(BAD_SEGMENT.search(piece) or piece.lower() in BAD_PRIVATE_COLLECTION
               for piece in route.split('/')):
            return None
        if not re.fullmatch(r'[a-z0-9.-]+', host) or '..' in host:
            return None
        return urlunsplit(('https', host, parts.path or '/', '', ''))
    except (ValueError, TypeError, UnicodeError):
        return None


def public_title(raw: object) -> str | None:
    if not isinstance(raw, str) or len(raw) < 3 or len(raw) > 160:
        return None
    # Unicode format controls (including bidi overrides/isolates and zero-width
    # characters), C1 controls and Unicode line/paragraph separators can
    # visually forge the final brief without containing ASCII newlines.
    if (any(unicodedata.category(ch) in {'Cc', 'Cf', 'Cs', 'Zl', 'Zp'} for ch in raw)
        or BAD_TEXT.search(raw) or '://' in raw
        or re.search(r'(?i)(?:[a-z]:[\\/]|\\\\|/(?:home|Users|private|tmp)/)', raw)):
        return None
    return raw


def timestamp(raw: object) -> str | None:
    if not isinstance(raw, str) or len(raw) > 40:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            return None
        return dt.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')
    except (ValueError, OverflowError):
        return None


def public_claims(raw: object) -> dict:
    obj = raw if isinstance(raw, dict) else {}
    result = {key: obj[key] for key in BOOL_FIELDS if type(obj.get(key)) is bool}
    region = obj.get('region')
    if isinstance(region, str) and region.upper() in REGIONS:
        result['region'] = region.upper()
    remaining = obj.get('remaining')
    if type(remaining) is int and 0 <= remaining <= 1000000:
        result['remaining'] = remaining
    expiry = timestamp(obj.get('expires_at'))
    if expiry:
        result['expires_at'] = expiry
    return result


def build_preview(report: dict, report_hash: str, now: datetime | None = None) -> dict:
    if not isinstance(report, dict) or not isinstance(report.get('events'), list):
        raise ValueError('daily report must be an object with an events array')
    raw_date = report.get('date')
    try:
        if not isinstance(raw_date, str) or datetime.strptime(raw_date, '%Y-%m-%d').date().isoformat() != raw_date:
            raise ValueError('invalid report date')
    except ValueError as exc:
        raise ValueError('invalid report date') from exc
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError('now must include timezone')
    now = now.astimezone(timezone.utc)
    # The production report stores *all* events, including rows that the
    # reviewed noise ledger deliberately suppresses from the Markdown brief.
    # Never resurrect those rows in a downstream export.
    audit_enabled = 'noise_audit' in report
    if audit_enabled and not isinstance(report['noise_audit'], dict):
        raise ValueError('invalid noise audit summary')
    records = []
    seen = set()
    for row in report['events']:
        if not isinstance(row, dict):
            continue
        audit = row.get('report_audit')
        if audit_enabled or 'report_audit' in row:
            if not isinstance(audit, dict) or audit.get('excluded') is not False:
                continue
        url = public_url(row.get('primary_url'))
        title = public_title(row.get('title'))
        status = row.get('status')
        if url is None or title is None or not isinstance(status, str) or status not in ALLOWED_STATUS:
            continue
        batch_id = row.get('batch_id', '')
        if not isinstance(batch_id, str) or len(batch_id) > 128:
            continue
        try:
            batch_bytes = batch_id.encode('utf-8')
        except UnicodeEncodeError:
            continue
        identity = hashlib.sha256(url.encode('utf-8') + b'\0' + batch_bytes).hexdigest()[:24]
        if identity in seen:
            continue
        seen.add(identity)
        official = []
        for ev in row.get('evidence', []) if isinstance(row.get('evidence'), list) else []:
            if not isinstance(ev, dict) or ev.get('kind') != 'official':
                continue
            evidence_url = public_url(ev.get('url'))
            checked = timestamp(ev.get('checked_at'))
            # A future-dated recheck cannot be evidence for this snapshot.
            if evidence_url and checked and datetime.fromisoformat(checked.replace('Z', '+00:00')) <= now:
                official.append({'url': evidence_url, 'checked_at': checked, 'claims': public_claims(ev.get('claims'))})
        # This is a local report snapshot. Even a recent public claim never
        # establishes the user's own account eligibility or current live stock.
        records.append({
            'event_key': identity,
            'title': title,
            'public_url': url,
            'reported_status': status,
            'publication_lane': 'independent_official_recheck_required',
            'personal_eligibility': 'UNKNOWN',
            'batch_key': hashlib.sha256(batch_bytes).hexdigest()[:16] if batch_bytes else None,
            'published_at': timestamp(row.get('published_at')),
            'first_seen': timestamp(row.get('first_seen')),
            'official_evidence': official,
        })
    return {
        'schema_version': 1,
        'source_type': 'LOCAL_REDACTED_PREVIEW_NOT_PUBLISHED',
        'report_date': raw_date,
        'generated_at': now.isoformat().replace('+00:00', 'Z'),
        'source_report_sha256': report_hash,
        'runtime_provenance_verified': False,
        'public_application_live_verified': False,
        'requires_operator_review_before_sharing': True,
        'count': {'input_events': len(report['events']), 'exported_events': len(records), 'skipped_or_duplicate': len(report['events']) - len(records)},
        'events': records,
    }


def _strict_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('ambiguous duplicate input field')
        result[key] = value
    return result


def _reject_json_constant(_):
    raise ValueError('nonstandard input number')


def _finite_json_float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError('nonfinite input number')
    return parsed


def parse_daily_json(raw: bytes) -> dict:
    """Fail closed on ambiguous, non-UTF-8 or excessively nested local reports."""
    if not isinstance(raw, bytes) or len(raw) > MAX_INPUT:
        raise ValueError('invalid daily report input size')
    try:
        text = raw.decode('utf-8', errors='strict')
        parsed = json.loads(text, object_pairs_hook=_strict_json_object,
                            parse_constant=_reject_json_constant, parse_float=_finite_json_float)
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise ValueError('invalid or ambiguous daily report JSON') from exc
    if not isinstance(parsed, dict):
        raise ValueError('daily report root must be an object')
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path, help='Explicit local WoolRadar daily JSON path')
    parser.add_argument('--output', required=True, type=Path, help='New local-only preview path, never overwritten')
    args = parser.parse_args(argv)
    source, target = args.input.resolve(strict=True), args.output.absolute()
    if source == target or target.is_symlink() or target.exists():
        parser.error('output must be a new regular path distinct from input')
    if source.stat().st_size > MAX_INPUT:
        parser.error('input daily report exceeds 10 MiB safety limit')
    raw = source.read_bytes()
    payload = build_preview(parse_daily_json(raw), hashlib.sha256(raw).hexdigest())
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, 'O_NOFOLLOW', 0)
    fd = os.open(target, flags, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as file:
            json.dump(payload, file, ensure_ascii=False, indent=2)
            file.write('\n')
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    print(f"Local preview created; exported={payload['count']['exported_events']}, skipped={payload['count']['skipped_or_duplicate']}. NOT PUBLISHED. Review manually before sharing.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
