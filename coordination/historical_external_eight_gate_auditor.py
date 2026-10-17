#!/usr/bin/env python3
"""Read-only integrity inventory for the eight non-code historical gates.

This module NEVER authenticates a human, awards personal eligibility, or marks
business acceptance.  File hashes prove bytes only.  For review-only tasks it
can inventory a review memo, but that is not a native-runtime acceptance.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
import os
import stat
from pathlib import Path, PurePosixPath
import re
from typing import Any

# From the immutable 50-family manifest, Git blob
# 96c71aad1e26e5bf7b0aa12ac1e4b62ddcb98744.
GATES = {
    'WR-H12': ('WoolRadar', 'USER_APPROVAL'),
    'WR-H13': ('WoolRadar', 'FRESH_GOLD'),
    'WR-H14': ('WoolRadar', 'SCHEDULED_BLOCKED'),
    'WR-H17': ('WoolRadar', 'MAINTAINER_APPROVAL'),
    'SAM-H08': ('YinQieJi-SAM', 'FRESH_GOLD'),
    'SAM-H11': ('YinQieJi-SAM', 'HUMAN_SOURCE_REVIEW'),
    'SAM-H24': ('YinQieJi-SAM', 'HUMAN_SOURCE_REVIEW'),
    'COORD-H07': ('WoolRadar-Coord', 'REVIEW_ONLY'),
}
SHA256 = re.compile(r'[0-9a-f]{64}\Z')
MAX_BYTES = 2 * 1024 * 1024


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('AMBIGUOUS_DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def _finite_float(raw: str) -> float:
    value = float(raw)
    if not math.isfinite(value):
        raise ValueError('NONFINITE_JSON_NUMBER')
    return value


def strict_json(payload: bytes) -> Any:
    if len(payload) > MAX_BYTES:
        raise ValueError('OVERSIZE_DOCUMENT')
    try:
        return json.loads(payload.decode('utf-8', errors='strict'),
                          object_pairs_hook=_unique_pairs,
                          parse_float=_finite_float,
                          parse_constant=lambda _: (_ for _ in ()).throw(
                              ValueError('NONFINITE_JSON_NUMBER')))
    except UnicodeError as exc:
        raise ValueError('INVALID_UTF8_DOCUMENT') from exc
    except RecursionError as exc:
        raise ValueError('EXCESSIVE_JSON_NESTING') from exc


def validate_manifest(manifest: Any) -> None:
    if not isinstance(manifest, dict) or not isinstance(manifest.get('jobs'), list):
        raise ValueError('INVALID_FROZEN_MANIFEST')
    actual = {}
    for job in manifest['jobs']:
        if not isinstance(job, dict):
            raise ValueError('INVALID_FROZEN_JOB')
        family_id = job.get('family_id')
        if family_id in GATES:
            if family_id in actual:
                raise ValueError('DUPLICATED_GATED_FAMILY')
            actual[family_id] = (job.get('project'), job.get('external_constraint'))
            if job.get('disposition') != 'EXTERNAL_OR_POLICY_GATED':
                raise ValueError('WRONG_GATED_DISPOSITION')
    if actual != GATES:
        raise ValueError('FROZEN_EIGHT_GATE_MAPPING_DRIFT')


def _read_safe_evidence(root: Path, rel: str) -> bytes:
    """Open through no-follow descriptors to prevent path-swap symlink reads."""
    if not isinstance(rel, str) or len(rel) > 256 or '\\' in rel or '\x00' in rel:
        raise ValueError('INVALID_EVIDENCE_PATH')
    posix = PurePosixPath(rel)
    if (not rel or posix.is_absolute() or
            any(part in ('', '.', '..') for part in rel.split('/')) or
            rel.startswith('~')):
        raise ValueError('EVIDENCE_PATH_TRAVERSAL')
    if not hasattr(os, 'O_NOFOLLOW') or not hasattr(os, 'O_DIRECTORY'):
        raise ValueError('SECURE_FILE_OPEN_UNSUPPORTED')
    descriptors = []
    try:
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        descriptors.append(fd)
        for component in posix.parts[:-1]:
            fd = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                         dir_fd=fd)
            descriptors.append(fd)
        fd = os.open(posix.parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=fd)
        descriptors.append(fd)
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError('EVIDENCE_NOT_REGULAR_OR_OUTSIDE')
        if info.st_size > MAX_BYTES:
            raise ValueError('OVERSIZE_EVIDENCE')
        with os.fdopen(os.dup(fd), 'rb') as stream:
            content = stream.read(MAX_BYTES + 1)
        if len(content) > MAX_BYTES:
            raise ValueError('OVERSIZE_EVIDENCE')
        return content
    except OSError as exc:
        raise ValueError('EVIDENCE_NOT_REGULAR_OR_SYMLINK') from exc
    finally:
        for fd in reversed(descriptors):
            os.close(fd)


def audit(manifest: Any, receipt: Any, evidence_root: Path) -> dict[str, Any]:
    validate_manifest(manifest)
    if (not isinstance(receipt, dict) or type(receipt.get('schema_version')) is not int
            or receipt['schema_version'] != 1
            or not isinstance(receipt.get('gates'), list)):
        raise ValueError('INVALID_GATE_RECEIPT')
    seen = set()
    items = []
    for row in receipt['gates']:
        if not isinstance(row, dict):
            raise ValueError('INVALID_GATE_ROW')
        family = row.get('family_id')
        if not isinstance(family, str) or family not in GATES:
            raise ValueError('UNKNOWN_GATE_FAMILY')
        if family in seen:
            raise ValueError('DUPLICATE_GATE_FAMILY')
        seen.add(family)
        if (row.get('project'), row.get('gate')) != GATES[family]:
            raise ValueError('MISMATCHED_GATE_REQUIREMENT')
        state = row.get('state')
        if state not in ('BLOCKED', 'LOCAL_EVIDENCE_ONLY', 'REVIEW_DOCUMENTED'):
            # Explicitly forbid PASS, APPROVED, VERIFIED, DONE and synonyms.
            raise ValueError('UNSUPPORTED_AUTOMATIC_APPROVAL')
        evidence = row.get('evidence')
        if evidence is None:
            if state != 'BLOCKED':
                raise ValueError('UNSUPPORTED_EVIDENCE_CLAIM')
            observed_hash = None
        else:
            if (not isinstance(evidence, dict)
                    or not isinstance(evidence.get('relative_path'), str)
                    or not isinstance(evidence.get('sha256'), str)
                    or not SHA256.fullmatch(evidence['sha256'])):
                raise ValueError('INVALID_EVIDENCE_DESCRIPTOR')
            observed_hash = sha256(_read_safe_evidence(
                evidence_root, evidence['relative_path'])).hexdigest()
            if observed_hash != evidence['sha256']:
                raise ValueError('EVIDENCE_CONTENT_SHA_MISMATCH')
            if state == 'BLOCKED':
                raise ValueError('BLOCKED_GATE_CANNOT_ATTACH_CLAIMED_EVIDENCE')
        if state == 'REVIEW_DOCUMENTED' and family != 'COORD-H07':
            raise ValueError('REVIEW_DOCUMENTED_ONLY_FOR_REVIEW_GATE')
        items.append({'family_id': family, 'project': GATES[family][0],
                      'gate': GATES[family][1], 'state': state,
                      'evidence_sha256_verified': observed_hash is not None,
                      'needs_independent_human_or_runtime_acceptance':
                          family != 'COORD-H07',
                      'business_gate_accepted': False})
    if seen != set(GATES):
        raise ValueError('INCOMPLETE_EIGHT_GATE_COVERAGE')
    return {
        'schema_version': 1,
        'families_evaluated': len(items),
        'review_documents_checked': sum(i['state'] == 'REVIEW_DOCUMENTED' for i in items),
        'local_evidence_checked': sum(i['evidence_sha256_verified'] for i in items),
        'external_business_families_auto_accepted': 0,
        'production_or_user_approval_authenticated': False,
        'all_historical_business_gates_accepted': False,
        'all_39_frozen_commands_accepted': False,
        'historical_recovery_closed': False,
        'results': sorted(items, key=lambda i: i['family_id']),
        'warning': 'Evidence hash is byte integrity, not approval, live source authenticity or eligibility.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--evidence-root', type=Path, required=True)
    args = parser.parse_args()
    try:
        # Use the existing, immutable Git-blob source identity contract.
        try:
            from HISTORICAL_CODEX_42_RECEIPT_GUARD_20261017 import load_verified_manifest
        except ImportError:
            from coordination.HISTORICAL_CODEX_42_RECEIPT_GUARD_20261017 import load_verified_manifest
        manifest = load_verified_manifest(args.manifest)
        receipt = strict_json(args.receipt.read_bytes())
        verdict = audit(manifest, receipt, args.evidence_root)
    except (OSError, ValueError, TypeError) as exc:
        # No raw receipt/body content or local path in stderr.
        print(json.dumps({'status': 'INVALID_OR_INCOMPLETE', 'reason': type(exc).__name__,
                          'historical_recovery_closed': False}))
        return 2
    print(json.dumps(verdict, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
