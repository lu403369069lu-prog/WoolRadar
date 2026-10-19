"""Real local Git source-pin contracts; no network, provider, or production access."""
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "digest_preparer_for_clean_pin", ROOT / "scripts" / "prepare_digest_upstream.py"
)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class DigestCleanPinnedCheckoutTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="digest-git-pin-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.checkout = self.root / "nodes" / "digest-ai-agent" / "upstream"
        self.checkout.mkdir(parents=True)
        self.git("init", "-q")
        (self.checkout / "newsbrief" / "sources").mkdir(parents=True)
        self.source = self.checkout / "newsbrief" / "sources" / "rss.py"
        self.source.write_text("AUTHENTIC = True\n", encoding="utf-8")
        self.git("add", "newsbrief/sources/rss.py")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "-qm", "frozen source")
        self.pin = self.git("rev-parse", "HEAD")
        (self.root / "UPSTREAMS.json").write_text(json.dumps([{
            "node": "digest-ai-agent",
            "repository": "https://github.com/WHOOPsClaw/Digest_ai_agent",
            "commit": self.pin
        }]), encoding="utf-8")
        self.python = self.checkout / ".venv" / (
            "Scripts/python.exe" if os.name == "nt" else "bin/python")
        self.python.parent.mkdir(parents=True)
        self.python.touch()

    def git(self, *args):
        p = subprocess.run(["git", "-C", str(self.checkout), *args],
                           check=True, capture_output=True, text=True, encoding="utf-8")
        return p.stdout.strip()

    def prepare_with_fake_import(self, verify_only):
        real = mod.run
        calls = []
        def controlled(*args, env=None):
            calls.append(args)
            if args[0] == "git":
                return real(*args, env=env)
            if not verify_only and args[1:4] == ("-m", "pip", "install"):
                return ""
            if len(args) >= 2 and args[1] == "-c":
                # Windows TEMP may use DOS 8.3 aliases (RUNNER~1 vs runneradmin).
                self.assertTrue(Path(args[0]).samefile(self.python))
                return ""
            raise AssertionError(f"unexpected side effect: {args}")
        with patch.object(mod, "run", side_effect=controlled):
            return mod.prepare(self.root, verify_only=verify_only), calls

    def test_clean_pin_with_only_virtualenv_is_admitted(self):
        path, calls = self.prepare_with_fake_import(verify_only=True)
        self.assertTrue(path.samefile(self.python))
        self.assertTrue(any("status" in c for c in calls))

    def test_tracked_python_tamper_rejected_before_import(self):
        self.source.write_text("AUTHENTIC = False\n", encoding="utf-8")
        for verify_only in (True, False):
            with self.subTest(verify_only=verify_only):
                with self.assertRaisesRegex(RuntimeError, "UPSTREAM_WORKTREE_DIRTY"):
                    self.prepare_with_fake_import(verify_only)

    def test_untracked_importable_python_module_rejected(self):
        (self.checkout / "newsbrief" / "sources" / "hijack.py").write_text(
            "SHOULD_NOT_LOAD = True\n", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "UPSTREAM_WORKTREE_DIRTY"):
            self.prepare_with_fake_import(verify_only=True)

    def test_dirty_python_cannot_reach_pip(self):
        self.source.write_text("DIRTY = True\n", encoding="utf-8")
        real = mod.run
        calls = []
        def controlled(*args, env=None):
            calls.append(args)
            if args[0] == "git":
                return real(*args, env=env)
            raise AssertionError("Unexpected package install or import")
        with patch.object(mod, "run", side_effect=controlled):
            with self.assertRaisesRegex(RuntimeError, "UPSTREAM_WORKTREE_DIRTY"):
                mod.prepare(self.root, verify_only=False)
        self.assertFalse(any(c[0] != "git" for c in calls))


if __name__ == "__main__":
    unittest.main()
