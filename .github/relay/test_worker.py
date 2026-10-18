"""Regression checks for durable replay, status authenticity and task rotation."""
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("relay_worker_under_test", HERE / "worker.py")
worker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(worker)

class RelaySafetyTests(unittest.TestCase):
    def queue(self):
        return json.loads((HERE / "queue.json").read_text(encoding="utf-8"))

    def initial(self, name):
        return {"schema_version": 1, "repo": name, "cursor": 0,
                "revision": 0, "processed_run_keys": [], "families": {},
                "strict_business_completed": 0}

    def receipt(self, q, *, run_key="123456/1", cursor=0):
        fam = q["families"][cursor]
        checks = [{"argv": c, "status": "PASS", "exit_code": 0, "total": 3,
                   "passed": 3, "failed": 0, "skipped": 0, "todo": 0,
                   "cancelled": 0, "failed_test_names": []} for c in fam["checks"]]
        status = ("EXTERNAL_GATE_NOT_EXECUTED" if fam["disposition"] == "EXTERNAL_OR_POLICY_GATED"
                  else "FORMAL_SUBSET_PASS_NATIVE_PENDING" if checks else "NO_FORMAL_MAPPING_NOT_EXECUTED")
        return {
            "schema_version": 1, "repo": q["repo"], "run_key": run_key,
            "source_commit": "a" * 40, "source_ref": q["source_ref"],
            "queue_sha256": worker.queue_digest(q),
            "previous_cursor": cursor, "next_cursor": (cursor + 1) % len(q["families"]),
            "strict_new_acceptances": 0, "generated_utc": "2026-10-18T00:00:00Z",
            "results": [{"id": fam["id"], "goal": fam["goal"], "status": status,
                         "checks": checks, "strictly_complete": False,
                         "business_accepted": False}]
        }

    def run_persist(self, directory, q, receipt, integration_sha="a" * 40, integration_mutator=None):
        state = directory / "engine.json"
        if not state.exists():
            worker.save(state, self.initial(q["repo"]))
        rec = directory / "receipt.json"
        integration = {
            "schema_version": 1, "repo": q["repo"],
            "command": (["/usr/bin/python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
                        if q["repo"] == "WoolRadar" else ["npm", "test"]),
            "source_subdir": "." if q["repo"] == "WoolRadar" else "SAM/snapshot",
            "verified_business_complete": False, "checked_utc": "2026-10-18T00:00:00Z",
            "status": "PASS", "exit_code": 0, "total": 5, "passed": 5, "failed": 0,
            "skipped": 0, "todo": 0, "cancelled": 0, "failed_test_names": []
        }
        if integration_sha is not None:
            integration["source_commit"] = integration_sha
        integration["run_key"] = receipt["run_key"]
        if integration_mutator is not None:
            integration_mutator(integration)
        worker.save(directory / "integration.json", integration)
        worker.save(rec, receipt)
        worker.persist(SimpleNamespace(state=str(directory), receipt=str(rec), repo=q["repo"]))
        return worker.load(state)

    def test_skip_todo_cancelled_never_count_as_formal_pass(self):
        cases = [
            ("Node all skipped", "# tests 2\n# pass 0\n# fail 0\n# cancelled 0\n# skipped 2\n# todo 0\n"),
            ("Node mixed skip", "# tests 2\n# pass 1\n# fail 0\n# cancelled 0\n# skipped 1\n# todo 0\n"),
            ("Node todo", "# tests 2\n# pass 1\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 1\n"),
            ("Node cancelled", "# tests 2\n# pass 1\n# fail 0\n# cancelled 1\n# skipped 0\n# todo 0\n"),
            ("Node missing summary", "# tests 2\n# pass 2\n# fail 0\n"),
            ("Python all skipped", "Ran 2 tests in 0.001s\n\nOK (skipped=2)\n"),
        ]
        for label, output in cases:
            with self.subTest(label=label):
                self.assertEqual(worker.parse_test_summary(output, 0)["status"], "FAIL")
        node_good = "# tests 2\n# pass 2\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n"
        self.assertEqual(worker.parse_test_summary(node_good, 0)["status"], "PASS")
        self.assertEqual(worker.parse_test_summary("Ran 2 tests in 0.001s\n\nOK\n", 0)["status"], "PASS")

    def test_real_python_expected_failure_cannot_pass_formal_gate(self):
        # Exercise a real unittest process: expected failures intentionally exit 0.
        # A relay must not upgrade that result into formal acceptance.
        source = (
            "import unittest\n"
            "class Probe(unittest.TestCase):\n"
            "    @unittest.expectedFailure\n"
            "    def test_known_bug(self):\n"
            "        self.assertEqual(1, 2)\n"
            "unittest.main()\n"
        )
        proc = subprocess.run(
            [sys.executable, "-c", source], text=True, capture_output=True,
            timeout=20, check=False)
        output = proc.stdout + "\n" + proc.stderr
        self.assertEqual(proc.returncode, 0)
        self.assertIn("expected failures=1", output)
        self.assertEqual(worker.parse_test_summary(output, proc.returncode)["status"], "FAIL")

    def test_python_summary_missing_ok_never_passes(self):
        self.assertEqual(
            worker.parse_test_summary("Ran 1 test in 0.001s\n", 0)["status"], "FAIL")

    def test_real_integration_report_producer_binds_checked_out_git_sha(self):
        # Execute the original producer using the real checkout Git identity,
        # but substitute the external full test process with a synthetic TAP
        # receipt. This never runs SAM production or fetches real sources.
        from unittest.mock import patch
        source_root = HERE.parent.parent
        spec = importlib.util.spec_from_file_location(
            "relay_integration_under_test", HERE / "integration_gate.py")
        integration_gate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(integration_gate)
        expected = worker.source_sha(source_root)
        q = self.queue()
        sample_output = (
            "Ran 1 test in 0.001s\n\nOK\n" if q["repo"] == "WoolRadar"
            else "# tests 1\n# pass 1\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n"
        )
        stub = SimpleNamespace(stdout=sample_output, stderr="", returncode=0)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "synthetic-integration.json"
            with patch.object(
                integration_gate, "subprocess",
                SimpleNamespace(run=lambda *args, **kwargs: stub)
            ):
                integration_gate.run(SimpleNamespace(
                    source=str(source_root), repo=q["repo"], output=str(target)))
            actual = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(actual["source_commit"], expected)
            self.assertEqual(actual["run_key"], __import__("os").environ.get("GITHUB_RUN_ID", "0") + "/" + __import__("os").environ.get("GITHUB_RUN_ATTEMPT", "1"))
            self.assertEqual(actual["status"], "PASS")
            self.assertIs(actual["verified_business_complete"], False)

    def test_full_integration_receipt_must_bind_exact_actions_run_attempt(self):
        q = self.queue()
        for fake in (None, "999999/1", "incorrect-run-id", True):
            with self.subTest(integration_run_key=fake), tempfile.TemporaryDirectory() as tmp:
                receipt = self.receipt(q)
                def corrupt(row):
                    if fake is None:
                        row.pop("run_key", None)
                    else:
                        row["run_key"] = fake
                with self.assertRaises(ValueError):
                    self.run_persist(
                        Path(tmp), q, receipt, integration_mutator=corrupt)

    def test_full_suite_pass_requires_exact_explicit_typed_counters(self):
        q = self.queue()
        for field in ("failed", "skipped", "todo", "cancelled"):
            with self.subTest(omitted=field), tempfile.TemporaryDirectory() as tmp:
                receipt = self.receipt(q)
                with self.assertRaises(ValueError):
                    self.run_persist(
                        Path(tmp), q, receipt,
                        integration_mutator=lambda row, key=field: row.pop(key, None))
            with self.subTest(boolean=field), tempfile.TemporaryDirectory() as tmp:
                receipt = self.receipt(q)
                with self.assertRaises(ValueError):
                    self.run_persist(
                        Path(tmp), q, receipt,
                        integration_mutator=lambda row, key=field: row.__setitem__(key, False))
        with self.subTest(boolean_total=True), tempfile.TemporaryDirectory() as tmp:
            receipt = self.receipt(q)
            def boolean_total(row):
                row["total"] = True
                row["passed"] = 1
            with self.assertRaises(ValueError):
                self.run_persist(Path(tmp), q, receipt, integration_mutator=boolean_total)
        with self.subTest(boolean_exit=True), tempfile.TemporaryDirectory() as tmp:
            receipt = self.receipt(q)
            with self.assertRaises(ValueError):
                self.run_persist(
                    Path(tmp), q, receipt,
                    integration_mutator=lambda row: row.__setitem__("exit_code", False))

    def test_integration_report_must_match_exact_tested_source_commit(self):
        q = self.queue()
        for source_sha in (None, "b" * 40, "invalid", True):
            with self.subTest(reported_sha=source_sha), tempfile.TemporaryDirectory() as tmp:
                receipt = self.receipt(q)
                with self.assertRaises(ValueError):
                    self.run_persist(Path(tmp), q, receipt, integration_sha=source_sha)

    def test_forged_pass_receipt_requires_explicit_zero_counters(self):
        q = self.queue()
        for field in ("failed", "skipped", "todo", "cancelled"):
            with self.subTest(missing=field), tempfile.TemporaryDirectory() as tmp:
                receipt = self.receipt(q)
                checks = receipt["results"][0]["checks"]
                self.assertTrue(checks, "requires a real mapped family")
                checks[0].pop(field, None)
                with self.assertRaises(ValueError):
                    self.run_persist(Path(tmp), q, receipt)
        for field in ("failed", "skipped", "todo", "cancelled"):
            with self.subTest(boolean=field), tempfile.TemporaryDirectory() as tmp:
                receipt = self.receipt(q)
                receipt["results"][0]["checks"][0][field] = False
                with self.assertRaises(ValueError):
                    self.run_persist(Path(tmp), q, receipt)

    def test_forged_skipped_receipt_rejected(self):
        q = self.queue()
        with tempfile.TemporaryDirectory() as tmp:
            receipt = self.receipt(q)
            receipt["results"][0]["checks"][0].update({"skipped": 3, "passed": 0})
            with self.assertRaises(ValueError):
                self.run_persist(Path(tmp), q, receipt)

    def test_queue_digest_is_lf_crlf_platform_stable(self):
        q = self.queue()
        lf = json.dumps(q, sort_keys=True, indent=2, ensure_ascii=False)
        crlf = lf.replace("\n", "\r\n")
        self.assertNotEqual(lf, crlf)
        self.assertEqual(worker.queue_digest(json.loads(lf)), worker.queue_digest(json.loads(crlf)))

    def test_command_allowlist_denies_shell_and_arbitrary_code(self):
        self.assertFalse(worker.safe(["bash", "-c", "rm -rf /"]))
        self.assertFalse(worker.safe(["node", "-e", "process.exit(0)"]))
        self.assertFalse(worker.safe(["python", "-c", "print(1)"]))
        self.assertFalse(worker.safe(["node", "--test", "/tmp/x.test.mjs"]))
        self.assertTrue(worker.safe(["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_notifications.py"]))

    def test_wool_runner_rejects_unreviewed_node_test_paths(self):
        q = self.queue()
        self.assertFalse(any(c[:2] == ["node", "--test"]
                             for f in q["families"] for c in f["checks"]))
        for name in ("../unreviewed.test.mjs", "../../escape.test.mjs",
                     "tools/unreviewed.test.mjs", "tools/../escape.test.mjs",
                     "C:\\private\\evil.test.mjs"):
            with self.subTest(path=name):
                self.assertFalse(worker.safe(["node", "--test", name]))

    def test_python_discovery_source_allowlist_blocks_unreviewed_roots(self):
        q = self.queue()
        valid = [c for f in q["families"] for c in f["checks"]
                 if c[:5] == ["python", "-m", "unittest", "discover", "-s"]]
        self.assertTrue(valid)
        self.assertTrue(all(worker.safe(c) for c in valid))
        for path, pattern in [
            ("../../unreviewed", "test_*.py"),
            ("../tests", "test_notifications.py"),
            ("tests/../secrets", "test_notifications.py"),
            ("tests", "test_unreviewed.py"),
            ("independent-quality/../tests", "test_*.py"),
            ("C:\\private", "test_*.py"),
        ]:
            with self.subTest(path=path, pattern=pattern):
                self.assertFalse(worker.safe([
                    "python", "-m", "unittest", "discover", "-s", path,
                    "-p", pattern]))

    def test_boolean_exit_code_cannot_pass_formal_subset(self):
        q = self.queue()
        eligible = next((i for i, fam in enumerate(q["families"])
                         if fam["checks"] and fam["disposition"] != "EXTERNAL_OR_POLICY_GATED"), None)
        self.assertIsNotNone(eligible)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            state = self.initial(q["repo"])
            state["cursor"] = eligible
            worker.save(root / "engine.json", state)
            receipt = self.receipt(q, cursor=eligible)
            receipt["results"][0]["checks"][0]["exit_code"] = False
            with self.assertRaises(ValueError):
                self.run_persist(root, q, receipt)
            self.assertEqual(worker.load(root / "engine.json")["revision"], 0)
            self.assertFalse((root / "history.jsonl").exists())
            receipt["results"][0]["checks"][0]["exit_code"] = 0
            final = self.run_persist(root, q, receipt)
            self.assertEqual(final["revision"], 1)

    def test_durable_persist_and_duplicate_replay(self):
        q = self.queue()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            receipt = self.receipt(q)
            first = self.run_persist(root, q, receipt)
            self.assertEqual(first["revision"], 1)
            self.assertEqual(first["cursor"], 1)
            self.assertEqual(first["strict_business_completed"], 0)
            again = self.run_persist(root, q, receipt)
            self.assertEqual(again["revision"], 1)
            self.assertEqual(len((root / "history.jsonl").read_text(encoding="utf-8").splitlines()), 1)

    def test_reject_forged_completion_and_stale_cursor(self):
        q = self.queue()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            r = self.receipt(q)
            r["results"][0]["strictly_complete"] = True
            with self.assertRaises(ValueError):
                self.run_persist(root, q, r)
            r["results"][0]["strictly_complete"] = False
            r["results"][0]["status"] = "BUSINESS_COMPLETE"
            with self.assertRaises(ValueError):
                self.run_persist(root, q, r)
            r = self.receipt(q)
            r["next_cursor"] = 5
            with self.assertRaises(ValueError):
                self.run_persist(root, q, r)
            r = self.receipt(q)
            r["queue_sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                self.run_persist(root, q, r)

    def test_failed_subset_is_prioritized_with_revision_cooldown(self):
        q = self.queue()
        state = self.initial(q["repo"])
        # A queue mapping may deliberately become empty (fail closed).
        # Pick an actually runnable family; do not rely on fixed slot 2.
        eligible = [f for f in q["families"][1:]
                    if f["checks"] and f["disposition"] != "EXTERNAL_OR_POLICY_GATED"]
        self.assertTrue(eligible, "queue has no eligible priority recheck")
        family_id = eligible[0]["id"]
        state["families"][family_id] = {"status": "FORMAL_CHECK_FAILED_OR_BLOCKED"}
        picked = worker.choose_recheck(state, q["families"], {q["families"][0]["id"]})
        self.assertEqual(picked["id"], family_id)
        state["families"][family_id]["last_recheck_revision"] = 0
        state["revision"] = 1
        self.assertIsNone(worker.choose_recheck(state, q["families"], {q["families"][0]["id"]}))
        state["revision"] = 2
        self.assertEqual(worker.choose_recheck(state, q["families"], set())["id"], family_id)

    def test_unrelated_source_tests_do_not_claim_family_formal_pass(self):
        """An unrelated passing test must never masquerade as family evidence."""
        q = self.queue()
        excluded = {
            "WR-H03": "test_config_backup.py",  # Not WAL/CLAIMED recovery.
            "COORD-H01": "test_orchestrator.py",  # Not dispatcher replay.
            "COORD-H02": "test_node_entry.py",  # Not GitHub event adaptation.
            "COORD-H06": "test_reindex_preview.py",  # Not Git return-sync.
            "WR-H18": "test_notifications.py",  # Not SENT-CAS uncertainty.
        }
        for family_id, unrelated_pattern in excluded.items():
            with self.subTest(family_id=family_id):
                family = next(f for f in q["families"] if f["id"] == family_id)
                self.assertNotIn(unrelated_pattern, repr(family["checks"]))

    def test_rotation_two_consecutive_receipts(self):
        q = self.queue()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = self.run_persist(root, q, self.receipt(q))
            self.assertEqual(first["cursor"], 1)
            second = self.run_persist(root, q, self.receipt(q, run_key="123457/1", cursor=1))
            self.assertEqual(second["cursor"], 2)
            self.assertEqual(second["revision"], 2)
            self.assertEqual(len(second["processed_run_keys"]), 2)

if __name__ == "__main__":
    unittest.main()
