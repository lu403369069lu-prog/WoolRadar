"""Independent synthetic process and symlink security gates for 42-job executor."""
import hashlib
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SRC=Path(__file__).with_name('HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py')
spec=importlib.util.spec_from_file_location('runner_under_test', SRC)
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)

class RunnerEvidenceIntegrity(unittest.TestCase):
    def test_raw_invalid_utf8_is_persisted_and_hashed_losslessly(self):
        raw=b'\xff\xfe\nRan 1 test in 0.001s\nOK\n'
        cmd={'argv':[sys.executable,'-c',f'import sys;sys.stdout.buffer.write({raw!r})'],
             'cwd':Path(tempfile.gettempdir()), 'key_sha256':'a'*64,'command':'synthetic'}
        mapping=[{'family_id':'WR-HQ','source_blob':'synthetic','command_key':cmd['key_sha256']}]
        rc,receipt,folder=runner.run_commands([cmd],mapping,'test-commit','wool')
        self.addCleanup(lambda: shutil.rmtree(folder,ignore_errors=True))
        self.assertNotEqual(rc,0)  # non-UTF8 output cannot pass strict official guard
        self.assertEqual((folder/('a'*64+'.log')).read_bytes(),raw)
        self.assertEqual(receipt['results'][0]['log_sha256'],hashlib.sha256(raw).hexdigest())

    def test_pinned_symlink_in_repo_must_be_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'tests').mkdir()
            (root/'tests/real.py').write_text('pass\n')
            link=root/'tests/test_link.py'
            try: link.symlink_to(root/'tests/real.py')
            except (OSError,NotImplementedError): self.skipTest('no symlink permission')
            job={'verified_test_path':'tests/test_link.py','verified_test_blob':'fake',
                 'local_cwd':'.','run_command':'python -B -m unittest discover -s tests -p test_link.py -v'}
            with self.assertRaises(RuntimeError):
                runner.pin_command(root,job,blob_lookup=lambda _: 'fake')

    def test_empty_commands_must_not_return_success_receipt(self):
        with self.assertRaises(RuntimeError):
            runner.run_commands([],[],'test-commit','wool')

    def test_regular_file_still_passes_pin(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/'tests').mkdir()
            (root/'tests/test_valid.py').write_text('pass\n')
            job={'verified_test_path':'tests/test_valid.py','verified_test_blob':'fake',
                 'local_cwd':'.','run_command':'python -B -m unittest discover -s tests -p test_valid.py -v'}
            cwd,argv=runner.pin_command(root,job,blob_lookup=lambda _: 'fake')
            self.assertEqual(cwd,root.resolve()); self.assertEqual(argv[0],sys.executable)

    def test_ascii_log_remains_byte_exact(self):
        raw=b'Ran 1 test in 0.001s\nOK\n'
        cmd={'argv':[sys.executable,'-c',f'import sys;sys.stdout.buffer.write({raw!r})'],
             'cwd':Path(tempfile.gettempdir()), 'key_sha256':'b'*64,'command':'synthetic'}
        mapping=[{'family_id':'WR-HQ','source_blob':'synthetic','command_key':cmd['key_sha256']}]
        rc,receipt,folder=runner.run_commands([cmd],mapping,'test-commit','wool')
        self.addCleanup(lambda: shutil.rmtree(folder,ignore_errors=True))
        self.assertEqual(rc,0)
        self.assertEqual((folder/('b'*64+'.log')).read_bytes(),raw)
        self.assertEqual(receipt['results'][0]['log_sha256'],hashlib.sha256(raw).hexdigest())

if __name__=='__main__':unittest.main()
