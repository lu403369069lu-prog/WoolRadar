"""Native unittest summary cannot hide a failed wrapper cleanup phase."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

SPEC = importlib.util.spec_from_file_location('tail_worker', Path(__file__).with_name('worker.py'))
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)


class PythonSummaryTailTests(unittest.TestCase):
    def test_real_runner_cleanup_error_after_ok_is_not_pass(self):
        source = '''import sys, traceback, unittest
class T(unittest.TestCase):
    def test_ok(self): self.assertTrue(True)
result = unittest.TextTestRunner(stream=sys.stdout).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
try:
    raise RuntimeError('wrapper cleanup failed')
except RuntimeError:
    traceback.print_exc(file=sys.stdout)
sys.exit(0 if result.wasSuccessful() else 1)
'''
        proc = subprocess.run([sys.executable, '-B', '-X', 'utf8', '-c', source],
                              capture_output=True, text=True, check=False, timeout=20)
        self.assertEqual(proc.returncode, 0)
        self.assertIn('OK\nTraceback', proc.stdout.replace('\r\n', '\n'))
        self.assertEqual(worker.parse_test_summary(proc.stdout + proc.stderr, 0)['status'], 'FAIL')

    def test_unittest_run_line_must_be_complete(self):
        for output in ('Ran 1 test rubbish\n\nOK\n',
                       'Ran 1 test in 0.001s\n\nOK\nFAILED (errors=1)\n',
                       'Ran 1 test in 0.001s\n\nOK\nnot ok 1 - cleanup\n'):
            with self.subTest(output=output):
                self.assertEqual(worker.parse_test_summary(output, 0)['status'], 'FAIL')

    def test_standard_and_crlf_ok_remain_pass(self):
        for output in ('Ran 2 tests in 0.001s\n\nOK\n',
                       'Ran 1 test in 1.250s\r\n\r\nOK\r\n',
                       'test_ok ... ok\nRan 1 test in 0.000s\n\nOK (skipped=0)\n\n'):
            with self.subTest(output=output):
                self.assertEqual(worker.parse_test_summary(output, 0)['status'], 'PASS')
