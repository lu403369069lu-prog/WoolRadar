"""A prior clean-pinned test cannot silently rewrite a dependency before later tests."""
import hashlib
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('pinned_dependency_under_test', ROOT/'HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def sha_git(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()


def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args], text=True).strip()


class RuntimeDependencyMutation(unittest.TestCase):
    def execute(self, corrupt, last_only=False):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'tests').mkdir()
            (root/'core').mkdir()
            (root/'core/policy.py').write_text('def flag(): return False\n')
            modified = 'def flag(): return True\\n'
            if corrupt:
                first = ('from pathlib import Path\nimport unittest\nclass T(unittest.TestCase):\n'
                         ' def test_modify_dependency(self):\n'
                         f'  Path("core/policy.py").write_text({modified!r}.replace("\\\\n","\\n"))\n')
                second = ('import unittest\nfrom core.policy import flag\nclass T(unittest.TestCase):\n'
                          ' def test_dep(self):\n'
                          '  open("second_ran", "w").write("yes")\n'
                          '  self.assertTrue(flag())\n')
            else:
                first = 'import unittest\nclass T(unittest.TestCase):\n def test_clean(self): self.assertTrue(True)\n'
                second = ('import unittest\nfrom core.policy import flag\nclass T(unittest.TestCase):\n'
                          ' def test_dep(self): self.assertFalse(flag())\n')
            (root/'tests/test_first.py').write_text(first)
            (root/'tests/test_second.py').write_text(second)
            git(root,'init','-q')
            git(root,'add','tests','core')
            git(root,'-c','user.name=QA','-c','user.email=qa@example.org','commit','-qm','frozen')
            sha=git(root,'rev-parse','HEAD')
            commands=[]
            for idx,name in enumerate(('first','second')):
                arg=[sys.executable,'-B','-m','unittest','discover','-s','tests','-p',f'test_{name}.py','-v']
                cmd=f'python -B -m unittest discover -s tests -p test_{name}.py -v'
                path=f'tests/test_{name}.py'
                commands.append({'cwd':root,'cwd_contract':'.', 'command':cmd, 'argv':arg,
                                 'key_sha256':hashlib.sha256(cmd.encode()).hexdigest(),
                                 'pinned_test':{'root':root,'relative':path,'blob':git(root,'rev-parse','HEAD:'+path)},
                                 'require_git_clean': True})
            if last_only:
                commands=commands[:1]
            mapping=[{'family_id':f'C-{i}', 'source_blob':'synthetic', 'command_key':c['key_sha256']}
                     for i,c in enumerate(commands)]
            rc,receipt,folder=runner.run_commands(commands,mapping,sha,'wool')
            self.addCleanup(lambda:shutil.rmtree(folder,ignore_errors=True))
            return rc,receipt,(root/'second_ran').exists()

    def test_mutating_dependency_is_blocked_even_though_next_test_blob_same(self):
        rc,receipt,second_ran=self.execute(True)
        self.assertNotEqual(rc,0,receipt['results'])
        self.assertFalse(second_ran)
        self.assertNotEqual(receipt['results'][-1]['exit_code'],0)

    def test_single_final_test_cannot_modify_tracked_source_and_report_pass(self):
        rc, receipt, _ = self.execute(True, last_only=True)
        self.assertNotEqual(rc, 0)
        self.assertNotEqual(receipt['results'][0]['exit_code'], 0)

    def test_clean_dependency_allows_both_commands(self):
        rc,receipt,second_ran=self.execute(False)
        self.assertEqual(rc,0,receipt['results'])
        self.assertTrue(all(r['status']=='PASS_EXACT_HEAD' for r in receipt['results']))

if __name__=='__main__': unittest.main()
