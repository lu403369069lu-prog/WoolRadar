"""Fail closed on multiple framework aggregate summaries in one raw process log."""
import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent

def load(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

guard=load('historical_guard_summary_under_test','HISTORICAL_CODEX_42_RECEIPT_GUARD_20261017.py')
runner=load('historical_executor_summary_under_test','HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py')

class DuplicateAggregates(unittest.TestCase):
    def test_node_earlier_failure_later_clean_summary_not_accepted(self):
        raw=b'# tests 2\n# pass 1\n# fail 1\n# skipped 0\n# tests 1\n# pass 1\n# fail 0\n# skipped 0\n'
        self.assertIsNone(guard.parse_actual_log_counts(raw))

    def test_python_earlier_skip_later_clean_summary_not_accepted(self):
        raw=(b'Ran 2 tests in 0.001s\nOK (skipped=1)\n'
             b'Ran 1 test in 0.001s\nOK\n')
        self.assertIsNone(guard.parse_actual_log_counts(raw))

    def test_mixed_tap_and_unittest_summaries_not_accepted(self):
        raw=b'Ran 1 test in 0.001s\nOK\n# tests 1\n# pass 1\n# fail 0\n# skipped 0\n'
        self.assertIsNone(guard.parse_actual_log_counts(raw))

    def test_single_valid_node_and_python_still_accepted(self):
        self.assertEqual(guard.parse_actual_log_counts(b'# tests 1\n# pass 1\n# fail 0\n# skipped 0\n'),
                         {'tests':1,'passed':1,'failed':0,'skipped':0})
        self.assertEqual(guard.parse_actual_log_counts(b'Ran 1 test in 0.001s\nOK\n'),
                         {'tests':1,'passed':1,'failed':0,'skipped':0})

    def _spawn_synthetic(self, raw):
        with tempfile.TemporaryDirectory() as repo:
            cmd='SYNTHETIC-DUPLICATE-COUNTS'
            key=hashlib.sha256(cmd.encode()).hexdigest()
            entry={'argv':[sys.executable,'-c',f'import sys;sys.stdout.buffer.write({raw!r})'],
                   'cwd':Path(repo),'cwd_contract':'.','command':cmd,'key_sha256':key}
            mapping=[{'family_id':'SYNTHETIC','source_blob':'none','command_key':key}]
            code,receipt,output=runner.run_commands([entry],mapping,guard.HEADS['wool'],'wool')
            self.addCleanup(lambda: shutil.rmtree(output,ignore_errors=True))
            return code,receipt,output

    def test_node_mixed_summary_runner_cannot_emit_green_receipt(self):
        raw=b'# tests 2\n# pass 2\n# fail 0\n# skipped 0\n# tests 1\n# pass 1\n# fail 0\n# skipped 0\n'
        code,receipt,output=self._spawn_synthetic(raw)
        self.assertNotEqual(code,0)
        formal=json.loads((output/'receipt-guard-v1.json').read_text())
        self.assertNotEqual(formal['results'][0]['exit_code'],0)

    def test_python_mixed_summary_runner_cannot_emit_green_receipt(self):
        raw=b'Ran 2 tests in 0.001s\nOK\nRan 1 test in 0.001s\nOK (skipped=1)\n'
        code,receipt,output=self._spawn_synthetic(raw)
        self.assertNotEqual(code,0)
        formal=json.loads((output/'receipt-guard-v1.json').read_text())
        self.assertNotEqual(formal['results'][0]['exit_code'],0)

if __name__=='__main__':unittest.main()
