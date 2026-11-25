"""Run a WoolRadar relay over disposable, synthetic tests."""

import importlib.util
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace


def initialize_source(source):
    tests = source / "tests"
    tests.mkdir(parents=True)
    (tests / "test_notifications.py").write_text(
        "import unittest\n\n"
        "class NotificationFixture(unittest.TestCase):\n"
        "    def test_example(self):\n"
        "        self.assertEqual(len({'demo-notification'}), 1)\n",
        encoding="utf-8",
    )
    (tests / "test_reindex_snapshot.py").write_text(
        "import unittest\n\n"
        "class SnapshotFixture(unittest.TestCase):\n"
        "    @unittest.skip('deliberately unavailable demo fixture')\n"
        "    def test_example(self):\n"
        "        pass\n",
        encoding="utf-8",
    )
    for command in (
        ("init", "--quiet", "--template="),
        ("add", "tests"),
        ("-c", "user.name=Demo", "-c", "user.email=demo@example.invalid",
         "commit", "--quiet", "--no-gpg-sign", "-m", "Synthetic demo inputs"),
    ):
        subprocess.run(["git", *command], cwd=source, check=True, capture_output=True)


def main():
    relay = Path(__file__).resolve().parents[1] / ".github" / "relay" / "worker.py"
    spec = importlib.util.spec_from_file_location("woolradar_relay", relay)
    worker = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(worker)
    base_cmd = ["python", "-m", "unittest", "discover", "-s", "tests", "-p"]
    repo = "WoolRadar"
    queue = {
        "schema_version": 1, "repo": repo, "source_ref": "demo", "source_subdir": ".",
        "families": [
            {"id": "WR-H01", "goal": "A runnable test", "disposition": "FORMAL",
             "checks": [base_cmd + ["test_notifications.py"]]},
            {"id": "WR-H02", "goal": "A skipped test with exit code zero", "disposition": "FORMAL",
             "checks": [base_cmd + ["test_reindex_snapshot.py"]]},
            {"id": "WR-H03", "goal": "Next queue item", "disposition": "EXTERNAL_OR_POLICY_GATED",
             "checks": []},
        ],
    }

    with TemporaryDirectory(prefix="woolradar-relay-demo-") as temp:
        root = Path(temp)
        source, state = root / "source", root / "state"
        initialize_source(source)
        queue_path = root / ".github" / "relay" / "queue.json"
        receipt_path = state / "receipt.json"
        worker.save(queue_path, queue)
        engine_path = state / "engine.json"
        worker.save(engine_path, {
            "schema_version": 1, "repo": repo, "cursor": 0, "revision": 0,
            "processed_run_keys": [], "families": {}, "strict_business_completed": 0,
        })
        args = SimpleNamespace(repo=repo, queue=queue_path, source=source, state=state,
                               output=receipt_path, receipt=receipt_path, limit=2)
        worker.evaluate(args)
        sys.stdout.flush()
        results = worker.load(receipt_path)["results"]
        assert results[0]["status"] == "FORMAL_SUBSET_PASS_NATIVE_PENDING"
        assert results[1]["status"] == "FORMAL_CHECK_FAILED_OR_BLOCKED"
        assert results[1]["checks"][0]["exit_code"] == 0
        assert results[1]["checks"][0]["skipped"] == 1

        integration_cmd = base_cmd + ["test_*.py"]
        worker.save(state / "integration.json", {
            **worker.test(integration_cmd, source, source),
            "schema_version": 1, "repo": repo, "command": integration_cmd,
            "source_subdir": ".", "verified_business_complete": False,
            "checked_utc": worker.load(receipt_path)["generated_utc"],
        })
        persist = [sys.executable, "-B", str(relay), "persist", "--repo", repo,
                   "--state", str(state), "--receipt", str(receipt_path)]
        subprocess.run(persist, cwd=root, check=True)
        first = worker.load(engine_path)
        assert (first["revision"], first["cursor"], first["strict_business_completed"]) == (1, 2, 0)
        history = (state / "history.jsonl").read_bytes()
        subprocess.run(persist, cwd=root, check=True)
        assert worker.load(engine_path) == first
        assert (state / "history.jsonl").read_bytes() == history
        print("DEMO_OK: two checks recorded, skipped check rejected, duplicate replay unchanged")


if __name__ == "__main__":
    main()
