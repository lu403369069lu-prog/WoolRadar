"""Recognize real Node reporters without accepting incomplete or ambiguous runs."""
import shutil
import subprocess
import tempfile
from pathlib import Path
import unittest

from worker import parse_test_summary


def summary(prefix, *, total=2, passed=2, failed=0, skipped=0, todo=0, cancelled=0):
    counts = dict(tests=total, pass_=passed, fail=failed, skipped=skipped,
                  todo=todo, cancelled=cancelled)
    return '\n'.join(prefix + ' ' + k.rstrip('_') + ' ' + str(v)
                     for k, v in counts.items()) + '\n'


class NodeSummaryContracts(unittest.TestCase):
    def test_spec_reporter_all_categories(self):
        result = parse_test_summary(summary('\u2139'), 0)
        self.assertEqual((result['status'], result['total'], result['passed']), ('PASS', 2, 2))

    def test_duplicate_or_mixed_summaries_cannot_select_last_pass(self):
        for output in (summary('#', passed=1, failed=1) + summary('#'),
                       summary('\u2139', passed=1, failed=1) + summary('\u2139'),
                       summary('#', passed=1, failed=1) + summary('\u2139'),
                       summary('#') + 'Ran 2 tests in 0.1s\nOK\n'):
            with self.subTest(output=output):
                self.assertEqual(parse_test_summary(output, 0)['status'], 'FAIL')

    def test_spec_incomplete_failed_skipped_todo_and_exit_status(self):
        for output, code in ((summary('\u2139').replace('\u2139 cancelled 0\n', ''), 0),
                             (summary('\u2139', passed=1, failed=1), 1),
                             (summary('\u2139', passed=1, skipped=1), 0),
                             (summary('\u2139', passed=1, todo=1), 0),
                             (summary('\u2139'), 1)):
            with self.subTest(output=output, code=code):
                self.assertEqual(parse_test_summary(output, code)['status'], 'FAIL')

    def test_actual_node_subprocess_reporters(self):
        node = shutil.which('node')
        self.assertIsNotNone(node, 'Node is required to validate the actual reporter contract')
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / 'fixture.test.mjs'
            fixture.write_text("import {test} from 'node:test';\ntest('real test',()=>{});\n", encoding='utf-8')
            for reporter in ('tap', 'spec'):
                with self.subTest(reporter=reporter):
                    proc = subprocess.run([node, '--test', '--test-reporter=' + reporter, str(fixture)],
                                          capture_output=True, text=True, encoding='utf-8', timeout=30,
                                          env={**__import__('os').environ, 'NO_COLOR': '1'})
                    self.assertEqual(proc.returncode, 0, proc.stderr)
                    result = parse_test_summary(proc.stdout + '\n' + proc.stderr, proc.returncode)
                    self.assertEqual((result['status'], result['total'], result['passed']), ('PASS', 1, 1))
