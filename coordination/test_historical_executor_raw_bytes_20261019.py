"""Synthetic regressions: original child stdout bytes must remain unchanged.

Run offline: python -B -m unittest coordination/test_historical_executor_raw_bytes_20261019.py -v
No production checkout or real project tests are touched.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "historical_executor_raw_bytes", ROOT / "HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py"
)
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class RawBytesEvidenceTests(unittest.TestCase):
    def run_fixture(self, raw):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(runner.tempfile, "mkdtemp", return_value=temp), \
                 patch.object(runner.subprocess, "run", return_value=SimpleNamespace(
                     returncode=0, stdout=raw
                 )):
                cmd = {"key_sha256": "a" * 64, "command": "synthetic unit command",
                       "argv": ["not-executed"], "cwd": Path(temp)}
                rc, receipt, folder = runner.run_commands(
                    [cmd], [{"family_id": "WR-H01",
                             "source_blob": "test", "command_key": "a" * 64}],
                    "f" * 40, "wool")
                saved = (folder / ("a" * 16 + ".log")).read_bytes()
                self.assertEqual(saved, raw)
                self.assertEqual(receipt["results"][0]["log_sha256"],
                                 hashlib.sha256(raw).hexdigest())
                self.assertEqual(json.loads((folder / "receipt.json").read_text())["results"][0]["log_sha256"],
                                 hashlib.sha256(raw).hexdigest())
                return rc, receipt

    def test_invalid_utf8_with_forged_ok_trailer_is_not_pass(self):
        rc, receipt = self.run_fixture(
            b"\xff\xfe\nRan 1 test in 0.001s\n\nOK\n")
        self.assertEqual(rc, 1)
        self.assertNotEqual(receipt["results"][0]["status"], "PASS_EXACT_HEAD")

    def test_clean_utf8_valid_summary_passes(self):
        rc, receipt = self.run_fixture(
            b"test_x ... ok\n\n----------------------------------------------------------------------\n"
            b"Ran 1 test in 0.001s\n\nOK\n")
        self.assertEqual(rc, 0)
        self.assertEqual(receipt["results"][0]["status"], "PASS_EXACT_HEAD")

    def test_arbitrary_utf8_without_test_summary_is_not_pass(self):
        rc, receipt = self.run_fixture(b"Everything is great, trust me!\n")
        self.assertEqual(rc, 1)
        self.assertNotEqual(receipt["results"][0]["status"], "PASS_EXACT_HEAD")


if __name__ == "__main__":
    unittest.main()
