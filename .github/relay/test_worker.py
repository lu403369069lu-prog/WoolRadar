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
import os
import venv
import zipfile
from unittest.mock import patch

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
            "source_commit": q["source_ref"] if len(q["source_ref"]) == 40 else "a" * 40, "source_ref": q["source_ref"],
            "queue_sha256": worker.queue_digest(q),
            "previous_cursor": cursor, "next_cursor": (cursor + 1) % len(q["families"]),
            "strict_new_acceptances": 0, "generated_utc": "2026-10-18T00:00:00Z",
            "results": [{"id": fam["id"], "goal": fam["goal"], "status": status,
                         "checks": checks, "strictly_complete": False,
                         "business_accepted": False}]
        }

    def run_persist(self, directory, q, receipt, integration_sha="DEFAULT", integration_mutator=None, runner_key=None):
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
            integration["source_commit"] = receipt['source_commit'] if integration_sha == 'DEFAULT' else integration_sha
        integration["run_key"] = receipt["run_key"]
        if integration_mutator is not None:
            integration_mutator(integration)
        worker.save(directory / "integration.json", integration)
        worker.save(rec, receipt)
        selected_run = runner_key if runner_key is not None else receipt["run_key"]
        runner_id, attempt = selected_run.split("/", 1)
        with patch.dict(os.environ, {"GITHUB_RUN_ID": runner_id, "GITHUB_RUN_ATTEMPT": attempt}):
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

    def test_glob_discovery_rejects_untracked_and_modified_test_bytes(self):
        """Exact HEAD is insufficient when the discovered worktree changes."""
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        self.assertTrue(worker.safe(check))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            verified = tests / "test_public_corpus_verified.py"
            original = ("import unittest\nclass Probe(unittest.TestCase):\n"
                        "    def test_verified(self): self.assertTrue(True)\n")
            verified.write_text(original, encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests/test_public_corpus_verified.py"],
                           cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester",
                            "-c", "user.email=test@example.invalid", "commit",
                            "-qm", "pin test"], cwd=root, check=True)
            pinned_sha = worker.source_sha(root)
            clean = worker.test(check, root, root)
            self.assertEqual((clean["status"], clean["total"]), ("PASS", 1))

            untracked = tests / "test_public_corpus_untracked.py"
            untracked.write_text(original.replace("verified", "extra"),
                                 encoding="utf-8")
            blocked = worker.test(check, root, root)
            self.assertEqual(blocked.get("error_kind"), "UNREVIEWED_TEST_SOURCE")
            self.assertEqual(blocked["status"], "BLOCKED")
            self.assertEqual(worker.source_sha(root), pinned_sha)

            untracked.unlink()
            verified.write_text(original.replace("True", "False"), encoding="utf-8")
            modified = worker.test(check, root, root)
            self.assertEqual(modified.get("error_kind"), "UNREVIEWED_TEST_SOURCE")
            self.assertEqual(modified["status"], "BLOCKED")
            self.assertEqual(worker.source_sha(root), pinned_sha)

    def test_glob_discovery_rejects_test_files_created_during_run(self):
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            verified = tests / "test_public_corpus_writer.py"
            verified.write_text(
                "import unittest\nfrom pathlib import Path\n"
                "class Probe(unittest.TestCase):\n"
                "    def test_write(self):\n"
                "        Path('tests/test_public_corpus_injected.py').write_text("
                "'import unittest\\nclass New(unittest.TestCase):\\n"
                " def test_ok(self): self.assertTrue(True)\\n')\n",
                encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests/test_public_corpus_writer.py"],
                           cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester",
                            "-c", "user.email=test@example.invalid", "commit",
                            "-qm", "pin test"], cwd=root, check=True)
            result = worker.test(check, root, root)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result.get("error_kind"), "UNREVIEWED_TEST_SOURCE")
            self.assertTrue((tests / "test_public_corpus_injected.py").exists())

    def test_modified_json_fixture_cannot_forge_pinned_pass(self):
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        self.assertTrue(worker.safe(check))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_public_corpus_fixture.py").write_text(
                "import json, unittest\nfrom pathlib import Path\n"
                "class FixtureCheck(unittest.TestCase):\n"
                " def test_valid(self):\n"
                "  value = json.loads(Path('tests/fixture.json').read_text())\n"
                "  self.assertTrue(value['valid'])\n", encoding="utf-8")
            fixture = tests / "fixture.json"
            fixture.write_text('{"valid": false}\n', encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester",
                            "-c", "user.email=test@example.invalid", "commit",
                            "-qm", "pin"], cwd=root, check=True)
            pinned_sha = worker.source_sha(root)
            self.assertEqual(worker.test(check, root, root)["status"], "FAIL")
            fixture.write_text('{"valid": true}\n', encoding="utf-8")
            changed = worker.test(check, root, root)
            self.assertEqual(changed.get("status"), "BLOCKED", changed)
            self.assertEqual(changed.get("error_kind"), "UNREVIEWED_TEST_SOURCE")
            self.assertEqual(worker.source_sha(root), pinned_sha)

            fixture.write_text('{"valid": false}\n', encoding="utf-8")
            rogue = tests / "unreviewed.json"
            rogue.write_text('{"valid": true}\n', encoding="utf-8")
            untracked = worker.test(check, root, root)
            self.assertEqual(untracked.get("status"), "BLOCKED", untracked)
            self.assertEqual(untracked.get("error_kind"), "UNREVIEWED_TEST_SOURCE")
            rogue.unlink()
            self.assertEqual(worker.test(check, root, root)["status"], "FAIL")

    def test_untracked_pyz_archive_cannot_forge_pinned_pass(self):
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_public_corpus_archive.py").write_text(
                "import sys, unittest\n"
                "sys.path.insert(0, 'tests/plugin.pyz')\n"
                "from helper_from_zip import value\n"
                "class Probe(unittest.TestCase):\n"
                " def test_valid(self): self.assertEqual(value, 17)\n",
                encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester",
                            "-c", "user.email=test@example.invalid", "commit",
                            "-qm", "pin"], cwd=root, check=True)
            pinned_sha = worker.source_sha(root)
            self.assertEqual(worker.test(check, root, root)["status"], "FAIL")
            archive = tests / "plugin.pyz"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("helper_from_zip.py", "value = 17\n")
            forged = worker.test(check, root, root)
            self.assertEqual(forged["status"], "BLOCKED", forged)
            self.assertEqual(forged.get("error_kind"), "UNREVIEWED_TEST_SOURCE")
            self.assertEqual(worker.source_sha(root), pinned_sha)

    def test_binary_fixture_change_must_not_normalize_crlf(self):
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_public_corpus_binary.py").write_text(
                "import unittest\nfrom pathlib import Path\n"
                "class Probe(unittest.TestCase):\n"
                " def test_bytes(self):\n"
                "  self.assertEqual(Path('tests/fixture.db').read_bytes(), b'A\\nB')\n",
                encoding="utf-8")
            fixture = tests / "fixture.db"
            fixture.write_bytes(b"A\r\nB")
            # Do not let a developer's global core.autocrlf rewrite this
            # deliberately binary fixture while staging the pinned blob.
            (root / ".gitattributes").write_text(
                "tests/fixture.db -text\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester",
                            "-c", "user.email=test@example.invalid", "commit",
                            "-qm", "pin"], cwd=root, check=True)
            pinned_sha = worker.source_sha(root)
            self.assertEqual(worker.test(check, root, root)["status"], "FAIL")
            fixture.write_bytes(b"A\nB")
            forged = worker.test(check, root, root)
            self.assertEqual(forged["status"], "BLOCKED", forged)
            self.assertEqual(forged.get("error_kind"), "UNREVIEWED_TEST_SOURCE")
            self.assertEqual(worker.source_sha(root), pinned_sha)

    def test_hyphenated_discovery_checks_selected_tests_and_helpers(self):
        """Discovery adds its own directory, regardless of package-name syntax."""
        check = ["python", "-m", "unittest", "discover", "-s",
                 "independent-quality/public-corpus-blind-dedup-20261016",
                 "-p", "test_*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / check[5]
            tests.mkdir(parents=True)
            target = tests / "test_selected.py"
            original = ("import unittest\nimport helper\nclass Probe(unittest.TestCase):\n"
                        " def test_truth(self): self.assertEqual(helper.value, 17)\n")
            target.write_text(original, encoding="utf-8")
            helper = tests / "helper.py"
            helper.write_text("value = 17\n", encoding="utf-8")
            # A valid unrelated import path must not hide omitted selected tests.
            (root / "unrelated.py").write_text("value = 1\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "pin"], cwd=root, check=True)
            self.assertEqual(worker.test(check, root, root)["status"], "PASS")
            for changed in (target, helper):
                with self.subTest(changed=changed.name):
                    old = changed.read_text(encoding="utf-8")
                    changed.write_text(old.replace("17", "18"), encoding="utf-8")
                    result = worker.test(check, root, root)
                    self.assertEqual(result.get("status"), "BLOCKED", result)
                    self.assertEqual(result.get("error_kind"), "UNREVIEWED_TEST_SOURCE", result)
                    changed.write_text(old, encoding="utf-8")
            helper.unlink()
            deleted = worker.test(check, root, root)
            self.assertEqual(deleted.get("status"), "BLOCKED", deleted)
            self.assertEqual(deleted.get("error_kind"), "UNREVIEWED_TEST_SOURCE", deleted)

    def test_assume_unchanged_index_flag_cannot_hide_modified_test(self):
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            target = tests / "test_public_corpus_pinned.py"
            original = ("import unittest\nclass Probe(unittest.TestCase):\n"
                        " def test_truth(self): self.assertTrue(True)\n")
            target.write_text(original, encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests/test_public_corpus_pinned.py"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "pin"], cwd=root, check=True)
            target.write_text(original.replace("True", "False"), encoding="utf-8")
            subprocess.run(["git", "update-index", "--assume-unchanged",
                            "tests/test_public_corpus_pinned.py"], cwd=root, check=True)
            result = worker.test(check, root, root)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result.get("error_kind"), "UNREVIEWED_TEST_SOURCE")

    def test_skip_worktree_index_flag_cannot_hide_modified_test(self):
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            target = tests / "test_public_corpus_pinned.py"
            target.write_text("import unittest\nclass Probe(unittest.TestCase):\n"
                              " def test_truth(self): self.assertTrue(True)\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests/test_public_corpus_pinned.py"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "pin"], cwd=root, check=True)
            subprocess.run(["git", "update-index", "--skip-worktree",
                            "tests/test_public_corpus_pinned.py"], cwd=root, check=True)
            target.write_text("import unittest\nclass Probe(unittest.TestCase):\n"
                              " def test_truth(self): self.assertTrue(False)\n", encoding="utf-8")
            result = worker.test(check, root, root)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result.get("error_kind"), "UNREVIEWED_TEST_SOURCE")

    def test_unreviewed_helper_python_cannot_change_pinned_test_result(self):
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            target = tests / "test_public_corpus_helper.py"
            target.write_text("import unittest\nimport helper\nclass Probe(unittest.TestCase):\n"
                              " def test_value(self): self.assertEqual(helper.value, 1)\n", encoding="utf-8")
            helper = tests / "helper.py"
            helper.write_text("value = 1\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests/test_public_corpus_helper.py", "tests/helper.py"],
                           cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "pin"], cwd=root, check=True)
            self.assertEqual(worker.test(check, root, root)["status"], "PASS")
            helper.write_text("value = 2\n", encoding="utf-8")
            changed = worker.test(check, root, root)
            self.assertEqual(changed["status"], "BLOCKED")
            self.assertEqual(changed.get("error_kind"), "UNREVIEWED_TEST_SOURCE")
            helper.write_text("value = 1\n", encoding="utf-8")
            helper.unlink()
            untracked = worker.test(check, root, root)
            self.assertEqual(untracked["status"], "BLOCKED")
            self.assertEqual(untracked.get("error_kind"), "UNREVIEWED_TEST_SOURCE")

    def test_untracked_sourceless_bytecode_cannot_forge_pinned_pass(self):
        """Sourceless helper.pyc is importable despite no .py source file."""
        import py_compile
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_public_corpus_bytecode.py").write_text(
                "import unittest\nimport helper\nclass Probe(unittest.TestCase):\n"
                " def test_value(self): self.assertEqual(helper.value, 17)\n",
                encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests/test_public_corpus_bytecode.py"],
                           cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "pin"], cwd=root, check=True)
            hidden = tests / "helper.py"
            hidden.write_text("value = 17\n", encoding="utf-8")
            py_compile.compile(str(hidden), cfile=str(tests / "helper.pyc"), doraise=True)
            hidden.unlink()
            # This previously reported PASS=1 although source HEAD contained
            # no helper module; the compiled bytecode supplied the assertion.
            result = worker.test(check, root, root)
            self.assertEqual(result.get("status"), "BLOCKED", result)
            self.assertEqual(result.get("error_kind"), "UNREVIEWED_TEST_SOURCE", result)

    def test_untracked_bytecode_cache_cannot_override_reviewed_helper(self):
        """Unchecked-hash cache bytes must not supersede a pinned .py helper."""
        import py_compile
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_public_corpus_cache.py").write_text(
                "import unittest\nimport helper\nclass Probe(unittest.TestCase):\n"
                " def test_value(self): self.assertEqual(helper.value, 17)\n",
                encoding="utf-8")
            helper = tests / "helper.py"
            helper.write_text("value = 0\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests/test_public_corpus_cache.py", "tests/helper.py"],
                           cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "pin"], cwd=root, check=True)
            self.assertEqual(worker.test(check, root, root)["status"], "FAIL")
            # Python may execute this bytecode in preference to helper.py even
            # while the checked-in source bytes still match HEAD.
            injected = root / "poison.py"
            injected.write_text("value = 17\n", encoding="utf-8")
            cached = tests / "__pycache__" / ("helper." + sys.implementation.cache_tag + ".pyc")
            cached.parent.mkdir()
            py_compile.compile(str(injected), cfile=str(cached), doraise=True,
                               invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
            result = worker.test(check, root, root)
            self.assertEqual(result.get("status"), "BLOCKED", result)
            self.assertEqual(result.get("error_kind"), "UNREVIEWED_TEST_SOURCE", result)

    def test_isolated_interpreter_keeps_reviewed_project_imports(self):
        """Real Wool tests import core.* from the checkout root."""
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests, core = root / "tests", root / "core"
            tests.mkdir()
            core.mkdir()
            (core / "__init__.py").write_text("value = 17\n", encoding="utf-8")
            (tests / "test_public_corpus_core_import.py").write_text(
                "import unittest\nfrom core import value\n"
                "class Probe(unittest.TestCase):\n"
                " def test_value(self): self.assertEqual(value, 17)\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests/test_public_corpus_core_import.py",
                            "core/__init__.py"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "pin"], cwd=root, check=True)
            result = worker.test(check, root, root)
            self.assertEqual((result.get("status"), result.get("total")), ("PASS", 1), result)
            (core / "__init__.py").write_text("value = 18\n", encoding="utf-8")
            mutated = worker.test(check, root, root)
            self.assertEqual(mutated.get("status"), "BLOCKED", mutated)
            self.assertEqual(mutated.get("error_kind"), "UNREVIEWED_TEST_SOURCE", mutated)
            (core / "__init__.py").write_text("value = 17\n", encoding="utf-8")
            (root / "roothelper.py").write_text("value = 123\n", encoding="utf-8")
            untracked = worker.test(check, root, root)
            self.assertEqual(untracked.get("status"), "BLOCKED", untracked)
            self.assertEqual(untracked.get("error_kind"), "UNREVIEWED_TEST_SOURCE", untracked)

    def test_inherited_pythonpath_cannot_make_failing_pinned_test_pass(self):
        """External sitecustomize must not alter a formally reviewed test."""
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            root = sandbox / "source"
            root.mkdir()
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_public_corpus_env.py").write_text(
                "import unittest\nclass Probe(unittest.TestCase):\n"
                " def test_truth(self): self.assertTrue(False)\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests/test_public_corpus_env.py"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "pin"], cwd=root, check=True)
            baseline = worker.test(check, root, root)
            self.assertEqual(baseline["status"], "FAIL", baseline)
            external = sandbox / "external-site"
            external.mkdir()
            (external / "sitecustomize.py").write_text(
                "import unittest\nunittest.TestCase.assertTrue = lambda self, expr, msg=None: None\n",
                encoding="utf-8")
            with patch.dict(os.environ, {"PYTHONPATH": str(external)}):
                result = worker.test(check, root, root)
            self.assertEqual(result["status"], "FAIL", result)

    def test_python_user_site_cannot_make_failing_pinned_test_pass(self):
        """An external usercustomize.py must not forge a reviewed test result."""
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            root = sandbox / "source"
            root.mkdir()
            tests = root / "tests"
            tests.mkdir()
            (tests / "test_public_corpus_user_site.py").write_text(
                "import unittest\nclass Probe(unittest.TestCase):\n"
                " def test_truth(self): self.assertTrue(False)\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests/test_public_corpus_user_site.py"],
                           cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "pin"], cwd=root, check=True)
            baseline = worker.test(check, root, root)
            self.assertEqual(baseline["status"], "FAIL", baseline)
            external = sandbox / "external-user-site"
            env = {**os.environ, "PYTHONUSERBASE": str(external)}
            user_site = subprocess.run(
                [sys.executable, "-X", "utf8", "-c",
                 "import site;print(site.getusersitepackages())"],
                text=True, encoding="utf-8", capture_output=True,
                check=True, env=env).stdout.strip()
            site_dir = Path(user_site)
            site_dir.mkdir(parents=True)
            (site_dir / "usercustomize.py").write_text(
                "import unittest\nunittest.TestCase.assertTrue = lambda self, expr, msg=None: None\n",
                encoding="utf-8")
            with patch.dict(os.environ, {"PYTHONUSERBASE": str(external)}):
                result = worker.test(check, root, root)
            self.assertEqual(result["status"], "FAIL", result)

    def test_active_virtualenv_pth_cannot_forge_failing_reviewed_test(self):
        """Interpreter startup hooks outside the checkout must not forge PASS."""
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            sandbox = Path(tmp)
            root = sandbox / "source"
            tests = root / "tests"
            tests.mkdir(parents=True)
            (tests / "test_public_corpus_pth.py").write_text(
                "import unittest\nclass Probe(unittest.TestCase):\n"
                " def test_truth(self): self.assertTrue(False)\n", encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests/test_public_corpus_pth.py"],
                           cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "pin"], cwd=root, check=True)
            environment = sandbox / "active-venv"
            venv.EnvBuilder(with_pip=False).create(environment)
            executable = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            site_run = subprocess.run(
                [str(executable), "-I", "-B", "-X", "utf8", "-c",
                 "import site;print(site.getsitepackages()[0])"],
                capture_output=True, text=True, encoding="utf-8", check=True)
            site_dir = Path(site_run.stdout.strip())
            self.assertTrue(site_dir.is_dir())
            with patch.object(worker.sys, "executable", str(executable)):
                baseline = worker.test(check, root, root)
                self.assertEqual(baseline["status"], "FAIL", baseline)
                (site_dir / "forge.pth").write_text(
                    "import unittest; unittest.TestCase.assertTrue = lambda self, value, msg=None: None\n",
                    encoding="utf-8")
                forged = worker.test(check, root, root)
            self.assertEqual(forged["status"], "FAIL", forged)
            self.assertEqual(subprocess.run(["git", "status", "--porcelain"], cwd=root,
                                            capture_output=True, check=True).stdout, b"")

    def test_nonidentifier_dynamic_import_helper_is_authenticated(self):
        """Importlib loads hyphenated module paths that source guards must pin."""
        check = ["python", "-m", "unittest", "discover", "-s", "tests",
                 "-p", "test_public_corpus*.py"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tests = root / "tests"
            helper = tests / "nonidentifier-dir" / "helper.py"
            helper.parent.mkdir(parents=True)
            helper.write_text("value = 17\n", encoding="utf-8")
            (tests / "test_public_corpus_dynamic.py").write_text(
                "import importlib,unittest\nclass Probe(unittest.TestCase):\n"
                " def test_truth(self): self.assertEqual("
                "importlib.import_module('nonidentifier-dir.helper').value,18)\n",
                encoding="utf-8")
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "add", "tests"], cwd=root, check=True)
            subprocess.run(["git", "-c", "user.name=Tester", "-c", "user.email=test@example.invalid",
                            "commit", "-qm", "pin"], cwd=root, check=True)
            self.assertEqual(worker.test(check, root, root)["status"], "FAIL")
            helper.write_text("value = 18\n", encoding="utf-8")
            result = worker.test(check, root, root)
            self.assertEqual(result.get("status"), "BLOCKED", result)
            self.assertEqual(result.get("error_kind"), "UNREVIEWED_TEST_SOURCE", result)

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
        stub = SimpleNamespace(stdout=sample_output.encode("utf-8"), stderr=b"", returncode=0)
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

    def test_persist_rejects_mismatched_github_actions_run_context(self):
        q = self.queue()
        for runner_key in ("999999/1", "123456/2", "synthetic/1"):
            with self.subTest(runner_key=runner_key), tempfile.TemporaryDirectory() as tmp:
                receipt = self.receipt(q)
                with self.assertRaises(ValueError):
                    self.run_persist(Path(tmp), q, receipt, runner_key=runner_key)

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
