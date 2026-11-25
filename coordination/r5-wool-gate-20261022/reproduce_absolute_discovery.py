"""Test that Python -I discovery tests exactly the selected source checkout."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil

HERE = Path(__file__).resolve().parent
R4 = HERE.parent / "r4-integration-gate-20261022"
if not R4.exists():
    R4 = HERE.parent / "integration-gate-negative-20261022"


def run(script, root, name):
    report = HERE / (name + ".json")
    call = [sys.executable, "-B", "-X", "utf8", str(script), "--repo", "WoolRadar",
            "--source", str(root), "--output", str(report)]
    proc = subprocess.run(call, capture_output=True, text=True, timeout=60)
    if proc.returncode:
        raise AssertionError((script.name, proc.returncode, proc.stderr[-1000:]))
    data = json.loads(report.read_text(encoding="utf-8"))
    # Evidence excludes filesystem paths, child command, environment and private data.
    return {"status": data["status"], "total": data.get("total"),
            "failed": data.get("failed"), "error_kind": data.get("error_kind")}


def main():
    original = R4 / "integration_gate_candidate_isolated.py"
    guarded = HERE / "integration_gate_guarded_discovery.py"
    assert guarded.exists()
    checks = {}
    observed = {}
    with tempfile.TemporaryDirectory(dir=HERE, prefix="source-fixture-") as directory:
        root = Path(directory)
        tests = root / "tests"
        tests.mkdir()
        (tests / "__init__.py").write_text("", encoding="utf-8")
        test = tests / "test_smoke.py"
        test.write_text("import unittest\nclass Probe(unittest.TestCase):\n"
                        " def test_no_forged_pass(self): self.assertTrue(False)\n",
                        encoding="utf-8")
        observed["original_failing_local"] = run(original, root, "original-failing-local")
        # The R4 -I runner ignores PYTHONDONTWRITEBYTECODE and can leave pyc.
        shutil.rmtree(tests / "__pycache__", ignore_errors=True)
        observed["guarded_failing_local"] = run(guarded, root, "guarded-failing-local")
        checks["local_failing_test_is_executed"] = (
            observed["guarded_failing_local"]["status"] == "FAIL" and
            observed["guarded_failing_local"]["total"] == 1)

        test.write_text("import unittest\nclass Probe(unittest.TestCase):\n"
                        " def test_real_pass(self): self.assertTrue(True)\n",
                        encoding="utf-8")
        observed["guarded_passing_local"] = run(guarded, root, "guarded-passing-local")
        checks["local_passing_test_is_executed"] = (
            observed["guarded_passing_local"]["status"] == "PASS" and
            observed["guarded_passing_local"]["total"] == 1)
        checks["guarded_does_not_write_pycache"] = not (tests / "__pycache__").exists()

        shutil.rmtree(tests)
        observed["original_missing_local"] = run(original, root, "original-missing-local")
        observed["guarded_missing_local"] = run(guarded, root, "guarded-missing-local")
        checks["missing_test_root_is_blocked"] = (
            observed["guarded_missing_local"]["status"] == "BLOCKED" and
            observed["guarded_missing_local"]["error_kind"] == "INVALID_TEST_DISCOVERY_ROOT")

    # The original's result is diagnostic: it may discover unrelated installed tests.
    checks["original_discovered_foreign_tests"] = (
        observed["original_missing_local"]["total"] not in (None, 0))
    evidence = {"kind": "synthetic_python_discovery_root_verification",
                "business_acceptance": False, "checks": checks, "observed": observed}
    (HERE / "discovery-evidence.json").write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
