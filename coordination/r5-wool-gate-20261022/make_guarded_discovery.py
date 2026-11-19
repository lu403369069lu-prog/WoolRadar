"""Derive a review-only absolute-test-discovery gate from the R4 -I candidate."""
from pathlib import Path

HERE = Path(__file__).resolve().parent
R4 = HERE.parent / "r4-integration-gate-20261022"
if not R4.exists():
    R4 = HERE.parent / "integration-gate-negative-20261022"
source = (R4 / "integration_gate_candidate_isolated.py").read_text(encoding="utf-8")
imp = 'from worker import parse_test_summary'
redirect = '''_REVIEW_ROOT = Path(__file__).resolve().parent.parent
_R4_WORKER = next((p for p in (
    _REVIEW_ROOT / "r4-integration-gate-20261022",
    _REVIEW_ROOT / "integration-gate-negative-20261022")
    if (p / "worker.py").is_file()), None)
if _R4_WORKER is None:
    raise RuntimeError("missing original R4 worker.py dependency")
sys.path.insert(0, str(_R4_WORKER))
from worker import parse_test_summary'''
assert source.count(imp) == 1
source = source.replace(imp, redirect)
old = 'cmd = [sys.executable, "-I", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]'
new = ('cmd = [sys.executable, "-I", "-B", "-m", "unittest", "discover", '
       '"-s", str(cwd / "tests"), "-t", str(cwd), "-p", "test_*.py"]')
assert source.count(old) == 1
source = source.replace(old, new)
anchor = '    try:\n        proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True,'
guard = '''    if args.repo == "WoolRadar":
        tests_dir = cwd / "tests"
        if (tests_dir.is_symlink() or not tests_dir.is_dir()
                or not tests_dir.resolve().is_relative_to(cwd)):
            base.update({"status": "BLOCKED", "error_kind": "INVALID_TEST_DISCOVERY_ROOT"})
            dest = Path(args.output)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(base, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
            print(json.dumps({"integration": "BLOCKED", "error_kind": base["error_kind"]}))
            return
'''
assert source.count(anchor) == 1
source = source.replace(anchor, guard + anchor)
out = HERE / "integration_gate_guarded_discovery.py"
out.write_text(source, encoding="utf-8", newline="\n")
compile(source, str(out), "exec")
print(f"GENERATED {out.name}; R4 sibling dependency pinned by path; syntax OK")
