"""Unit regressions for the exact-blob, offline, 42-target Codex handoff runner.

These controls are intentionally runnable with only Python stdlib. They never
launch a real project test, modify a GitHub branch or touch production data.
"""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "HISTORICAL_CODEX_42_TARGET_RUNNER_20261017.py"
spec = importlib.util.spec_from_file_location("historical_42_runner", SOURCE)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class ReceiptTruthTests(unittest.TestCase):
    def test_node_aggregate(self):
        c = runner.counts("# tests 14\n# pass 14\n# fail 0\n# cancelled 0\n# skipped 0\n")
        self.assertEqual(c, {"tests": 14, "passed": 14, "failed": 0, "skipped": 0})
        self.assertEqual(runner.verdict(0, c), "PASS")

    def test_python_aggregate(self):
        c = runner.counts("Ran 10 tests in 0.010s\n\nOK\n")
        self.assertEqual(c["passed"], 10)
        self.assertEqual(runner.verdict(0, c), "PASS")

    def test_zero_test_exit_zero_must_not_pass(self):
        self.assertEqual(runner.verdict(0, runner.counts("Ran 0 tests in 0.000s\n\nOK\n")),
                         "BLOCKED_ZERO_OR_UNKNOWN_TESTS")

    def test_unparsable_exit_zero_must_not_pass(self):
        self.assertEqual(runner.verdict(0, runner.counts("finished successfully\n")),
                         "BLOCKED_ZERO_OR_UNKNOWN_TESTS")

    def test_all_skipped_must_not_pass(self):
        c = runner.counts("# tests 2\n# pass 0\n# fail 0\n# skipped 2\n")
        self.assertEqual(runner.verdict(0, c), "BLOCKED_ALL_SKIPPED_OR_UNKNOWN_PASS")

    def test_some_skipped_must_not_pass(self):
        c = runner.counts("# tests 2\n# pass 1\n# fail 0\n# skipped 1\n")
        self.assertEqual(runner.verdict(0, c), "PARTIAL_SKIPPED_NOT_ACCEPTED")

    def test_report_count_inconsistency(self):
        c = runner.counts("# tests 10\n# pass 8\n# fail 0\n# skipped 0\n")
        self.assertEqual(runner.verdict(0, c), "BLOCKED_COUNT_INCONSISTENCY")

    def test_failed_subtests_cannot_override_exit_failure(self):
        c = runner.counts("Ran 4 tests in 0.2s\nFAILED (failures=1, errors=1)\n")
        self.assertEqual(c["passed"], 2)
        self.assertEqual(runner.verdict(1, c), "TEST_FAILED")

    def test_python_skip_is_partial(self):
        c = runner.counts("Ran 3 tests in 0.010s\n\nOK (skipped=1)\n")
        self.assertEqual(c, {"tests": 3, "passed": 2, "failed": 0, "skipped": 1})
        self.assertEqual(runner.verdict(0, c), "PARTIAL_SKIPPED_NOT_ACCEPTED")

    def test_malformed_node_aggregate_fails_closed(self):
        c = runner.counts("# tests 4\n# pass 4\n# fail 0\n")
        self.assertEqual(runner.verdict(0, c), "PARTIAL_SKIPPED_NOT_ACCEPTED")

    def test_correct_wool_delivery_bridge_target(self):
        job = {"family_id": "WR-H15",
               "run_command": "python -B -m unittest discover -s independent-quality/delivery-bridge-20261016 -p test_delivery_boundaries.py -v",
               "verified_test_path": "independent-quality/delivery-bridge-20261016/test_delivery_boundaries.py",
               "local_cwd": "."}
        with tempfile.TemporaryDirectory() as directory:
            cwd, cmd = runner.validate_command(job, Path(directory).resolve())
        self.assertEqual(cwd, ".")
        self.assertEqual(cmd[1:], ["-B", "-m", "unittest", "discover",
                                   "-s", "independent-quality/delivery-bridge-20261016",
                                   "-p", "test_delivery_boundaries.py", "-v"])

    def test_wrong_historical_wool_path_must_be_rejected(self):
        job = {"family_id": "WR-H15",
               "run_command": "python -B -m unittest discover -s independent-quality/public-corpus-blind-dedup-20261016 -p test_delivery_boundaries.py -v",
               "verified_test_path": "independent-quality/delivery-bridge-20261016/test_delivery_boundaries.py",
               "local_cwd": "."}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(runner.Blocked, "command targets"):
                runner.validate_command(job, Path(directory).resolve())

    def test_arbitrary_shell_is_not_allowlisted(self):
        job = {"family_id": "WR-H01", "run_command": "curl https://example.org",
               "verified_test_path": "tests/test_notifications.py", "local_cwd": "."}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(runner.Blocked):
                runner.validate_command(job, Path(directory).resolve())

    def test_short_python_argv_does_not_index_crash(self):
        job = {"family_id": "WR-H01", "run_command": "python",
               "verified_test_path": "tests/test_notifications.py", "local_cwd": "."}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(runner.Blocked):
                runner.validate_command(job, Path(directory).resolve())

    def test_node_relative_source_path_resolves_to_reviewed_blob(self):
        job = {"family_id": "SAM-H05",
               "run_command": "node --import tsx --test ../independent-review/20261016/rooted-source-authorization.test.ts",
               "verified_test_path": "SAM/independent-review/20261016/rooted-source-authorization.test.ts",
               "local_cwd": "SAM/snapshot"}
        with tempfile.TemporaryDirectory() as directory:
            cwd, argv = runner.validate_command(job, Path(directory).resolve())
        self.assertEqual(cwd, "SAM/snapshot")
        self.assertEqual(argv[:4], ["node", "--import", "tsx", "--test"])

    def test_node_proof_path_mismatch_rejected(self):
        job = {"family_id": "SAM-H05",
               "run_command": "node --import tsx --test ../independent-review/20261016/rooted-source-authorization.test.ts",
               "verified_test_path": "SAM/snapshot/test/rooted-source-authorization.test.ts",
               "local_cwd": "SAM/snapshot"}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(runner.Blocked, "Node command/test path mismatch"):
                runner.validate_command(job, Path(directory).resolve())

    def test_globbed_unittest_pattern_cannot_satisfy_single_family_proof(self):
        job = {"family_id": "WR-H01",
               "run_command": "python -B -m unittest discover -s tests -p test_*.py -v",
               "verified_test_path": "tests/test_notifications.py", "local_cwd": "."}
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(runner.Blocked, "unsafe test pattern"):
                runner.validate_command(job, Path(directory).resolve())

    def test_bad_manifest_bytes_rejected_before_execution(self):
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "tampered.json"
            src.write_text('{"total_families":50,"ready_for_local_codex":42,"jobs":[]}')
            with self.assertRaisesRegex(runner.Blocked, "Manifest byte SHA"):
                runner.load_and_validate(src, "wool", Path(directory).resolve())

    @unittest.skipUnless(os.name == "nt", "Windows root semantics only")
    def test_production_root_denied_before_any_git_call(self):
        with self.assertRaisesRegex(runner.Blocked, "Potential production"):
            runner.safe_checkout(Path(r"C:\WoolRadar"), "0" * 40, "wool")

    def test_path_traversal_denied(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(runner.Blocked):
                runner.in_repo(Path(directory).resolve(), "../outside.txt")


if __name__ == "__main__":
    unittest.main()
