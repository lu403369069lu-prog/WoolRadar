"""Standalone offline regression contracts for the 50-family Codex handoff.

Run: python -B -m unittest coordination/test_historical_batch_contract_20261017.py -v
No repo clones, network, credentials, user files or scheduled writes are used.
"""
import importlib.util
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "historical_batch_under_test", HERE / "HISTORICAL_CODEX_BATCH_RUNNER_20261017.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class BatchSafetyContracts(unittest.TestCase):
    def test_python_two_pass_explicit_ok(self):
        rc, counts = module.evaluate_run("W-ALL", 0, "Ran 2 tests in 0.004s\n\nOK\n")
        self.assertEqual(rc, 0)
        self.assertEqual(counts, {"tests_reported": 2, "passed": 2, "failed": 0, "skipped": 0})

    def test_python_skips_are_not_passed(self):
        rc, counts = module.evaluate_run("W-DB", 0, "Ran 3 tests in 0.002s\n\nOK (skipped=1)\n")
        self.assertEqual(rc, 0)
        self.assertEqual((counts["passed"], counts["skipped"]), (2, 1))

    def test_python_failures_errors_not_counted_as_pass(self):
        rc, counts = module.evaluate_run("W-ALL", 1,
            "Ran 3 tests in 0.002s\n\nFAILED (failures=1, errors=1, skipped=1)\n")
        self.assertEqual(rc, 1)
        self.assertEqual((counts["passed"], counts["failed"], counts["skipped"]), (0, 2, 1))

    def test_python_zero_tests_false_green_rejected(self):
        rc, counts = module.evaluate_run("W-SNAPSHOT", 0, "Ran 0 tests in 0.000s\n\nOK\n")
        self.assertEqual(rc, 126)
        self.assertEqual(counts["tests_reported"], 0)

    def test_python_missing_final_ok_rejected(self):
        rc, _ = module.evaluate_run("W-ALL", 0, "Ran 22 tests in 1.000s\n")
        self.assertEqual(rc, 126)

    def test_node_summary_and_missing_summary(self):
        good = "# tests 4\n# suites 1\n# pass 3\n# fail 0\n# skipped 1\n"
        rc, counts = module.evaluate_run("S-ALL", 0, good)
        self.assertEqual(rc, 0)
        self.assertEqual((counts["passed"], counts["skipped"]), (3, 1))
        rc, _ = module.evaluate_run("S-TEACHER", 0, "No tests discovered\n")
        self.assertEqual(rc, 126)

    def test_node_failed_with_forged_zero_exit_rejected(self):
        rc, _ = module.evaluate_run("S-ROOTED", 0,
            "# tests 4\n# pass 3\n# fail 1\n# skipped 0\n")
        self.assertEqual(rc, 126)

    def test_build_is_a_compilation_not_a_test_suite(self):
        rc, counts = module.evaluate_run("S-BUILD", 0, "tsc -p tsconfig.json\n")
        self.assertEqual(rc, 0)
        self.assertIsNone(counts["tests_reported"])

    def test_nonzero_process_exit_never_downgraded(self):
        rc, _ = module.evaluate_run("W-ALL", 125, "Ran 1 test in 0.1s\nOK\n")
        self.assertEqual(rc, 125)

    def test_42_handoff_commands_have_matching_test_discovery_paths(self):
        table = (HERE / "HISTORICAL_80_PERCENT_CODEX_HANDOFF_20261017.md").read_text("utf-8")
        rows = [row for row in table.splitlines() if re.match(r"^\| (WR|SAM|COORD)-H\d+ \|", row)]
        self.assertEqual(len(rows), 50)
        executable = 0
        for row in rows:
            fields = [f.strip() for f in row.split("|")]
            if fields[5] != "CODEX_RUN":
                continue
            executable += 1
            path = re.search(r"\`([^\`]+)\`", fields[4])
            self.assertIsNotNone(path, row)
            source_path = path.group(1)
            command = fields[6]
            if "unittest discover" in command:
                folder = re.search(r"-s\s+(\S+)", command)
                pattern = re.search(r"-p\s+(\S+)", command)
                self.assertIsNotNone(folder, row)
                self.assertIsNotNone(pattern, row)
                self.assertEqual(folder.group(1), source_path.rsplit("/", 1)[0], row)
                self.assertEqual(pattern.group(1), source_path.rsplit("/", 1)[-1], row)
            elif "node --" in command and "test" in command:
                self.assertIn(source_path, command, row)
        self.assertEqual(executable, 42)


if __name__ == "__main__":
    unittest.main()
