"""Current-source-only producer/selector followup, synthetic files exclusively."""
import argparse
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
    (out / 'synthetic-temp').mkdir(exist_ok=True)
    tempfile.tempdir = str(out / 'synthetic-temp')
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    sampler = repo / 'independent-quality/public-corpus-blind-dedup-20261016'
    bridge = repo / 'independent-quality/delivery-bridge-20261016'
    sys.path[:0] = [str(repo), str(sampler), str(bridge)]
    from core.public_corpus import record_public_sample
    from core.developer_grants import is_developer_grant_lead
    from core.collector import contains_keyword
    from freeze_public_sample_dedup import freeze_public_sources
    from redact_daily import build_preview
    from consume_preview import review_delta
    paths = ['core/public_corpus.py', 'core/developer_grants.py', 'core/collector.py',
             'independent-quality/public-corpus-blind-dedup-20261016/freeze_public_sample_dedup.py',
             'independent-quality/delivery-bridge-20261016/consume_preview.py']
    hashes = {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in paths}
    suite = unittest.TestSuite()
    scopes = []
    for folder, pattern in [(repo / 'tests', 'test_public_corpus_identity.py'),
                            (repo / 'tests', 'test_developer_grant_discovery.py'),
                            (sampler, 'test_*.py'), (bridge, 'test_snapshot_chronology.py')]:
        tests = unittest.TestLoader().discover(str(folder), pattern=pattern)
        scopes.append({'directory': str(folder.relative_to(repo)), 'pattern': pattern,
                       'methods': tests.countTestCases()})
        suite.addTests(tests)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(suite)
    tests = {'run': result.testsRun, 'passed': result.wasSuccessful(),
             'failure_ids': [x.id() for x, _ in result.failures],
             'error_ids': [x.id() for x, _ in result.errors]}
    checks, findings = [], []

    def produce(urls):
        with tempfile.TemporaryDirectory() as name:
            rows = [{'url': url, 'title': 'Synthetic public program ' + chr(65 + i), 'summary': ''}
                    for i, url in enumerate(urls)]
            path = record_public_sample(Path(name), 'synthetic',
                                        {'id': 'synthetic', 'kind': 'rss', 'auth': 'public_feed'},
                                        rows, [False] * len(rows))
            return json.loads(path.read_text(encoding='utf-8'))

    def pick(source):
        return freeze_public_sources([(source, 'a' * 64)], 8)

    positive = produce(['https://feed.example/view?batch=alpha&ref=public-a&utm_source=feed',
                        'https://feed.example/view?batch=beta&ref=public-b',
                        'https://feed.example/#/programs/alpha?offer=one',
                        'https://feed.example/#/programs/beta?offer=two'])
    assert all(row['url_identity_preserved'] is True for row in positive['rows'])
    assert len(pick(positive)['rows']) == len(positive['rows'])
    assert all('utm_source' not in row['url'] for row in positive['rows'])
    checks.append({'name': 'real-producer-retains-functional-ref-batch-and-spa-identities', 'passed': True})
    for label, url in [('unknown-selector', 'https://feed.example/view?unknown=alpha'),
                       ('contact-value', 'https://feed.example/view?ref=synthetic%40example.com'),
                       ('credential-value', 'https://feed.example/view?ref=SYNTHETIC_token'),
                       ('conflicting-selector', 'https://feed.example/view?batch=alpha&batch=beta'),
                       ('private-spa-query', 'https://feed.example/#/programs/alpha?session=synthetic')]:
        source = produce([url])
        assert source['rows'][0]['url_identity_preserved'] is False
        assert not pick(source)['rows']
        checks.append({'name': label + '-loss-marked-and-excluded', 'passed': True})
    legacy = {'schema_version': 1, 'source_id': 'legacy', 'public_only': True,
              'rows': [{'url': 'https://feed.example/offer', 'title': 'Synthetic legacy',
                        'summary': '', 'url_sanitized': True}]}
    assert not pick(legacy)['rows']
    checks.append({'name': 'legacy-sanitized-without-identity-proof-excluded', 'passed': True})

    prefix = 'https://feed.example/' + 'a' * 2048
    long_urls = produce([prefix + '/alpha', prefix + '/beta'])
    selected = pick(long_urls)
    if any(row['url_identity_preserved'] is True for row in long_urls['rows']):
        findings.append({'priority': 'P1', 'title': 'Producer URL truncation is incorrectly marked identity-preserving',
                         'input_rows': len(long_urls['rows']), 'selected_rows': len(selected['rows']),
                         'stored_urls_collapsed': long_urls['rows'][0]['url'] == long_urls['rows'][1]['url'],
                         'identity_flags': [row['url_identity_preserved'] for row in long_urls['rows']],
                         'content_truncated_flags': [row['content_truncated'] for row in long_urls['rows']],
                         'minimal_fix': 'Set url_identity_preserved=False whenever the URL itself is truncated. '
                                        'Do not confuse title/summary truncation with URL identity; selector must exclude these lost identities.'})
    else:
        assert not selected['rows']
        checks.append({'name': 'url-truncation-marked-lost-and-excluded', 'passed': True})

    award = 'Selected developers receive $' + str(len('synthetic')) + '.'
    good = 'This developer grant is accepting applications. No application fee. ' + award
    assert is_developer_grant_lead(good) and contains_keyword(good, ['developer perks'])
    assert not contains_keyword(good, [])
    for label, text in [('not-accepting', 'Developer grant is not accepting applications. ' + award),
                        ('not-open', 'Developer grant applications are not open. Apply for future updates. ' + award),
                        ('applicant-question', 'Can I apply for this developer grant? ' + award)]:
        assert not is_developer_grant_lead(text)
        assert not contains_keyword(text, ['developer perks'])
    checks.append({'name': 'grant-no-fee-positive-toggle-and-three-denial-controls', 'passed': True})
    denied = 'This developer grant does not accept applications. ' + award
    if is_developer_grant_lead(denied) or contains_keyword(denied, ['developer perks']):
        findings.append({'priority': 'P2', 'title': 'Previously reported does-not-accept negation remains accepted',
                         'helper_accepts': is_developer_grant_lead(denied),
                         'collector_accepts': contains_keyword(denied, ['developer perks']),
                         'minimal_fix': 'Cover do/does/did not accept applications alongside not accepting; '
                                        'retain genuinely open and explicit fee-waiver controls.'})
    else:
        checks.append({'name': 'does-not-accept-negation-rejected', 'passed': True})

    old = build_preview({'date': '2026-10-16', 'events': []}, 'a' * 64,
                        now=datetime(2026, 10, 16, 8, tzinfo=timezone.utc))
    current = build_preview({'date': '2026-10-16', 'events': [{
        'title': 'Synthetic developer benefit', 'primary_url': 'https://feed.example/offer',
        'status': 'UNKNOWN', 'evidence': []}]}, 'b' * 64,
        now=datetime(2026, 10, 16, 8, 0, 0, 1, tzinfo=timezone.utc))
    assert review_delta(current, old)['status'] == 'SNAPSHOT_ORDER_AMBIGUOUS'
    checks.append({'name': 'subsecond-distinct-content-now-ambiguous', 'passed': True})
    assert hashes == {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in paths}
    report = {'reviewer': 'independent budget_review agent',
              'command': 'python -B _outbox/pipeline-integration-20261016/followup_checks.py --repo-root <delivery-worktree>',
              'exit_code': 0, 'source_sha256': hashes, 'formal_scope': scopes,
              'formal_tests': tests, 'checks': checks, 'findings': findings,
              'limits': ['Only current safe code and synthetic producer files; no old Git/cache/fixtures, '
                         'real private data, new public samples or old frozen sample used.',
                         'No worktree/source writes, production or network. No amount text echoed.',
                         'Identity metadata is a producer contract, not a signature, independent approval '
                         'or proof that an arbitrary supplied source is genuine.',
                         'No full regression or accuracy/holdout/connection claim.']}
    path = out / 'followup-review.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert json.loads(path.read_text(encoding='utf-8')) == report
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
