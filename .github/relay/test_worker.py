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
            "queue_sha256": hashlib.sha256((HERE / "queue.json").read_bytes()).hexdigest(),
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
        family_id = q["families"][2]["id"]
        state["families"][family_id] = {"status": "FORMAL_CHECK_FAILED_OR_BLOCKED"}
        picked = worker.choose_recheck(state, q["families"], {q["families"][0]["id"]})
        self.assertEqual(picked["id"], family_id)
        state["families"][family_id]["last_recheck_revision"] = 0
        state["revision"] = 1
        self.assertIsNone(worker.choose_recheck(state, q["families"], {q["families"][0]["id"]}))
        state["revision"] = 2
        self.assertEqual(worker.choose_recheck(state, q["families"], set())["id"], family_id)

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
