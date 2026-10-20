"""Offline recovery contracts for the pinned Digest upstream setup helper."""

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prepare_digest_upstream", PROJECT / "scripts" / "prepare_digest_upstream.py"
)
preparer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preparer)
PIN = "3d527f7f7e68e1b3e20df4e2f1e20a5b445f6fcb"


class DigestSetupRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=PROJECT / ".test-tmp")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "UPSTREAMS.json").write_text(json.dumps([{
            "node": "digest-ai-agent",
            "repository": "https://github.com/WHOOPsClaw/Digest_ai_agent",
            "commit": PIN,
        }]), encoding="utf-8")
        self.checkout = self.root / "nodes" / "digest-ai-agent" / "upstream"
        self.checkout.mkdir(parents=True)
        venv = self.checkout / ".venv"
        self.interpreter = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        self.interpreter.parent.mkdir(parents=True)
        self.interpreter.touch()

    def test_resume_existing_incomplete_checkout_at_exact_pin(self):
        """A clone interrupted before pinned checkout must resume safely."""
        state = {"head": "9" * 40}
        calls = []

        def fake_run(*cmd, env=None):
            calls.append(cmd)
            if "rev-parse" in cmd:
                return state["head"]
            if "checkout" in cmd:
                self.assertEqual(cmd[-2:], ("--detach", PIN))
                state["head"] = PIN
            return ""

        with patch.object(preparer, "run", side_effect=fake_run):
            self.assertEqual(preparer.prepare(self.root), self.interpreter)
        self.assertEqual(state["head"], PIN)
        self.assertEqual(sum("checkout" in c for c in calls), 1)
        self.assertFalse(any("clone" in c for c in calls))

    def test_verify_only_mismatched_checkout_never_mutates(self):
        calls = []

        def fake_run(*cmd, env=None):
            calls.append(cmd)
            return "9" * 40

        with patch.object(preparer, "run", side_effect=fake_run):
            with self.assertRaisesRegex(RuntimeError, "UPSTREAM_PIN_MISMATCH"):
                preparer.prepare(self.root, verify_only=True)
        self.assertEqual(len(calls), 1)
        self.assertIn("rev-parse", calls[0])


if __name__ == "__main__":
    unittest.main()
