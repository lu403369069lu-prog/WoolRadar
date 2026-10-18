"""Regression checks for durable replay, status authenticity and task rotation."""
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

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
                   "passed": 3, "failed": 0, "failed_test_names": []} for c in fam["checks"]]
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

    def run_persist(self, directory, q, receipt):
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
            "failed_test_names": []
        }
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
        self.assertTrue(worker.safe(["python", "-m", "unittest", "discover", "-s", "tests", "-p", "test_core.py"]))

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

    def test_unmapped_families_persist_as_unexecuted_not_accepted(self):
        """Changing a false formal mapping must never be mistaken for a pass."""
        q = self.queue()
        for index, family in enumerate(q["families"]):
            if family["checks"] or family["disposition"] == "EXTERNAL_OR_POLICY_GATED":
                continue
            with self.subTest(family=family["id"]):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    state = self.initial(q["repo"])
                    state["cursor"] = index
                    worker.save(root / "engine.json", state)
                    rec = self.receipt(q, cursor=index)
                    self.assertEqual(rec["results"][0]["status"],
                                     "NO_FORMAL_MAPPING_NOT_EXECUTED")
                    result = self.run_persist(root, q, rec)
                    self.assertEqual(result["families"][family["id"]]["status"],
                                     "NO_FORMAL_MAPPING_NOT_EXECUTED")
                    self.assertEqual(result["strict_business_completed"], 0)
                    self.assertIsNone(worker.choose_recheck(
                        {"revision": result["revision"], "families": {
                            family["id"]: {"status": "FORMAL_CHECK_FAILED_OR_BLOCKED"}}},
                        [family], set()))

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
