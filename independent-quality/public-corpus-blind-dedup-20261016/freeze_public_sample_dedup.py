"""Offline local-only public-corpus selection for future *unseen* review batches.
No network, no label edits, no producer/source changes, no automatic upload.
Do not reuse a development or already unblinded corpus as a new holdout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
from pathlib import Path
from urllib.parse import unquote_plus, urlsplit, urlunsplit

MAX_INPUT = 8_000_000
MAX_ROWS = 500
MAX_SOURCES = 20
MAX_OUTPUT = 4_000_000
SOURCE_ID = re.compile(r"[A-Za-z0-9_-]{1,64}\Z")


def _sensitive_public_route(route: str) -> bool:
    """Reject legacy sampled routes which could still contain credentials."""
    decoded = route
    for _ in range(4):
        latest = unquote_plus(decoded)
        if (re.search(r'(?i)(?:@|\d{13,}|token|secret|bearer|password|session)', latest)
                or re.search(r'(?i)(?:^|/)(?:reset|activate|magic-link|credential|api[_-]?key)(?:/|$)', latest)
                or re.search(r'(?i)(?:^|/)[a-f0-9]{24,}(?:/|$)', latest)):
            return True
        if latest == decoded:
            return False
        decoded = latest
    return '%' in decoded


def canonical_public_url(raw: object) -> str | None:
    if not isinstance(raw, str) or len(raw) > 2048 or not raw:
        return None
    try:
        raw.encode('utf-8')  # reject unpaired Unicode surrogates, including in paths
        p = urlsplit(raw)
        if p.scheme not in ('http', 'https') or not p.hostname or p.username or p.password:
            return None
        host = p.hostname.lower().rstrip('.')
        if not re.fullmatch(r'[a-z0-9.-]+', host) or '..' in host or host.startswith('-'):
            return None
        # Never collapse business-significant query parameters or app routes.
        # Remove only known marketing trackers; a query such as ?batch=2
        # can represent a genuinely different grant/VPS campaign.
        p.query.encode('utf-8')
        p.fragment.encode('utf-8')
        if (_sensitive_public_route(p.path)
                or _sensitive_public_route(p.fragment.partition('?')[0])):
            return None
        retained = []
        for part in p.query.split('&'):
            # Repeatedly decode only the query key: a nested-encoded secret
            # key or delimiter must never reach an output review URL.
            key = part.split('=', 1)[0]
            for _ in range(5):
                decoded = unquote_plus(key)
                if decoded == key:
                    break
                key = decoded
            if '%' in key or any(delimiter in key for delimiter in '=&;#?'):
                return None
            key = key.lower()
            if key in {'access_token', 'refresh_token', 'id_token', 'api_key',
                       'apikey', 'client_secret', 'password', 'session',
                       'session_id', 'authorization', 'oauth_token', 'jwt',
                       'token', 'secret', 'auth', 'code', 'signature', 'sig',
                       'sessionid', 'api-key', 'email', 'phone'}:
                return None
            if key in {'utm_source', 'utm_medium', 'utm_term', 'utm_content',
                       'fbclid', 'gclid', 'msclkid', 'mc_cid', 'mc_eid'}:
                continue
            if part:
                retained.append(part)
        fragment = p.fragment if p.fragment.startswith(('/', '!/')) else ''
        if re.search(r'(?i)(?:access_token|refresh_token|id_token|password|session|api_key|token|secret|auth|code|signature|sig|email|phone)=',
                     fragment):
            return None
        port = p.port
        netloc = host if port is None or (p.scheme == 'http' and port == 80) or (p.scheme == 'https' and port == 443) else f'{host}:{port}'
        return urlunsplit((p.scheme, netloc, p.path or '/', '&'.join(retained), fragment))
    except (ValueError, TypeError, UnicodeError):
        return None


def freeze_public_sources(sources: list[tuple[dict, str]], limit: int = 8,
                          excluded_urls: set[str] | None = None,
                          prior_sha256: list[str] | None = None) -> dict:
    """Uses public, unlabelled source samples only; hash order never reads collector accepted labels."""
    if type(limit) is not int or not (1 <= limit <= 50) or not (1 <= len(sources) <= MAX_SOURCES):
        raise ValueError('invalid source count or cap')
    prior = set()
    for old_url in excluded_urls or ():
        url = canonical_public_url(old_url)
        if url is None:
            raise ValueError('invalid previous review URL')
        prior.add(url)
    prior_hashes = prior_sha256 or []
    if (len(prior_hashes) > MAX_SOURCES or
            any(not isinstance(x, str) or not re.fullmatch('[a-f0-9]{64}', x)
                for x in prior_hashes)):
        raise ValueError('invalid previous review fingerprints')
    seen_ids = set()
    source_data = []
    for source, raw_sha in sources:
        if not isinstance(source, dict) or source.get('schema_version') != 1 or source.get('public_only') is not True:
            raise ValueError('not an approved public-corpus source')
        ident = source.get('source_id')
        rows = source.get('rows')
        if not isinstance(ident, str) or not SOURCE_ID.fullmatch(ident) or ident in seen_ids:
            raise ValueError('duplicate or invalid source identity')
        if not isinstance(rows, list) or len(rows) > MAX_ROWS or any(not isinstance(r, dict) for r in rows):
            raise ValueError('invalid source rows')
        if not isinstance(raw_sha, str) or not re.fullmatch('[a-f0-9]{64}', raw_sha):
            raise ValueError('invalid source fingerprint')
        seen_ids.add(ident)
        source_data.append((ident, rows, raw_sha))
    # Resolve duplicates in the complete unbounded candidate pool BEFORE applying each source cap.
    globally_seen = set()
    picked = []
    audits = []
    for ident, rows, sha in sorted(source_data):
        in_source = set()
        candidates = []
        duplicate_within = duplicate_between = invalid = upstream_identity_loss = excluded_prior = 0
        for row in rows:
            # Old schema-v1 producers did not attest to URL identity. Even
            # url_sanitized=False cannot prove that query or SPA route identity
            # was preserved upstream. A fresh blind denominator requires an
            # explicit positive claim from the current public-corpus producer.
            if row.get('url_identity_preserved') is not True:
                upstream_identity_loss += 1
                continue
            url = canonical_public_url(row.get('url'))
            if (url is None or not isinstance(row.get('title'), str)
                    or not isinstance(row.get('summary'), str)):
                invalid += 1
                continue
            if url in in_source:
                duplicate_within += 1
                continue
            in_source.add(url)
            if url in globally_seen:
                duplicate_between += 1
                continue
            if url in prior:
                excluded_prior += 1
                continue
            candidates.append((url, row))
        # Cross-source identities are claimed for ALL URLs, not just sampled rows;
        # otherwise duplicate URLs can reappear in a later source's batch.
        globally_seen.update(in_source)
        candidates.sort(key=lambda item: (hashlib.sha256(item[0].encode()).hexdigest(), item[0]))
        for url, row in candidates[:limit]:
            title = row['title']
            summary = row['summary']
            picked.append({'sample_id': f'S{len(picked)+1:04d}', 'source_id': ident,
                           'url': url, 'title': title[:512], 'summary': summary[:20000]})
        audits.append({'source_id': ident, 'raw_sha256': sha, 'input_rows': len(rows),
                       'candidate_unique_urls': len(candidates), 'duplicate_within_source': duplicate_within,
                       'duplicate_across_source': duplicate_between, 'invalid_rows': invalid,
                       'excluded_prior_url': excluded_prior,
                       'upstream_url_identity_lost': upstream_identity_loss,
                       'selected_rows': len([r for r in picked if r['source_id'] == ident])})
    return {'schema_version': 1, 'purpose': 'LOCAL_ONLY_REVIEW_CANDIDATES_HOLDOUT_UNVERIFIED',
            'no_truth_labels': True, 'not_independent_if_used_for_tuning': True,
            'prior_url_exclusions': len(prior), 'prior_sha256': sorted(prior_hashes),
            'exact_url_dedup_only': True,
            'upstream_identity_fully_preserved': all(a['upstream_url_identity_lost'] == 0 for a in audits),
            'sources': audits, 'rows': picked,
            'limits': 'Public title/snippet may contain private text; manually review before sharing. Different URLs may be the same campaign. No availability or eligibility claims.'}


def parse_strict_json(raw: bytes) -> object:
    def strict_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('ambiguous duplicate public corpus field')
            result[key] = value
        return result
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError('nonfinite number')
        return number
    def reject_constant(_):
        raise ValueError('non-JSON number')
    try:
        decoded = raw.decode('utf-8', errors='strict')
        return json.loads(decoded, object_pairs_hook=strict_object,
                          parse_float=finite_float, parse_constant=reject_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ValueError('invalid public-corpus JSON') from exc


def parse_source_json(raw: bytes) -> dict:
    source = parse_strict_json(raw)
    if not isinstance(source, dict):
        raise ValueError('public-corpus root must be an object')
    if 'stored_count' in source and (type(source['stored_count']) is not int or
                                      source['stored_count'] != len(source.get('rows', []))):
        raise ValueError('inconsistent public corpus row count')
    return source


def parse_prior_review_urls(raw: bytes) -> set[str]:
    """Read only URL identities from past review samples, never labels/verdicts."""
    document = parse_strict_json(raw)
    rows = document.get('rows') if isinstance(document, dict) else document
    if not isinstance(rows, list) or len(rows) > MAX_ROWS * MAX_SOURCES:
        raise ValueError('invalid previous review rows')
    result = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('invalid previous review row')
        url = canonical_public_url(row.get('url'))
        if url is None:
            raise ValueError('invalid previous review URL')
        result.add(url)
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', action='append', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--per-source', type=int, default=8)
    parser.add_argument('--exclude-prior', action='append', default=[], type=Path,
                        help='previous blind review JSON; URL identities only, never truth labels')
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        parser.error('output must be a new local path')
    sources = []
    for path in args.input:
        if not path.is_file() or path.stat().st_size > MAX_INPUT:
            parser.error('invalid input public-corpus file')
        raw = path.read_bytes()
        source = parse_source_json(raw)
        sources.append((source, hashlib.sha256(raw).hexdigest()))
    excluded, prior_hashes = set(), []
    if len(args.exclude_prior) > MAX_SOURCES:
        parser.error('too many previous reviews')
    for path in args.exclude_prior:
        if not path.is_file() or path.stat().st_size > MAX_INPUT:
            parser.error('invalid previous review file')
        raw = path.read_bytes()
        excluded.update(parse_prior_review_urls(raw))
        prior_hashes.append(hashlib.sha256(raw).hexdigest())
    result = freeze_public_sources(sources, args.per_source,
                                   excluded_urls=excluded, prior_sha256=prior_hashes)
    bytes_out = (json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n').encode('utf-8')
    if len(bytes_out) > MAX_OUTPUT:
        raise ValueError('local sample too large')
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os,'O_NOFOLLOW',0), 0o600)
    try:
        with os.fdopen(fd, 'wb') as file:
            file.write(bytes_out)
    except BaseException:
        args.output.unlink(missing_ok=True)
        raise
    print(f'Local review candidates={len(result["rows"])}; NOT PUBLISHED; no claimability verdict')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
