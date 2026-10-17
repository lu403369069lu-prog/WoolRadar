"""A previous approved test command must not be allowed to change later test bytes."""
import hashlib
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('runtime_repin_runner',HERE/'HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py')
runner=importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def git_blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\x00'+raw).hexdigest()

class RuntimeRePin(unittest.TestCase):
    def fixture(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        (self.root/'tests').mkdir()
        target=self.root/'tests/test_second.py'
        target.write_text('import unittest\nclass T(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n')
        return target

    def execute(self,commands):
        for command in commands:
            command['key_sha256']=hashlib.sha256(command['command'].encode()).hexdigest()
        mapping=[{'family_id':f'F{i}', 'source_blob':'synthetic', 'command_key':c['key_sha256']}
                 for i,c in enumerate(commands)]
        rc, receipt,folder=runner.run_commands(commands,mapping,'mock','wool')
        self.addCleanup(lambda:shutil.rmtree(folder,ignore_errors=True))
        return rc,receipt

    def test_prior_command_cannot_mutate_next_pinned_test_to_fake_green(self):
        target=self.fixture()
        sha=git_blob(target.read_bytes())
        tampered=('import unittest\nfrom pathlib import Path\n'
                  'class T(unittest.TestCase):\n def test_ok(self):\n'
                  '  Path("tampered_ran").write_text("YES")\n  self.assertTrue(True)\n')
        mutate=f'import pathlib,sys;pathlib.Path({str(target)!r}).write_text({tampered!r});sys.stdout.write("Ran 1 test in 0.001s\\nOK\\n")'
        commands=[
            {'cwd':self.root,'cwd_contract':'.', 'command':'mutation-command',
             'argv':[sys.executable,'-c',mutate]},
            {'cwd':self.root,'cwd_contract':'.','command':'subsequent-pinned-test',
             'argv':[sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_second.py','-v'],
             'pinned_test':{'root':self.root,'relative':'tests/test_second.py','blob':sha}}
        ]
        rc,receipt=self.execute(commands)
        self.assertNotEqual(rc,0)
        self.assertFalse((self.root/'tampered_ran').exists(), 'tampered test actually executed')
        self.assertNotEqual(receipt['results'][-1]['exit_code'],0)

    def test_unchanged_exact_pinned_test_still_executes(self):
        target=self.fixture()
        sha=git_blob(target.read_bytes())
        commands=[{'cwd':self.root,'cwd_contract':'.','command':'unchanged-pinned-test',
             'argv':[sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_second.py','-v'],
             'pinned_test':{'root':self.root,'relative':'tests/test_second.py','blob':sha}}]
        rc,receipt=self.execute(commands)
        self.assertEqual(rc,0)
        self.assertEqual(receipt['results'][0]['status'],'PASS_EXACT_HEAD')

if __name__=='__main__': unittest.main()
