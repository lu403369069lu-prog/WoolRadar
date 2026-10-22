"""Real disposable-Git regressions; synthetic suites are not PR113 acceptance."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

MODULE = None
RESULTS = []

class SourceGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='r8-', dir=Path(__file__).parent / 'scratch')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'source'
        self.root.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.name', 'Isolated audit')
        self.git('config', 'user.email', 'audit@example.invalid')
        self.git('config', 'core.autocrlf', 'false')
        for directory in ('.github/relay', 'coordination', 'coordination/original-tests'):
            target = self.root / directory
            target.mkdir(parents=True, exist_ok=True)
            (target / 'test_sample.py').write_text('import unittest\nclass Sample(unittest.TestCase):\n    def test_positive(self): self.assertTrue(True)\n', encoding='utf-8')
        (self.root / 'coordination/verify_original_suite.py').write_text('print(\'{"verified_original_files": 11}\')\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'Synthetic guard fixture')
        self.sha = self.git('rev-parse', 'HEAD').strip()
        self.selected = self.root / '.github/relay/test_sample.py'
        MODULE.EXPECTED_COUNTS = {k: 1 for k in MODULE.EXPECTED_COUNTS}

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.root), *args], capture_output=True,
                              text=True, encoding='utf-8', check=True, timeout=20).stdout

    def gate(self):
        result = MODULE.run(self.root, self.sha)
        RESULTS.append({'case': self._testMethodName, 'status': result['status'],
                        'error_kind': result.get('error_kind'), 'total': result.get('total')})
        return result

    def test_clean_checkout_runs_three_real_synthetic_tests(self):
        result = self.gate()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['total'], 3)

    def hidden_change(self, flag):
        self.git('update-index', flag, '.github/relay/test_sample.py')
        self.selected.write_text(self.selected.read_text(encoding='utf-8') + '# modified bytes hidden by Git index\n', encoding='utf-8')
        self.assertEqual(self.git('status', '--porcelain', '--untracked-files=all'), '')
        result = self.gate()
        self.assertEqual(result['status'], 'BLOCKED')
        self.assertEqual(result['suites'], [], 'must block before executing source tests')

    def test_assume_unchanged_modified_test_is_blocked(self):
        self.hidden_change('--assume-unchanged')

    def test_skip_worktree_modified_test_is_blocked(self):
        self.hidden_change('--skip-worktree')

    def test_ordinary_modified_test_is_blocked(self):
        self.selected.write_text('# modified\n', encoding='utf-8')
        self.assertEqual(self.gate()['status'], 'BLOCKED')

    def test_unchanged_assume_flag_is_also_blocked(self):
        self.git('update-index', '--assume-unchanged', '.github/relay/test_sample.py')
        self.assertEqual(self.gate()['status'], 'BLOCKED')

    def test_unchanged_skip_flag_is_also_blocked(self):
        self.git('update-index', '--skip-worktree', '.github/relay/test_sample.py')
        self.assertEqual(self.gate()['status'], 'BLOCKED')

    def test_flag_added_during_suite_cannot_produce_pass(self):
        self.selected.write_text('import unittest, subprocess\nfrom pathlib import Path\n'
                                 'class Sample(unittest.TestCase):\n'
                                 '    def test_mutate(self):\n'
                                 '        subprocess.run(["git", "update-index", "--assume-unchanged", "coordination/test_sample.py"], check=True)\n'
                                 '        p=Path("coordination/test_sample.py")\n'
                                 '        p.write_bytes(p.read_bytes()+b"# hidden change\\n")\n', encoding='utf-8')
        self.git('add', '.')
        self.git('commit', '-qm', 'Synthetic in-suite mutation')
        self.sha = self.git('rev-parse', 'HEAD').strip()
        result = self.gate()
        self.assertEqual(result['status'], 'BLOCKED')

    def test_missing_tracked_file_is_blocked(self):
        self.selected.unlink()
        self.assertEqual(self.gate()['status'], 'BLOCKED')

    def test_untracked_test_is_blocked(self):
        (self.selected.parent / 'test_extra.py').write_text('# extra\n', encoding='utf-8')
        self.assertEqual(self.gate()['status'], 'BLOCKED')

    def test_wrong_expected_sha_is_blocked(self):
        self.assertEqual(MODULE.run(self.root, '0' * 40)['status'], 'BLOCKED')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    (Path(__file__).parent / 'scratch').mkdir(exist_ok=True)
    spec = importlib.util.spec_from_file_location('reviewed_gate', args.module)
    MODULE = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(MODULE)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SourceGuardTests))
    args.report.write_text(json.dumps({'synthetic_only': True, 'run': result.testsRun,
                                      'failures': len(result.failures), 'errors': len(result.errors),
                                      'observations': RESULTS}, indent=2) + '\n', encoding='utf-8')
    raise SystemExit(0 if result.wasSuccessful() else 1)
