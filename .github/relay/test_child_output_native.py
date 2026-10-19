"""Native subprocess must not turn invalid child bytes into test evidence."""
from pathlib import Path
import tempfile
import unittest
from worker import test as run_test


class ActualChildByteIntegrity(unittest.TestCase):
    def test_real_unittest_invalid_byte_output_is_not_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            (root / "tests").mkdir()
            (root / "tests" / "test_notifications.py").write_text(
                "import os,unittest\n"
                "class Evidence(unittest.TestCase):\n"
                " def test_one(self): os.write(1,bytes([255])); self.assertTrue(True)\n",
                encoding="utf-8")
            argv = ["python", "-m", "unittest", "discover", "-s", "tests",
                    "-p", "test_notifications.py"]
            result = run_test(argv, root, root)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["error_kind"], "NON_UTF8_CHILD_OUTPUT")
            self.assertIsNone(result["passed"])
