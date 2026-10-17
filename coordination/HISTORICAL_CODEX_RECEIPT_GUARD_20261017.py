"""Validate source-locked local Codex batch receipts without promoting releases."""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

HEADS = {
    'wool': '80c5ea18769c1312e5be5fd99a39e4f3d498c64f',
    'sam': '82bf36efa90cced8dafb56502812eb49f40515f3',
    'coord': '27796df5f9847c1bb5d48d2a445e418dfb3d8e96',
}
BATCHES = {
    'wool': {'W-ALL', 'W-SAMPLER', 'W-SNAPSHOT'},
    'sam': {'S-BUILD', 'S-ALL', 'S-ROOTED', 'S-TEACHER'},
    'coord': {'C-ALL'},
}
HEX = re.compile(r'^[0-9a-f]{64}$')


def review(data: dict) -> dict:
    """Only certifies receipt structural consistency, never business readiness."""
    errors = []
    project = data.get('project')
    expected = HEADS.get(project)
    if expected is None:
        errors.append('UNKNOWN_PROJECT')
    if expected is not None and data.get('repo_head') != expected:
        errors.append('HEAD_MISMATCH')
    if data.get('schema') != 1 or data.get('source') != 'local-disposable-codex':
        errors.append('UNTRUSTED_RECEIPT_PROVENANCE')
    results = data.get('results')
    if not isinstance(results, list):
        results = []
        errors.append('INVALID_RESULTS')
    seen = set()
    for result in results:
        if not isinstance(result, dict):
            errors.append('MALFORMED_BATCH')
            continue
        key = result.get('batch')
        if key in seen:
            errors.append('DUPLICATE_BATCH')
        seen.add(key)
        if project in BATCHES and key not in BATCHES[project]:
            errors.append('UNEXPECTED_BATCH')
        rc = result.get('exit_code')
        if isinstance(rc, bool) or not isinstance(rc, int) or rc != 0:
            errors.append('BATCH_NONZERO_OR_UNKNOWN')
        if not isinstance(result.get('log_sha256'), str) or not HEX.fullmatch(result['log_sha256']):
            errors.append('INVALID_LOG_DIGEST')
        counts = result.get('counts')
        if not isinstance(counts, dict):
            errors.append('NO_COUNTS')
        elif key != 'S-BUILD':
            total = counts.get('tests_reported')
            passed = counts.get('passed')
            failed = counts.get('failed')
            skipped = counts.get('skipped')
            if (not isinstance(total, int) or isinstance(total, bool) or total <= 0):
                errors.append('NO_TEST_COUNT')
            if (not isinstance(passed, int) or isinstance(passed, bool)
                    or failed != 0 or (isinstance(total, int) and passed > total)):
                errors.append('INVALID_TEST_OUTCOME')
            if skipped != 0:
                errors.append('SKIPPED_NOT_FULLY_ACCEPTED')
    if project in BATCHES and set(BATCHES[project]) != seen:
        errors.append('MISSING_REQUIRED_BATCH')
    return {
        'project': project, 'head': data.get('repo_head'),
        'local_suite_receipt_accepted': len(errors) == 0,
        'errors': sorted(set(errors)),
        'business_gold_accepted': False,
        'historical_recovery_closed': False,
        'safe_next_action': 'Review individual test logs and private-data redaction; do not auto-merge.'
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.receipt.read_text(encoding='utf-8'))
    report = review(data)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report['local_suite_receipt_accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
