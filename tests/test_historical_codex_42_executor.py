"""40+ history families via allowlisted command validation (synthetic checkout)."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('historical_job_executor',ROOT/'coordination'/'HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py')
EXEC=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EXEC)

class SafeCommands(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        for rel in ('tests/test_a.py','SAM/snapshot/test/a.ts',
                    'SAM/independent-review/20261016/a.test.ts',
                    'SAM/independent-review/20261016-0904-audit-coverage/a.test.mjs'):
            p=self.root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('fake source','utf-8')
    def job(self,p,command,cwd='.'):
        return {'family_id':'SYN-H1','project':'WoolRadar','disposition':'READY_FOR_LOCAL_CODEX',
                'local_cwd':cwd,'verified_test_path':p,'verified_test_blob':'f'*40,
                'run_command':command}
    def lookup(self,path):return 'f'*40
    def test_python_allowlist(self):
        j=self.job('tests/test_a.py','python -B -m unittest discover -s tests -p test_a.py -v')
        cwd,argv=EXEC.pin_command(self.root,j,self.lookup)
        self.assertEqual(cwd,self.root);self.assertEqual(argv[1:],['-B','-m','unittest','discover','-s','tests','-p','test_a.py','-v'])
    def test_node_ts_allowlist(self):
        j=self.job('SAM/snapshot/test/a.ts','node --import tsx --test test/a.ts','SAM/snapshot')
        self.assertEqual(EXEC.pin_command(self.root,j,self.lookup)[1][-1],'test/a.ts')
    def test_independent_node_glob(self):
        j=self.job('SAM/independent-review/20261016/a.test.ts','node --import tsx --test ../independent-review/20261016/a.test.ts','SAM/snapshot')
        self.assertEqual(EXEC.pin_command(self.root,j,self.lookup)[1][-1],'../independent-review/20261016/a.test.ts')
    def test_node_mjs(self):
        j=self.job('SAM/independent-review/20261016-0904-audit-coverage/a.test.mjs','node --test ../independent-review/20261016-0904-audit-coverage/a.test.mjs','SAM/snapshot')
        self.assertEqual(EXEC.pin_command(self.root,j,self.lookup)[1][0],'node')
    def test_wrong_blob_blocked(self):
        j=self.job('tests/test_a.py','python -B -m unittest discover -s tests -p test_a.py -v')
        with self.assertRaisesRegex(RuntimeError,'Git blob'):
            EXEC.pin_command(self.root,j,lambda _: 'e'*40)
    def test_arbitrary_command_rejected(self):
        j=self.job('tests/test_a.py','python -c print(99)')
        with self.assertRaisesRegex(RuntimeError,'allowlisted'): EXEC.pin_command(self.root,j,self.lookup)
    def test_wrong_test_path_rejected(self):
        j=self.job('tests/test_a.py','python -B -m unittest discover -s tests -p other.py -v')
        with self.assertRaisesRegex(RuntimeError,'test path'): EXEC.pin_command(self.root,j,self.lookup)
    def test_shell_append_rejected(self):
        j=self.job('tests/test_a.py','python -B -m unittest discover -s tests -p test_a.py -v ; rm -rf .')
        with self.assertRaisesRegex(RuntimeError,'allowlisted'):EXEC.pin_command(self.root,j,self.lookup)
    def test_missing_target_blocked(self):
        j=self.job('tests/no.py','python -B -m unittest discover -s tests -p no.py -v')
        with self.assertRaisesRegex(RuntimeError,'target missing'): EXEC.pin_command(self.root,j,self.lookup)
    def test_deduplicate_by_exact_command(self):
        command='python -B -m unittest discover -s tests -p test_a.py -v'
        a=self.job('tests/test_a.py',command)
        b=dict(a,family_id='SYN-H2')
        cmds,rows=EXEC.plan_jobs(self.root,'wool',{'jobs':[a,b]},self.lookup)
        self.assertEqual((len(cmds),len(rows)),(1,2))
        self.assertEqual(rows[0]['command_key'],rows[1]['command_key'])
    def test_symlink_outside_checkout_denied(self):
        with tempfile.TemporaryDirectory() as outside:
            dest=Path(outside)/'secret.py';dest.write_text('private','utf-8')
            path=self.root/'tests'/'link.py'
            path.symlink_to(dest)
            j=self.job('tests/link.py','python -B -m unittest discover -s tests -p link.py -v')
            with self.assertRaisesRegex(RuntimeError,'symlinked outside'):EXEC.pin_command(self.root,j,self.lookup)

if __name__=='__main__':unittest.main()
