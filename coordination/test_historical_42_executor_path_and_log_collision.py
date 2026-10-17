"""No-skip adversarial source-path and command-log integrity tests."""
from __future__ import annotations
import hashlib
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

SRC=Path(__file__).with_name('HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py')
spec=importlib.util.spec_from_file_location('runner_new_security',SRC)
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def job(rel,cwd,cmd):
    return {'verified_test_path':rel,'verified_test_blob':'verified',
            'local_cwd':cwd,'run_command':cmd}

class PathAndLogSecurity(unittest.TestCase):
    def test_reject_symlink_parent_test_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'real').mkdir();(root/'real/test_case.py').write_text('pass\n')
            (root/'tests').symlink_to(root/'real',target_is_directory=True)
            with self.assertRaises(RuntimeError):
                runner.pin_command(root,job('tests/test_case.py','.',
                    'python -B -m unittest discover -s tests -p test_case.py -v'),
                    blob_lookup=lambda _:'verified')

    def test_reject_symlink_command_directory_to_same_regular_test(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'tests').mkdir();(root/'tests/test_case.py').write_text('pass\n')
            (root/'shortcut').symlink_to(root/'tests',target_is_directory=True)
            with self.assertRaises(RuntimeError):
                runner.pin_command(root,job('tests/test_case.py','.',
                    'python -B -m unittest discover -s shortcut -p test_case.py -v'),
                    blob_lookup=lambda _:'verified')

    def test_reject_symlink_working_directory(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'actual').mkdir();(root/'actual/tests').mkdir();
            (root/'actual/tests/test_case.py').write_text('pass\n')
            (root/'alias').symlink_to(root/'actual',target_is_directory=True)
            with self.assertRaises(RuntimeError):
                runner.pin_command(root,job('actual/tests/test_case.py','alias',
                    'python -B -m unittest discover -s tests -p test_case.py -v'),
                    blob_lookup=lambda _:'verified')

    def test_no_log_overwrite_for_same_first_16_digest_nibbles(self):
        prefix='f'*16
        ka,kb=prefix+'0'*48,prefix+'1'*48
        outputs=[b'Ran 1 test in 0.001s\nOK\n',b'Ran 2 tests in 0.002s\nOK\n']
        commands=[{'argv':[sys.executable,'-c',f'import sys;sys.stdout.buffer.write({out!r})'],
                   'cwd':Path(tempfile.gettempdir()),'key_sha256':k,'command':f'synthetic-{i}'}
                  for i,(k,out) in enumerate(zip((ka,kb),outputs))]
        mapping=[{'family_id':f'F{i}','source_blob':'verified','command_key':k}
                 for i,k in enumerate((ka,kb))]
        rc,receipt,folder=runner.run_commands(commands,mapping,'fixed','wool')
        self.addCleanup(lambda:shutil.rmtree(folder,ignore_errors=True))
        self.assertEqual(rc,0)
        for k,out in zip((ka,kb),outputs):
            self.assertEqual((folder/(k+'.log')).read_bytes(),out)
        self.assertEqual(len([p for p in folder.glob('*.log') if len(p.stem)==64]),2)
        # Official guard receipt adds one byte-identical test-NNN.log per command.
        self.assertEqual(sorted(p.name for p in folder.glob('test-*.log')),
                         ['test-000.log','test-001.log'])
        for i,out in enumerate(outputs):
            self.assertEqual((folder/f'test-{i:03d}.log').read_bytes(),out)
        self.assertEqual([r['log_sha256'] for r in receipt['results']],
                         [hashlib.sha256(out).hexdigest() for out in outputs])

    def test_duplicate_family_name_rejected(self):
        cs, ms=self.good_commands_and_mapping()
        with self.assertRaises(RuntimeError):runner.run_commands(cs,ms+ms,'fixed','wool')

    def test_duplicate_command_key_rejected(self):
        cs, ms=self.good_commands_and_mapping()
        with self.assertRaises(RuntimeError):runner.run_commands(cs+cs,ms,'fixed','wool')

    def test_unmapped_command_rejected(self):
        cs, ms=self.good_commands_and_mapping()
        with self.assertRaises(RuntimeError):runner.run_commands(cs,[{**ms[0], 'command_key':'0'*64}],'fixed','wool')

    def test_malformed_digest_name_rejected_before_file_creation(self):
        cs, ms=self.good_commands_and_mapping()
        cs[0]['key_sha256']='../escape'
        ms[0]['command_key']='../escape'
        with self.assertRaises(RuntimeError):runner.run_commands(cs,ms,'fixed','wool')

    def test_legitimate_real_nested_file_is_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'tests').mkdir();(root/'tests/test_case.py').write_text('pass\n')
            cwd,argv=runner.pin_command(root,job('tests/test_case.py','.',
                'python -B -m unittest discover -s tests -p test_case.py -v'),
                blob_lookup=lambda _:'verified')
            self.assertEqual(cwd,root.resolve());self.assertEqual(argv[0],sys.executable)

    def test_sam_sibling_command_path_remains_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'SAM/snapshot').mkdir(parents=True)
            (root/'SAM/independent-review').mkdir()
            (root/'SAM/independent-review/rooted.test.mjs').write_text('// synthetic\n')
            entry=job('SAM/independent-review/rooted.test.mjs','SAM/snapshot',
                      'node --test ../independent-review/rooted.test.mjs')
            cwd,argv=runner.pin_command(root,entry,blob_lookup=lambda _:'verified')
            self.assertEqual(cwd,root/'SAM/snapshot')
            self.assertEqual(argv[-1],'../independent-review/rooted.test.mjs')

    def test_sam_command_escape_above_checkout_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/'SAM/snapshot').mkdir(parents=True)
            (root/'SAM/independent-review').mkdir()
            (root/'SAM/independent-review/rooted.test.mjs').write_text('// synthetic\n')
            entry=job('SAM/independent-review/rooted.test.mjs','SAM/snapshot',
                      'node --test ../../../outside/rooted.test.mjs')
            with self.assertRaises(RuntimeError):
                runner.pin_command(root,entry,blob_lookup=lambda _:'verified')

    def good_commands_and_mapping(self):
        key='f'*64
        cs=[{'argv':[sys.executable,'-c','print("OK")'],
             'cwd':Path(tempfile.gettempdir()),'key_sha256':key,'command':'one'}]
        return cs,[{'family_id':'F1','source_blob':'verified','command_key':key}]

if __name__=='__main__':unittest.main()
