"""Formal receipt fail-closed on unfinished TAP plans and JSON Boolean integers."""
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

SRC=Path(__file__).with_name('HISTORICAL_CODEX_42_RECEIPT_GUARD_20261017.py')
spec=importlib.util.spec_from_file_location('strict_guard_under_test',SRC)
guard=importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

GOOD_TAP=b'# tests 1\n# pass 1\n# fail 0\n# skipped 0\n# cancelled 0\n# todo 0\n'

class StrictReceiptTypesAndTestCompleteness(unittest.TestCase):
    def test_positive_cancelled_tap_must_not_count_as_all_passed(self):
        self.assertIsNone(guard.parse_actual_log_counts(GOOD_TAP.replace(b'# cancelled 0',b'# cancelled 1')))

    def test_todo_tap_must_not_be_certified_as_completed_tests(self):
        self.assertIsNone(guard.parse_actual_log_counts(GOOD_TAP.replace(b'# todo 0',b'# todo 1')))

    def test_duplicate_optional_node_summary_cannot_hide_earlier_cancel(self):
        self.assertIsNone(guard.parse_actual_log_counts(GOOD_TAP.replace(b'# cancelled 0',b'# cancelled 1\n# cancelled 0')))

    def test_zero_cancelled_and_todo_node_summary_remains_valid(self):
        self.assertEqual(guard.parse_actual_log_counts(GOOD_TAP),
            {'tests':1,'passed':1,'failed':0,'skipped':0})

    def _valid_review(self):
        self.folder=tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        root=Path(self.folder.name)
        log=b'Ran 1 test in 0.001s\nOK\n'
        (root/'test-000.log').write_bytes(log)
        cmd='python -B -m unittest discover -s tests -p test_synthetic.py -v'
        args=cmd.split()
        manifest={'jobs':[{'family_id':'SYN-1', 'project':'WoolRadar',
                'disposition':'READY_FOR_LOCAL_CODEX', 'run_command':cmd,'local_cwd':'.'}]}
        receipt={'project':'wool','repo_sha':guard.HEADS['wool'],
                 'schema_version':1,'source':'disposable-local-codex',
                 'no_real_gold_claim':True,'production_modified':False,
                 'runtime':{'python':'3.13.5','platform':'Linux'},
                 'unique_commands':1,'tested_families':1,
                 'results':[{'family_ids':['SYN-1'], 'cwd':'.','argv':args,
                     'local_log':'test-000.log','sha256':hashlib.sha256(log).hexdigest(),
                     'exit_code':0,'status':'PASS',
                     'counts':{'tests':1,'passed':1,'failed':0,'skipped':0}}]}
        return manifest,receipt,root

    def test_boolean_schema_version_cannot_masquerade_as_integer_one(self):
        manifest,receipt,root=self._valid_review()
        self.assertTrue(guard.review(receipt,manifest,root)['local_full_family_receipt_accepted'])
        receipt['schema_version']=True
        verdict=guard.review(receipt,manifest,root)
        self.assertFalse(verdict['local_full_family_receipt_accepted'])
        self.assertIn('UNTRUSTED_PROVENANCE',verdict['errors'])

    def test_boolean_command_or_family_total_cannot_masquerade_as_one(self):
        manifest,receipt,root=self._valid_review()
        receipt['unique_commands']=True
        receipt['tested_families']=True
        verdict=guard.review(receipt,manifest,root)
        self.assertFalse(verdict['local_full_family_receipt_accepted'])
        self.assertIn('COMMAND_COUNT_MISMATCH',verdict['errors'])
        self.assertIn('FAMILY_COUNT_MISMATCH',verdict['errors'])

if __name__=='__main__': unittest.main()
