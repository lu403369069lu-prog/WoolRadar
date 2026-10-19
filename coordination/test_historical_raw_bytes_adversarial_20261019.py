"""Offline synthetic tests for raw byte integrity in batch and job executors.

This test module does not inspect user files or run production tasks.
"""
import importlib.util
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

DIR = Path(__file__).resolve().parent
def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, DIR / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

batch = load("historical_batch_byte_review", "HISTORICAL_CODEX_BATCH_RUNNER_20261017.py")
job = load("historical_job_byte_review", "HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py")


class RawBytesAdversarialTests(unittest.TestCase):
    def check_job(self, raw, expect_success):
        with tempfile.TemporaryDirectory() as tmp:
            command = {"key_sha256": "a" * 64, "command": "fixture only",
                       "argv": ["not-called"], "cwd": Path(tmp)}
            mapping = [{"family_id": "WR-H01", "source_blob": "fixed",
                        "command_key": "a" * 64}]
            with patch.object(job.tempfile, "mkdtemp", return_value=tmp), \
                 patch.object(job.subprocess, "run", return_value=SimpleNamespace(
                     returncode=0, stdout=raw)):
                rc, receipt, folder = job.run_commands(
                    [command], mapping, "a" * 40, "wool")
            self.assertEqual((folder / ("a" * 16 + ".log")).read_bytes(), raw)
            self.assertEqual(receipt["results"][0]["log_sha256"],
                             hashlib.sha256(raw).hexdigest())
            self.assertEqual(rc == 0, expect_success)

    def test_one_hundred_byte_mutations_do_not_forge_success(self):
        # 100 distinct one-byte non-UTF8 mutations in a genuine-looking summary.
        valid = b"Ran 1 test in 0.001s\n\nOK\n"
        for i in range(100):
            raw = bytes((0x80 + (i % 64),)) + b"X" * (i // 64) + valid
            with self.subTest(mutation=i):
                self.check_job(raw, False)

    def test_batch_quiet_build_is_allowed(self):
        rc, counts = batch.evaluate_run("S-BUILD", 0, "")
        self.assertEqual(rc, 0)

    def test_batch_test_with_no_summary_is_denied(self):
        rc, counts = batch.evaluate_run("W-ALL", 0, "")
        self.assertNotEqual(rc, 0)

    def test_valid_utf8_summary_is_accepted_by_job(self):
        self.check_job(b"Ran 1 test in 0.001s\n\nOK\n", True)


if __name__ == "__main__":
    unittest.main()
