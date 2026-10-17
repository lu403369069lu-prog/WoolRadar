"""Ignored untracked Python import hooks must not invalidate frozen HEAD proof."""
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('untracked_check', HERE / 'HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


class UntrackedImportSafety(unittest.TestCase):
    def repo(self, base, ignore=False):
        root = Path(base)
        git(root, 'init', '-q')
        (root / 'test_frozen.py').write_text('import unittest\nclass A(unittest.TestCase):\n def test_yes(self): self.assertTrue(True)\n')
        if ignore:
            (root / '.gitignore').write_text('sitecustomize.py\n')
        git(root, 'add', '.')
        git(root, '-c', 'user.name=Isolated QA', '-c', 'user.email=qa@example.org', 'commit', '-qm', 'trusted')
        return root, git(root, 'rev-parse', 'HEAD')

    def test_clean_real_git_tree_passes(self):
        with tempfile.TemporaryDirectory() as d:
            root, head = self.repo(d)
            self.assertIsNone(runner._verify_frozen_worktree(root, head))

    def test_status_show_untracked_no_must_not_hide_importable_file(self):
        with tempfile.TemporaryDirectory() as d:
            root, head = self.repo(d)
            git(root, 'config', 'status.showUntrackedFiles', 'no')
            (root/'sitecustomize.py').write_text('raise RuntimeError("SYNTHETIC_IMPORT_SIDE_EFFECT")')
            self.assertEqual(git(root,'status','--porcelain'),'')
            with self.assertRaisesRegex(RuntimeError, 'Untracked|untracked|Unexpected'):
                runner._verify_frozen_worktree(root, head)

    def test_gitignore_hidden_python_site_hook_must_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root, head = self.repo(d, ignore=True)
            (root/'sitecustomize.py').write_text('raise RuntimeError("SYNTHETIC_IMPORT_SIDE_EFFECT")')
            self.assertEqual(git(root,'status','--porcelain','--untracked-files=all'),'')
            with self.assertRaisesRegex(RuntimeError, 'Untracked|untracked|Unexpected'):
                runner._verify_frozen_worktree(root, head)

if __name__ == '__main__': unittest.main()
