"""Git HEAD object alone cannot certify bytes actually executed in a dirty worktree."""
import hashlib
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location('real_disk_blob_under_test', HERE/'HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py')
runner = importlib.util.module_from_spec(sp)
sp.loader.exec_module(runner)


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.STDOUT, text=True).strip()


class WorktreePinnedContent(unittest.TestCase):
    def setup_repo(self, root):
        (root/'tests').mkdir()
        path = root/'tests/test_actual.py'
        path.write_text('import unittest\nclass A(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n')
        git(root,'init','-q')
        git(root,'add','tests/test_actual.py')
        git(root,'-c','user.name=Isolated-QA','-c','user.email=qa@example.org','commit','-qm','frozen fixture')
        sha=git(root,'rev-parse','HEAD:tests/test_actual.py')
        entry={'verified_test_path':'tests/test_actual.py','verified_test_blob':sha,
               'local_cwd':'.','run_command':'python -B -m unittest discover -s tests -p test_actual.py -v'}
        return path,entry,sha

    def test_exact_committed_bytes_allowed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            path,entry,sha=self.setup_repo(root)
            with patch.object(runner.contract, "git", side_effect=lambda args, cwd: git(cwd,*args), create=True):
                cwd,argv=runner.pin_command(root,entry)
            self.assertEqual(cwd,root.resolve())
            self.assertEqual(sha,git(root,'hash-object',str(path)))

    def test_dirty_test_file_denied_even_if_HEAD_blob_matches(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            path,entry,sha=self.setup_repo(root)
            path.write_text('import unittest\nclass A(unittest.TestCase):\n def test_false_green(self): self.assertTrue(True)\n')
            self.assertEqual(git(root,'rev-parse','HEAD:tests/test_actual.py'),sha)
            self.assertNotEqual(git(root,'hash-object',str(path)),sha)
            with patch.object(runner.contract, "git", side_effect=lambda args, cwd: git(cwd,*args), create=True):
                with self.assertRaisesRegex(RuntimeError,'working.tree|worktree|disk|contents'):
                    runner.pin_command(root,entry)

    def test_dirty_file_restored_to_exact_bytes_passes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            path,entry,sha=self.setup_repo(root)
            raw=path.read_bytes()
            path.write_text('changed')
            path.write_bytes(raw)
            with patch.object(runner.contract, "git", side_effect=lambda args, cwd: git(cwd,*args), create=True):
                cwd,argv=runner.pin_command(root,entry)
            self.assertEqual(cwd,root.resolve())

if __name__=='__main__':unittest.main()
