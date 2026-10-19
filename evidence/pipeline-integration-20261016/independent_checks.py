"""Current safe source only; synthetic cases, no historical fixtures/data/network."""
import argparse
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from datetime import datetime, timezone


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    out = Path(__file__).resolve().parent
    (out / 'synthetic-temp').mkdir(parents=True, exist_ok=True)
    tempfile.tempdir = str(out / 'synthetic-temp')
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    bridge = repo / 'independent-quality/delivery-bridge-20261016'
    grants = repo / 'independent-quality/developer-grant-20261016'
    sampler = repo / 'independent-quality/public-corpus-blind-dedup-20261016'
    sys.path[:0] = [str(repo), str(bridge), str(grants), str(sampler)]
    from consume_preview import validate, review_delta
    from redact_daily import build_preview
    from core.developer_grants import is_developer_grant_lead
    from core.collector import contains_keyword
    from freeze_public_sample_dedup import freeze_public_sources, parse_source_json
    files = [bridge / 'consume_preview.py', repo / 'core/developer_grants.py',
             repo / 'core/collector.py', sampler / 'freeze_public_sample_dedup.py']
    hashes = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    suite = unittest.TestSuite()
    test_patterns = [(bridge, 'test_consume_preview.py'), (bridge, 'test_snapshot_chronology.py'),
                     (grants, 'test_developer_grants.py'), (sampler, 'test_*.py')]
    counts = []
    for folder, pattern in test_patterns:
        tests = unittest.TestLoader().discover(str(folder), pattern=pattern)
        counts.append({'directory': str(folder.relative_to(repo)), 'pattern': pattern,
                       'methods': tests.countTestCases()})
        suite.addTests(tests)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(suite)
    # Never print or persist test failure bodies that might echo fixture values.
    test_summary = {'run': result.testsRun, 'passed': result.wasSuccessful(),
                    'failure_ids': [test.id() for test, _ in result.failures],
                    'error_ids': [test.id() for test, _ in result.errors]}
    checks, findings = [], []
    now = datetime(2026, 10, 16, 8, tzinfo=timezone.utc)
    row = {'title': 'Public developer cloud benefit', 'primary_url': 'https://vendor.example/offer',
           'status': 'UNKNOWN', 'batch_id': '', 'first_seen': '2026-10-16T00:00:00Z', 'evidence': []}
    base = build_preview({'date': '2026-10-16', 'events': [row]}, 'a' * 64, now=now)

    def checked(value):
        raw = json.dumps(value).encode()
        return validate(raw, hashlib.sha256(raw).hexdigest(), now=now)

    previous = checked(copy.deepcopy(base))
    changed = copy.deepcopy(base)
    changed['events'][0]['title'] = 'Updated public developer cloud benefit'
    assert review_delta(checked(changed), previous)['status'] == 'SNAPSHOT_ORDER_AMBIGUOUS'
    changed['generated_at'] = '2026-10-16T08:00:00.000001Z'
    # now must be later than the sub-second publication for validation.
    raw = json.dumps(changed).encode()
    changed = validate(raw, hashlib.sha256(raw).hexdigest(),
                       now=datetime(2026, 10, 16, 8, 0, 1, tzinfo=timezone.utc))
    fractional = review_delta(changed, previous)
    checks.append({'name': 'exact-equal-distinct-snapshot-rejected', 'passed': True})
    if fractional['status'] != 'SNAPSHOT_ORDER_AMBIGUOUS':
        findings.append({'priority': 'P2', 'title': 'Fractional timestamps bypass the stated same-second ambiguity policy',
                         'actual_status': fractional['status'],
                         'candidate_count': len(fractional['candidate_keys']),
                         'detail': 'Distinct content in one wall-clock second is ordered by microseconds although comments say sub-second publisher ordering is outside schema v1.',
                         'minimal_fix': 'Compare second-granularity publication time for ambiguity, or explicitly define and test a supported trustworthy sub-second ordering contract.'})
    earlier = copy.deepcopy(base)
    earlier['generated_at'] = '2026-10-16T07:59:59Z'
    assert review_delta(checked(earlier), previous)['status'] == 'OUT_OF_ORDER_IGNORED'
    removed = copy.deepcopy(base)
    removed['generated_at'] = '2026-10-16T08:00:01Z'
    removed['events'] = []
    removed['count'] = {'input_events': 0, 'exported_events': 0, 'skipped_or_duplicate': 0}
    withdrawal = review_delta(removed, previous)
    assert not withdrawal['candidate_keys'] and withdrawal['withdrawn_keys']
    assert withdrawal['status'] == 'MANUAL_SOURCE_RECHECK_REQUIRED'
    checks.append({'name': 'reversed-snapshot-ignored-and-withdrawal-is-review-only', 'passed': True})

    # Amount is newly constructed synthetic test material, never echoed to output.
    award = 'Selected developers receive $' + str(len('synthetic')) + '.'
    positive = 'The developer grant is accepting applications. ' + award
    assert is_developer_grant_lead(positive)
    assert contains_keyword(positive, ['developer perks'])
    assert not contains_keyword(positive, [])
    assert not contains_keyword(positive, ['free VPS'])
    assert not is_developer_grant_lead('Developer grant applications are closed. ' + award)
    checks.append({'name': 'developer-grant-positive-toggle-and-explicit-closed-controls', 'passed': True})
    accepted_negations = []
    for label, text in [('negated-acceptance', 'This developer grant does not accept applications. ' + award),
                        ('not-open', 'Developer grant applications are not open. Apply for future updates. ' + award),
                        ('applicant-question', 'Can I apply for this developer grant? ' + award)]:
        helper = is_developer_grant_lead(text)
        collector = contains_keyword(text, ['developer perks'])
        if helper or collector:
            accepted_negations.append({'case': label, 'helper': helper, 'collector_hook': collector})
    if accepted_negations:
        findings.append({'priority': 'P2', 'title': 'Developer grant hook revives explicit application denials/questions',
                         'synthetic_cases': accepted_negations,
                         'detail': 'Application regex matches a positive substring inside not-accepting or applicant-question text; the grant hook runs outside existing available_clauses filtering.',
                         'minimal_fix': 'Add narrowly tested negated acceptance/not-open and applicant-intent guards to the grant helper; keep genuine grant announcements and keyword opt-in controls.'})

    def source(ident, rows):
        return ({'schema_version': 1, 'public_only': True, 'source_id': ident, 'rows': rows}, 'b' * 64)
    sample_rows = [{'url': 'https://feed.example/item?utm_source=one', 'title': 'First benefit', 'summary': '', 'accepted': True},
                   {'url': 'https://feed.example/item?utm_source=two', 'title': 'Duplicate benefit', 'summary': '', 'accepted': False},
                   {'url': 'https://feed.example/other', 'title': 'Other benefit', 'summary': '', 'accepted': False}]
    first = freeze_public_sources([source('alpha', sample_rows)], 8)
    flipped = copy.deepcopy(sample_rows)
    for item in flipped:
        item['accepted'] = not item['accepted']
    second = freeze_public_sources([source('alpha', flipped)], 8)
    assert first['rows'] == second['rows'] and len(first['rows']) == 2
    assert all('accepted' not in item for item in first['rows'])
    checks.append({'name': 'tracking-dedup-and-selection-independent-of-accepted-labels', 'passed': True})
    functional = freeze_public_sources([source('alpha', [
        {'url': 'https://feed.example/view?program=alpha', 'title': 'Alpha benefit', 'summary': ''},
        {'url': 'https://feed.example/view?program=beta', 'title': 'Beta benefit', 'summary': ''}])], 8)
    if len(functional['rows']) != 2:
        findings.append({'priority': 'P2', 'title': 'All-query stripping collapses distinct functional resource identities',
                         'synthetic_case': 'Same /view path with different program selectors and different titles',
                         'input_count': 2, 'selected_count': len(functional['rows']),
                         'detail': 'This is more than removing tracking labels; a distinct public resource may disappear from the blind denominator. Source producer may already have discarded such query identity, which this selector cannot reconstruct.',
                         'minimal_fix': 'Document this canonical-identity limitation or preserve approved functional identity separately; do not describe it as exact original-URL deduplication.'})
    try:
        parse_source_json(b'{"schema_version":1,"schema_version":1}')
    except ValueError:
        checks.append({'name': 'duplicate-json-fields-rejected', 'passed': True})
    else:
        raise AssertionError('Duplicate source fields accepted')
    assert hashes == {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    report = {'reviewer': 'independent budget_review agent',
              'command': 'python -B _outbox/pipeline-integration-20261016/independent_checks.py --repo-root <delivery-worktree>',
              'exit_code': 0, 'source_sha256': hashes, 'formal_scope': counts,
              'formal_tests': test_summary, 'checks': checks, 'findings': findings,
              'limits': ['Only current safe source and synthetic fixtures. No old Git/cache, real private data or new public samples read.',
                         'No fixture amount text or historical sensitive literals printed or persisted in review output.',
                         'No worktree edits, production, network, full regression or accuracy claim.',
                         'Withdrawal/candidate keys remain manual-review signals, never live availability or closure proof.']}
    path = out / 'independent-review.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert json.loads(path.read_text(encoding='utf-8')) == report
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
