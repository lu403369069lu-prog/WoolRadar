"""Real unsafe log-file edge cases must not produce a frozen PASS receipt.

Synthetic bypasses of the *old path precheck* model a filesystem race; the
new implementation requires O_NOFOLLOW descriptor-based reading.
"""
from __future__ import annotations
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).parent
sp=importlib.util.spec_from_file_location('log_guard_under_test',HERE/'HISTORICAL_CODEX_42_RECEIPT_GUARD_20261017.py')
guard=importlib.util.module_from_spec(sp);sp.loader.exec_module(guard)
VALID=b'Ran 1 test in 0.001s\nOK\n'

class RawLogMustRemainPinned(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        cmd='python -B -m unittest discover -s tests -p test_synthetic.py -v'
        self.manifest={'jobs':[{'family_id':'SYN','project':'WoolRadar','disposition':'READY_FOR_LOCAL_CODEX','run_command':cmd,'local_cwd':'.'}]}
        self.receipt={'project':'wool','repo_sha':guard.HEADS['wool'],'schema_version':1,
                      'source':'disposable-local-codex','no_real_gold_claim':True,'production_modified':False,
                      'runtime':{'python':'3.13.5','platform':'Linux'},
                      'unique_commands':1,'tested_families':1,
                      'results':[{'family_ids':['SYN'],'cwd':'.','argv':cmd.split(),
                                  'local_log':'test-000.log','sha256':hashlib.sha256(VALID).hexdigest(),
                                  'exit_code':0,'status':'PASS',
                                  'counts':{'tests':1,'passed':1,'failed':0,'skipped':0}}]}
        self.log=self.root/'test-000.log'
        self.log.write_bytes(VALID)

    def verdict(self):
        return guard.review(self.receipt,self.manifest,self.root)

    def test_normal_valid_small_regular_log_remains_accepted(self):
        self.assertTrue(self.verdict()['local_full_family_receipt_accepted'])

    def test_log_with_excessive_trailing_bytes_cannot_be_accepted(self):
        huge=VALID+b' '* (8 * 1024 * 1024+1)
        self.log.write_bytes(huge)
        self.receipt['results'][0]['sha256']=hashlib.sha256(huge).hexdigest()
        result=self.verdict()
        self.assertFalse(result['local_full_family_receipt_accepted'])
        self.assertIn('UNSAFE_RAW_LOG_TYPE_OR_SIZE',result['errors'])

    @unittest.skipUnless(hasattr(os,'mkfifo'),'FIFO only available on POSIX')
    def test_fifo_cannot_block_or_supply_fake_log(self):
        self.log.unlink();os.mkfifo(self.log)
        original=Path.read_bytes
        def fake_read(path):
            if path == self.log: return VALID  # simulate old read after type check
            return original(path)
        with patch.object(Path,'read_bytes',fake_read):
            result=self.verdict()
        self.assertFalse(result['local_full_family_receipt_accepted'])
        self.assertIn('UNSAFE_RAW_LOG_TYPE_OR_SIZE',result['errors'])

    def test_symlink_swapped_after_precheck_is_rejected(self):
        private=self.root/'private_unrelated_file.log';private.write_bytes(VALID)
        self.log.unlink();self.log.symlink_to(private)
        real_is_symlink=Path.is_symlink
        def stale_precheck(path):
            if path == self.log: return False  # model stale precheck during race
            return real_is_symlink(path)
        with patch.object(Path,'is_symlink',stale_precheck):
            result=self.verdict()
        self.assertFalse(result['local_full_family_receipt_accepted'])
        self.assertIn('UNSAFE_RAW_LOG_TYPE_OR_SIZE',result['errors'])

    @unittest.skipUnless(hasattr(os, 'O_NOFOLLOW'), 'POSIX simulation of missing Win32 nofollow')
    def test_windows_fallback_accepts_stable_regular_log(self):
        # Exercise the Windows fallback branch on Linux without claiming
        # actual Windows filesystem or reparse-point acceptance.
        old_flag = os.O_NOFOLLOW
        delattr(os, 'O_NOFOLLOW')
        try:
            self.assertTrue(self.verdict()['local_full_family_receipt_accepted'])
        finally:
            os.O_NOFOLLOW = old_flag

    @unittest.skipUnless(hasattr(os, 'O_NOFOLLOW'), 'POSIX simulation of missing Win32 nofollow')
    def test_windows_fallback_rejects_swapped_link_after_lstat(self):
        private=self.root/'private-unrelated.log';private.write_bytes(VALID)
        original_open = os.open
        old_flag=os.O_NOFOLLOW
        delattr(os,'O_NOFOLLOW')
        def swap_open(target, flags, *args, **kwargs):
            if str(target) == str(self.log):
                self.log.unlink()
                self.log.symlink_to(private)
            return original_open(target, flags, *args, **kwargs)
        try:
            with patch.object(os,'open',swap_open):
                verdict=self.verdict()
        finally:
            os.O_NOFOLLOW=old_flag
        self.assertFalse(verdict['local_full_family_receipt_accepted'])
        self.assertIn('UNSAFE_RAW_LOG_TYPE_OR_SIZE',verdict['errors'])

if __name__=='__main__':unittest.main()
