"""Reproduce R5 discovery-root mismatch from a clean exact PR113 local checkout.

Usage: python -B reproduce_pr113_r5_layout.py --checkout PATH_TO_PR113_CHECKOUT
"""
import argparse
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile

HEAD = "396ce94e3510d4f09f951b0a973716c3c343bc93"
HERE = Path(__file__).resolve().parent
GATE = HERE.parent / "r5-wool-gate-20261022" / "integration_gate_guarded_discovery.py"


def local_git(checkout: Path, *args) -> str:
    return subprocess.run(["git", "-C", str(checkout), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def verify(checkout: Path) -> dict:
    if local_git(checkout, "rev-parse", "HEAD") != HEAD:
        raise RuntimeError("requires the exact reviewed PR113 HEAD")
    if local_git(checkout, "status", "--porcelain=v1"):
        raise RuntimeError("source checkout must be clean")
    files = local_git(checkout, "ls-tree", "-r", "--name-only", "HEAD").splitlines()
    tests = [f for f in files if f.startswith((".github/relay/", "coordination/"))
             and PurePosixPath(f).name.startswith("test_") and f.endswith(".py")]
    assert tests and "tests" not in local_git(checkout, "ls-tree", "--name-only", "HEAD").splitlines()

    with tempfile.TemporaryDirectory(prefix="review-r6-layout-", dir=HERE) as temp_dir:
        temp = Path(temp_dir)
        zip_path = temp / "pr113.zip"
        subprocess.run(["git", "-C", str(checkout), "archive", "--format=zip",
                        "-o", str(zip_path), "HEAD"], check=True)
        root = temp / "source"
        root.mkdir()
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(root)
        assert not (root / "tests").exists()
        assert all((root / f).is_file() for f in tests)
        output = temp / "report.json"
        proc = subprocess.run([sys.executable, "-B", str(GATE), "--repo", "WoolRadar",
                               "--source", str(root), "--output", str(output)],
                              capture_output=True, text=True, timeout=90)
        report = json.loads(output.read_text(encoding="utf-8"))

    result = {
        "source_head_sha": HEAD,
        "tracked_test_python_files": len(tests),
        "test_root_present": False,
        "gate_process_exit": proc.returncode,
        "gate_status": report["status"],
        "gate_error_kind": report.get("error_kind"),
        "original_worktree_clean_after": not bool(local_git(checkout, "status", "--porcelain=v1")),
        "business_acceptance": False,
    }
    assert (result["gate_process_exit"], result["gate_status"], result["gate_error_kind"]) == (
        0, "BLOCKED", "INVALID_TEST_DISCOVERY_ROOT")
    assert result["original_worktree_clean_after"]
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    args = parser.parse_args()
    result = verify(args.checkout.resolve())
    (HERE / "real-layout-evidence.json").write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
