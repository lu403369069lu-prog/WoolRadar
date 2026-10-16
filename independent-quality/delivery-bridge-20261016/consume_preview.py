"""Inspect an explicitly supplied WoolRadar preview, never publish it.

This is a *review queue*, not a confirmed-offer feed or runtime attestation.
An independent channel must provide each expected preview file SHA-256.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from redact_daily import public_url, public_title, public_claims

class UnsafePreview(ValueError):
    pass

TOP = {'schema_version', 'source_type', 'report_date', 'generated_at',
       'source_report_sha256', 'runtime_provenance_verified',
       'public_application_live_verified', 'requires_operator_review_before_sharing',
       'count', 'events'}
EVENT = {'event_key', 'title', 'public_url', 'reported_status', 'publication_lane',
         'personal_eligibility', 'batch_key', 'published_at', 'first_seen', 'official_evidence'}
PROOF = {'url', 'checked_at', 'claims'}
SHA64 = re.compile('[0-9a-f]{64}\\Z')
SHA24 = re.compile('[0-9a-f]{24}\\Z')


def _time(value):
    if not isinstance(value, str) or len(value) > 40:
        raise UnsafePreview('invalid time')
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as exc:
        raise UnsafePreview('invalid time') from exc
    if dt.tzinfo is None:
        raise UnsafePreview('unscoped time')
    try:
        return dt.astimezone(timezone.utc)
    except (ValueError, OverflowError) as exc:
        raise UnsafePreview('invalid time') from exc


def validate(raw: bytes, expected_digest: str, *, now: datetime | None = None):
    if not isinstance(expected_digest, str) or not SHA64.fullmatch(expected_digest):
        raise UnsafePreview('independent digest required')
    if len(raw) > 2 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != expected_digest:
        raise UnsafePreview('digest mismatch or oversized preview')
    try:
        obj = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise UnsafePreview('invalid preview json') from exc
    if not isinstance(obj, dict) or set(obj) != TOP:
        raise UnsafePreview('unexpected preview fields')
    if type(obj['schema_version']) is not int or obj['schema_version'] != 1:
        raise UnsafePreview('schema mismatch')
    if (obj['source_type'] != 'LOCAL_REDACTED_PREVIEW_NOT_PUBLISHED'
        or obj['runtime_provenance_verified'] is not False
        or obj['public_application_live_verified'] is not False
        or obj['requires_operator_review_before_sharing'] is not True):
        raise UnsafePreview('untrusted or promoted origin')
    if not isinstance(obj['source_report_sha256'], str) or not SHA64.fullmatch(obj['source_report_sha256']):
        raise UnsafePreview('bad source fingerprint')
    now = now or datetime.now(timezone.utc)
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise UnsafePreview('invalid clock')
    now = now.astimezone(timezone.utc)
    generated = _time(obj['generated_at'])
    if not timedelta(0) <= now - generated <= timedelta(hours=36):
        raise UnsafePreview('stale or future preview')
    try:
        if not isinstance(obj['report_date'], str):
            raise ValueError('not a date')
        day = date.fromisoformat(obj['report_date'])
        if day.isoformat() != obj['report_date']:
            raise ValueError('noncanonical date')
    except ValueError as exc:
        raise UnsafePreview('bad report date') from exc
    shanghai_today = now.astimezone(ZoneInfo('Asia/Shanghai')).date()
    if day not in (shanghai_today, shanghai_today - timedelta(days=1)):
        raise UnsafePreview('stale report day')
    if not isinstance(obj['events'], list) or not isinstance(obj['count'], dict):
        raise UnsafePreview('invalid events')
    if set(obj['count']) != {'input_events', 'exported_events', 'skipped_or_duplicate'}:
        raise UnsafePreview('bad counters')
    counts = obj['count']
    if any(type(counts[k]) is not int or counts[k] < 0 for k in counts):
        raise UnsafePreview('bad counters')
    if counts['exported_events'] != len(obj['events']) or counts['input_events'] != counts['exported_events'] + counts['skipped_or_duplicate']:
        raise UnsafePreview('counter mismatch')
    seen = set()
    for row in obj['events']:
        if not isinstance(row, dict) or set(row) != EVENT:
            raise UnsafePreview('unexpected event fields')
        key = row['event_key']
        if not isinstance(key, str) or not SHA24.fullmatch(key) or key in seen:
            raise UnsafePreview('bad or duplicated event key')
        seen.add(key)
        if row['publication_lane'] != 'independent_official_recheck_required' or row['personal_eligibility'] != 'UNKNOWN':
            raise UnsafePreview('promotion not allowed')
        if row['reported_status'] not in ('DISCOVERED','CROSS_CHECKED','OFFICIAL_VERIFIED','CLAIMABLE','UNKNOWN','CONFLICTED','EXPIRED','FAILED','REDEEMED'):
            raise UnsafePreview('invalid reported status')
        if public_title(row['title']) is None or public_url(row['public_url']) is None or public_url(row['public_url']) != row['public_url']:
            raise UnsafePreview('invalid public metadata')
        if row['published_at'] is not None:
            _time(row['published_at'])
        if row['first_seen'] is not None:
            _time(row['first_seen'])
        if row['batch_key'] is not None and (not isinstance(row['batch_key'], str) or not re.fullmatch('[a-f0-9]{16}', row['batch_key'])):
            raise UnsafePreview('invalid batch key')
        if not isinstance(row['official_evidence'], list):
            raise UnsafePreview('invalid official evidence')
        for p in row['official_evidence']:
            if not isinstance(p, dict) or set(p) != PROOF or not isinstance(p['claims'], dict):
                raise UnsafePreview('unexpected official evidence fields')
            if public_url(p['url']) is None or public_url(p['url']) != p['url']:
                raise UnsafePreview('unsafe official evidence url')
            # Equality alone would allow True == 1; compare typed JSON too.
            if json.dumps(public_claims(p['claims']), sort_keys=True) != json.dumps(p['claims'], sort_keys=True):
                raise UnsafePreview('unsafe official evidence claims')
            _time(p['checked_at'])
    return obj


def review_delta(current: dict, previous: dict | None = None) -> dict:
    """Only candidate IDs are emitted; caller must independently recheck sources."""
    if previous is None:
        return {'status': 'BASELINE_ONLY', 'candidate_keys': [], 'notices': ['No newly-opened-offer claims permitted']}
    def revision(row):
        canonical = dict(row)
        canonical['official_evidence'] = sorted(
            [{key: value for key, value in proof.items() if key != 'checked_at'}
             for proof in row['official_evidence']],
            key=lambda proof: json.dumps(proof, sort_keys=True))
        return json.dumps(canonical, sort_keys=True, ensure_ascii=False)
    old = {row['event_key']: revision(row) for row in previous['events']}
    return {'status': 'MANUAL_SOURCE_RECHECK_REQUIRED',
            'candidate_keys': [row['event_key'] for row in current['events'] if row['event_key'] not in old or revision(row) != old[row['event_key']]],
            'notices': ['Candidate IDs are not proof of availability, account eligibility, or new publication']}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--sha256', required=True, help='Independent precommitted digest of preview file')
    parser.add_argument('--previous', type=Path)
    parser.add_argument('--previous-sha256')
    args = parser.parse_args(argv)
    if bool(args.previous) != bool(args.previous_sha256):
        parser.error('previous file and independent digest must be specified together')
    current = validate(args.input.read_bytes(), args.sha256)
    previous = validate(args.previous.read_bytes(), args.previous_sha256) if args.previous else None
    print(json.dumps(review_delta(current, previous), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
