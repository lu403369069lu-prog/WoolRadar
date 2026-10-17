"""Synthetic output receipts protect against false PASS in the Codex batch runner."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('hist_verdict', ROOT / 'coordination' / 'HISTORICAL_CODEX_BATCH_RUNNER_20261017.py')
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)

class BatchRunVerdict(unittest.TestCase):
    def verdict(self, log, exit_code=0, batch='W-ALL'):
        return RUNNER.evaluate_run(batch, exit_code, log)
    def test_python_zero_tests_rejected(self):
        rc,c=self.verdict('Ran 0 tests in 0.001s\n\nOK\n');self.assertEqual((rc,c['tests_reported']),(126,0))
    def test_python_true_pass(self):
        rc,c=self.verdict('Ran 3 tests in 0.010s\n\nOK\n');self.assertEqual((rc,c['passed']),(0,3))
    def test_python_skip_rejected(self):
        rc,c=self.verdict('Ran 3 tests in 0.010s\n\nOK (skipped=1)\n');self.assertEqual(rc,126)
    def test_python_error_not_pass(self):
        rc,c=self.verdict('Ran 3 tests in 0.010s\nFAILED (failures=1, errors=1)\n',1);self.assertEqual((rc,c['failed']),(1,2))
    def test_node_tap_true_pass(self):
        rc,c=self.verdict('# tests 2\n# pass 2\n# fail 0\n# skipped 0\n',0,'S-ALL');self.assertEqual((rc,c['passed']),(0,2))
    def test_node_partial_skip_rejected(self):
        rc,_=self.verdict('# tests 2\n# pass 1\n# fail 0\n# skipped 1\n',0,'S-ALL');self.assertEqual(rc,126)
    def test_node_all_skip_rejected(self):
        rc,_=self.verdict('# tests 2\n# pass 0\n# fail 0\n# skipped 2\n',0,'S-ALL');self.assertEqual(rc,126)
    def test_node_inconsistent_counts_rejected(self):
        rc,_=self.verdict('# tests 3\n# pass 2\n# fail 0\n# skipped 0\n',0,'S-ALL');self.assertEqual(rc,126)
    def test_node_missing_fail_count_rejected(self):
        rc,_=self.verdict('# tests 2\n# pass 2\n',0,'S-ALL');self.assertEqual(rc,126)
    def test_missing_summary_rejected(self):
        rc,_=self.verdict('Everything passed\n',0,'W-ALL');self.assertEqual(rc,126)
    def test_runtime_failure_retained(self):
        rc,_=self.verdict('setup failed\n',1,'W-ALL');self.assertEqual(rc,1)
    def test_compile_only_success_is_allowed(self):
        rc,_=self.verdict('TypeScript compile succeeded\n',0,'S-BUILD');self.assertEqual(rc,0)
    def test_zero_total_tap_rejected(self):
        rc,_=self.verdict('# tests 0\n# pass 0\n# fail 0\n# skipped 0\n',0,'S-ALL');self.assertEqual(rc,126)
    def test_python_unverified_summary_rejected(self):
        rc,_=self.verdict('Ran 2 tests in 0.1s\n',0,'W-ALL');self.assertEqual(rc,126)

if __name__=='__main__':unittest.main()
