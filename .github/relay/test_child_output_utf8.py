"""Offline regression: malformed child output must not certify relay tests.

Only subprocess.run is mocked; no source checkout, network, or production tests.
"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("relay_utf8_review", HERE / "worker.py")
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)


class ChildOutputByteIntegrityTests(unittest.TestCase):
    def exercise(self, stdout, stderr=b""):
        with tempfile.TemporaryDirectory(prefix="relay-byte-contract-") as temp:
            root = Path(temp)
            (root / "tests").mkdir()
            argv = ["python", "-m", "unittest", "discover", "-s", "tests",
                    "-p", "test_notifications.py"]
            done = SimpleNamespace(returncode=0, stdout=stdout, stderr=stderr)
            with patch.object(worker.subprocess, "run", return_value=done) as mocked:
                result = worker.test(argv, root, root)
            kwargs = mocked.call_args.kwargs
            self.assertNotIn("errors", kwargs)
            self.assertNotIn("text", kwargs)
            self.assertEqual(kwargs["env"]["PYTHONIOENCODING"], "utf-8")
            return result

    def test_invalid_stdout_with_success_trailer_is_blocked(self):
        result = self.exercise(b"\xff\nRan 1 test in 0.001s\n\nOK\n")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["error_kind"], "NON_UTF8_CHILD_OUTPUT")
        self.assertIsNone(result["passed"])

    def test_invalid_stderr_with_success_stdout_is_blocked(self):
        result = self.exercise(b"Ran 1 test in 0.001s\n\nOK\n", b"\xfe")
        self.assertEqual(result["status"], "BLOCKED")

    def test_clean_genuine_unittest_summary_still_passes(self):
        result = self.exercise(b"test_ok ... ok\n\nRan 1 test in 0.001s\n\nOK\n")
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["passed"], 1)

    def test_missing_summary_does_not_pass(self):
        result = self.exercise(b"done without test summary")
        self.assertNotEqual(result["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
