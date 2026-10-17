"""Scoped synthetic benefit review, not independent quality acceptance."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root', type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo_root.resolve()
    out = Path(__file__).resolve().parent
    (out / 'synthetic-temp').mkdir(exist_ok=True)
    tempfile.tempdir = str(out / 'synthetic-temp')
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    sys.path.insert(0, str(repo))
    from core.collector import contains_keyword
    from core.developer_benefits import is_explicit_developer_benefit
    paths = ['core/developer_benefits.py', 'core/collector.py',
             'tests/test_explicit_developer_benefits.py']
    hashes = {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in paths}
    suite = unittest.TestSuite()
    for name in ['test_explicit_developer_benefits.py', 'test_offer_keyword_context.py']:
        suite.addTests(unittest.TestLoader().discover(str(repo / 'tests'), pattern=name))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream).run(suite)
    formal = {'run': result.testsRun, 'passed': result.wasSuccessful(),
              'failure_ids': [test.id() for test, _ in result.failures],
              'error_ids': [test.id() for test, _ in result.errors]}
    positive = 'The software certification exam fee is now waived for verified students.'
    event = 'Developer hackathon: apply to host a Fest. Organizers will receive participant swag.'
    checks = []
    assert contains_keyword(positive, ['developer perks'])
    assert contains_keyword(event, ['developer perks'])
    assert not contains_keyword(positive, [])
    assert not contains_keyword(event, ['free VPS'])
    checks.append({'name': 'waiver-event-positive-and-keyword-opt-in-controls', 'passed': True})
    for value in ['', None, {}, 'x' * 16001]:
        assert not is_explicit_developer_benefit(value)
    assert not contains_keyword('x' * 16001 + positive, ['developer perks'])
    checks.append({'name': 'invalid-and-overlong-helper-input-does-not-create-new-benefit-lead', 'passed': True})
    controls = [
        ('explicit-paid-exam', 'Students pay an exam fee for the software certification.'),
        ('direct-past', 'The developer certification exam fee was waived last year.'),
        ('explicit-negation', 'The developer certification exam fee is not waived.'),
        ('unrelated-event', 'Company picnic: hosts will receive T-shirts. Apply to host a Fest.')]
    for label, text in controls:
        assert not contains_keyword(text, ['developer perks'])
        checks.append({'name': label + '-control-rejected', 'passed': True})
    cases = [
        ('closed-suffix', 'The software certification exam fee is now waived. This offer is over.'),
        ('question', 'Does anyone know whether the developer certification exam fee is now waived?'),
        ('paid-condition', 'The software certification exam fee is now waived only with a paid subscription.'),
        ('quoted-past', "Last year's announcement said: 'The developer certification exam fee is now waived for students'."),
        ('unrelated-certification-scope', 'Software industry news. The driving exam fee is now waived for motorists.'),
        ('unrelated-event-scope', 'Developer biography. Company picnic hosts will receive T-shirts. Apply to host a Fest.')]
    observed = []
    for label, text in cases:
        observed.append({'case': label, 'synthetic_text': text,
                         'helper': is_explicit_developer_benefit(text),
                         'collector': contains_keyword(text, ['developer perks']),
                         'expected': False})
    assert all(not case['helper'] and not case['collector'] for case in observed), 'One of the six original counterexamples remains accepted'
    findings = []
    guard_cases = [case for case in observed if case['collector'] and case['case'] in
                   {'closed-suffix', 'question', 'paid-condition', 'quoted-past'}]
    if guard_cases:
        findings.append({'priority': 'P2', 'title': 'New benefit hook accepts closed/question/paid/history context',
                         'cases': guard_cases,
                         'detail': 'Whole-text helper executes after existing clause guards and can revive a rejected statement. Direct past-tense and basic not-waived controls pass, but equivalent suffix/question or historical quotation contexts do not.',
                         'minimal_fix': 'Add scoped tests for these exact contexts and share or extend the existing intent/closure guard without suppressing genuine waiver and host-support announcements.'})
    scope_cases = [case for case in observed if case['collector'] and case['case'].startswith('unrelated-')]
    if scope_cases:
        findings.append({'priority': 'P2', 'title': 'Unrelated developer/software mention supplies scope for non-developer benefit',
                         'cases': scope_cases,
                         'detail': 'Scope is required only somewhere in the text, so unrelated driving certification or company-picnic swag can acquire developer scope from another sentence.',
                         'minimal_fix': 'Bind the technical/developer scope to the claimed certification or event with bounded contextual rules and retain the intended long-form developer-event positives.'})
    for label, text, expected in [
        ('nontechnical-student-certification', 'Driving certification examination fee is now waived for students.', False),
        ('software-hackathon', 'Software hackathon: apply to host a Fest. Organizers will receive participant swag.', True)]:
        actual = contains_keyword(text, ['developer perks'])
        checks.append({'name': label, 'expected': expected, 'actual': actual, 'passed': actual == expected})
        if actual != expected:
            findings.append({'priority': 'P2', 'title': label + ' scope boundary mismatch',
                             'synthetic_text': text, 'expected': expected, 'actual': actual,
                             'detail': ('Certification plus students does not establish a technical exam domain.' if not expected else
                                        'New technical-event restriction omits the explicitly software-scoped hackathon previously accepted.'),
                             'minimal_fix': ('Require a technical certification qualifier, not student status alone.' if not expected else
                                             'Retain software hackathon as a technical event positive control.')})
    assert hashes == {name: hashlib.sha256((repo / name).read_bytes()).hexdigest() for name in paths}
    record = {'reviewer': 'independent budget_review agent',
              'command': 'python -B _outbox/pipeline-integration-20261016/oct17_benefits_rereview_checks.py --repo-root <delivery-worktree>',
              'exit_code': 0, 'source_sha256': hashes, 'formal_tests': formal,
              'checks': checks, 'findings': findings,
              'qualification_boundary': 'In the three reviewed files this is a boolean discovery branch. No evidence/status/account-eligibility promotion is introduced by the branch; whole-system qualification behavior was not re-audited.',
              'limits': ['All new counterexamples are synthetic development checks, not a new holdout or 95% acceptance.',
                         'No retired sample, original data, DB, report, network or paid API used.',
                         'No worktree/product edits or full-suite rerun. No raw data upload.',
                         'Dedup was not reviewed: the previously reported same-campaign false split remains unresolved; no dedup pass claimed.']}
    path = out / 'oct17-benefits-rereview.json'
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert json.loads(path.read_text(encoding='utf-8')) == record
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
