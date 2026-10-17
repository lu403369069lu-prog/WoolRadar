"""Stdlib-only synthetic acceptance and adversarial tests for 42-target receipts."""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


SOURCE = Path(__file__).with_name("HISTORICAL_CODEX_42_RECEIPT_GUARD_20261017.py")
spec = importlib.util.spec_from_file_location("historical_receipt_guard_42", SOURCE)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

SAMPLE_LOG = b"synthetic stdout, no private data\n"
GOOD_HASH = hashlib.sha256(SAMPLE_LOG).hexdigest()
COMMAND = "python -B -m unittest discover -s tests -p test_notifications.py -v"
ARGS = ["python", "-B", "-m", "unittest", "discover", "-s", "tests",
        "-p", "test_notifications.py", "-v"]
FAMILIES = ["WR-H01", "WR-H04"]


def manifest():
    return {"jobs": [{"project": "WoolRadar", "disposition": "READY_FOR_LOCAL_CODEX",
                      "family_id": family, "local_cwd": ".", "run_command": COMMAND}
                     for family in FAMILIES]}


def receipt():
    return {
        "schema_version": 1,
        "source": "disposable-local-codex",
        "project": "wool",
        "repo_sha": guard.HEADS["wool"],
        "runtime": {"python": "3.12.14", "platform": "Windows-11"},
        "no_real_gold_claim": True,
        "production_modified": False,
        "tested_families": 2,
        "unique_commands": 1,
        "results": [{
            "family_ids": list(FAMILIES), "cwd": ".", "argv": list(ARGS),
            "exit_code": 0, "status": "PASS",
            "counts": {"tests": 3, "passed": 3, "failed": 0, "skipped": 0},
            "sha256": GOOD_HASH, "local_log": "test-001.log"
        }]
    }


def checked(data, write_log=True):
    with tempfile.TemporaryDirectory(prefix="history-receipt-42-test-") as tmp:
        if write_log:
            (Path(tmp) / "test-001.log").write_bytes(SAMPLE_LOG)
        return guard.review(data, manifest(), Path(tmp))


class ReviewTruth(unittest.TestCase):
    def test_valid_synthetic_dedup_group(self):
        r = checked(receipt())
        self.assertTrue(r["local_full_family_receipt_accepted"], r["errors"])
        self.assertEqual(r["families_expected"], 2)
        self.assertEqual(r["unique_commands_expected"], 1)

    def test_no_result_can_approve_business_gold(self):
        r = checked(receipt())
        self.assertFalse(r["business_gold_accepted"])
        self.assertFalse(r["historical_recovery_closed"])
        self.assertFalse(r["windows_node24_and_26_both_verified"])

    def test_missing_family_is_not_complete(self):
        d = receipt()
        d["results"][0]["family_ids"] = ["WR-H01"]
        self.assertIn("INCOMPLETE_FAMILY_COVERAGE", checked(d)["errors"])

    def test_fake_family_same_command_rejected(self):
        d = receipt()
        d["results"][0]["family_ids"].append("WR-H77")
        self.assertIn("FAMILY_COMMAND_MISMATCH", checked(d)["errors"])

    def test_duplicate_family_rejected(self):
        d = receipt()
        d["results"][0]["family_ids"].append("WR-H01")
        self.assertIn("MALFORMED_FAMILIES", checked(d)["errors"])

    def test_skip_must_not_pass(self):
        d = receipt()
        d["results"][0]["counts"] = {"tests": 3, "passed": 2, "failed": 0, "skipped": 1}
        self.assertIn("NO_COMPLETE_GREEN_TESTS", checked(d)["errors"])

    def test_inconsistent_count_must_fail(self):
        d = receipt()
        d["results"][0]["counts"]["passed"] = 1
        self.assertIn("INCONSISTENT_COUNTS", checked(d)["errors"])

    def test_no_tests_must_fail(self):
        d = receipt()
        d["results"][0]["counts"] = {"tests": 0, "passed": 0, "failed": 0, "skipped": 0}
        self.assertIn("NO_COMPLETE_GREEN_TESTS", checked(d)["errors"])

    def test_nonzero_exit(self):
        d = receipt()
        d["results"][0]["exit_code"] = 1
        self.assertIn("NONZERO_EXIT", checked(d)["errors"])

    def test_missing_raw_log(self):
        self.assertIn("MISSING_RAW_LOG", checked(receipt(), False)["errors"])

    def test_digest_cannot_be_modified(self):
        d = receipt()
        d["results"][0]["sha256"] = "a" * 64
        self.assertIn("LOG_SHA256_MISMATCH", checked(d)["errors"])

    def test_log_name_cannot_escape(self):
        d = receipt()
        d["results"][0]["local_log"] = "../secret.txt"
        self.assertIn("UNSAFE_LOG_FILENAME", checked(d)["errors"])

    def test_unauthorized_command_rejected(self):
        d = receipt()
        d["results"][0]["argv"] = ["python", "-c", "print(123)"]
        self.assertIn("INVALID_COMMAND", checked(d)["errors"])

    def test_different_allowlisted_test_is_not_the_expected_test(self):
        d = receipt()
        d["results"][0]["argv"][-2] = "test_rogue.py"
        self.assertIn("UNEXPECTED_COMMAND", checked(d)["errors"])

    def test_wrong_git_sha(self):
        d = receipt()
        d["repo_sha"] = "0" * 40
        self.assertIn("HEAD_MISMATCH", checked(d)["errors"])

    def test_missing_runtime(self):
        d = receipt()
        d["runtime"] = {}
        self.assertIn("MISSING_RUNTIME", checked(d)["errors"])

    def test_fake_business_approval(self):
        d = receipt()
        d["no_real_gold_claim"] = False
        self.assertIn("UNSAFE_REAL_GOLD_CLAIM", checked(d)["errors"])

    def test_tampered_manifest_fails_before_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "manifest.json"
            p.write_text('{"jobs":[],"total_families":50}')
            with self.assertRaisesRegex(ValueError, "WRONG_IMMUTABLE_MANIFEST_BLOB"):
                guard.load_verified_manifest(p)


if __name__ == "__main__":
    unittest.main()
