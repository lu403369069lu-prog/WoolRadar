#!/usr/bin/env python3
"""Historical Codex offline acceptance, 2026-10-17.

DRY RUN by default. Runs only in a disposable, nonproduction clone/worktree.
No git push, merge, checkout, installation, API, scheduled task or user data reads.
The exact immutable SHA contract is required before executing a test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

EXPECTED = {
    "wool": "80c5ea18769c1312e5be5fd99a39e4f3d498c64f",
    "sam": "82bf36efa90cced8dafb56502812eb49f40515f3",
    "coord": "27796df5f9847c1bb5d48d2a445e418dfb3d8e96",
}

# Every command uses only this code checkout and synthetic/temp test fixtures.
# SAM dependency installation is intentionally NOT automatic.
BATCHES = {
    "wool": [
        ("W-ALL", ".", [sys.executable, "-B", "-m", "unittest", "discover",
                         "-s", "tests", "-p", "test_*.py", "-v"]),
        ("W-SAMPLER", ".", [sys.executable, "-B", "-m", "unittest", "discover",
                             "-s", "independent-quality/public-corpus-blind-dedup-20261016",
                             "-p", "test_*.py", "-v"]),
        ("W-SNAPSHOT", ".", [sys.executable, "-B", "-m", "unittest", "discover",
                              "-s", "independent-quality/delivery-bridge-20261016",
                              "-p", "test_*.py", "-v"]),
    ],
    "sam": [
        ("S-BUILD", "SAM/snapshot", ["npm.cmd" if os.name == "nt" else "npm", "run", "build"]),
        ("S-ALL", "SAM/snapshot", ["npm.cmd" if os.name == "nt" else "npm", "test"]),
        ("S-ROOTED", "SAM/snapshot", ["node", "--import", "tsx", "--test",
                                      "../independent-review/20261016/rooted-source-authorization.test.ts",
                                      "../independent-review/20261016/glob-case-parity.test.ts",
                                      "../independent-review/20261016/glob-ripgrep-572-matrix.test.ts"]),
        ("S-TEACHER", "SAM/snapshot", ["node", "--test",
                                       "../independent-review/20261016-0904-audit-coverage/audit_coverage.test.mjs",
                                       "../independent-review/20261016-0904-audit-coverage/holdout_identity_check.test.mjs",
                                       "../independent-review/20261016-0904-audit-coverage/holdout_identity_cli.test.mjs",
                                       "../independent-review/20261016-0904-audit-coverage/positive_answer_gate.test.mjs",
                                       "../independent-review/20261016-0904-audit-coverage/strict_teacher_jsonl.test.mjs"]),
    ],
    "coord": [
        ("C-ALL", ".", [sys.executable, "-B", "-m", "unittest", "discover",
                         "-s", "tests", "-p", "test_*.py", "-v"]),
    ],
}



def validate_handoff_manifest(manifest_path: Path, project: str, expected: str) -> dict:
    """Fail closed when 50-family manifest and reviewed execution contract disagree."""
    if not manifest_path.is_file():
        raise RuntimeError('Missing adjacent historical 50-family jobs manifest.')
    try:
        doc = json.loads(manifest_path.read_text(encoding='utf-8'))
    except (ValueError, UnicodeError) as exc:
        raise RuntimeError('Cannot parse historical jobs manifest.') from exc
    jobs = doc.get('jobs')
    refs = doc.get('immutable_refs')
    if doc.get('total_families') != 50 or not isinstance(jobs, list) or len(jobs) != 50:
        raise RuntimeError('Unexpected historical family count; manual review required.')
    if not isinstance(refs, dict) or any(key not in refs for key in ('W','S','C')):
        raise RuntimeError('Missing reviewed project refs in historical manifest.')
    key = {'wool':'W','sam':'S','coord':'C'}[project]
    if refs[key].get('sha') != expected or EXPECTED[project] != expected:
        raise RuntimeError('Runner and jobs manifest source SHA mismatch.')
    projects = {'W':'WoolRadar','S':'YinQieJi-SAM','C':'WoolRadar-Coord'}
    used = set()
    ready = 0
    for job in jobs:
        fid = job.get('family_id')
        if not isinstance(fid, str) or not fid or fid in used:
            raise RuntimeError('Missing or repeated historical family identifier.')
        used.add(fid)
        matched = next((k for k,v in projects.items() if v == job.get('project')), None)
        if matched is None or job.get('required_head_sha') != refs[matched].get('sha') or job.get('repo') != refs[matched].get('repo'):
            raise RuntimeError('Historical job is not pinned to its project source.')
        mode = job.get('disposition')
        if mode == 'READY_FOR_LOCAL_CODEX':
            ready += 1
            if not (job.get('run_command') and job.get('verified_test_blob') and job.get('verified_test_path')):
                raise RuntimeError('Runnable history job missing required test evidence.')
        elif mode != 'EXTERNAL_OR_POLICY_GATED':
            raise RuntimeError('Unknown historical job disposition.')
    if ready != 42 or doc.get('ready_for_local_codex') != 42 or doc.get('external_or_policy_gated') != 8:
        raise RuntimeError('Historical 42/8 readiness contract changed.')
    if not any(job['project'] == projects[key] for job in jobs):
        raise RuntimeError('Selected project has no reviewed jobs.')
    return {'families':len(jobs),'ready':ready,'project':project,'source':expected}



def git(args: list[str], cwd: Path) -> str:
    p = subprocess.run(["git", *args], cwd=cwd, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       timeout=30, check=False)
    if p.returncode:
        raise RuntimeError("git preflight failed (code %s): %s" %
                           (p.returncode, p.stderr[:300]))
    return p.stdout.strip()


def preflight(repo: Path, project: str, expected: str) -> str:
    path = str(repo.resolve()).replace("/", "\\").lower().rstrip("\\")
    # Do not touch the local installation and user/PLC material.
    forbidden = ("c:\\woolradar", "\\sam_local\\", "\\twincat\\",
                 "\\production\\", "\\appdata\\")
    if any(path == f or path.startswith(f + "\\") for f in forbidden[:1]) or any(
            f in path for f in forbidden[1:]):
        raise RuntimeError("Refusing production/private repo path; use disposable clone.")
    root = Path(git(["rev-parse", "--show-toplevel"], repo)).resolve()
    if root != repo:
        raise RuntimeError("Supply exact repository root, not subfolder.")
    head = git(["rev-parse", "HEAD"], repo)
    if head != expected:
        raise RuntimeError("SHA mismatch: expected %s, got %s; rebase/review before tests." %
                           (expected, head))
    if git(["status", "--porcelain"], repo):
        raise RuntimeError("Dirty worktree. Execute in a clean disposable copy.")
    marker = ("SAM/snapshot/package.json" if project == "sam"
              else "coordination/relay.py" if project == "coord"
              else "core/public_corpus.py")
    if not (repo / marker).is_file():
        raise RuntimeError("Wrong project/ref: missing %s" % marker)
    return head


def summarize(output: str) -> dict[str, int | None]:
    """Parse one subprocess's actual test counts, never infer a pass from exit=0."""
    node = re.search(r"(?m)^# tests (\d+)\s*$", output)
    node_pass = re.search(r"(?m)^# pass (\d+)\s*$", output)
    node_fail = re.search(r"(?m)^# fail (\d+)\s*$", output)
    node_skip = re.search(r"(?m)^# skipped (\d+)\s*$", output)
    py = re.search(r"(?m)^Ran (\d+) tests? in [\d.]+s", output)
    py_ok = re.search(r"(?m)^OK(?:\s*\(skipped=(\d+)\))?\s*$", output)
    py_failed = re.search(r"(?m)^FAILED \(([^)]*)\)", output)
    if node:
        return {"tests_reported": int(node.group(1)),
                "passed": int(node_pass.group(1)) if node_pass else None,
                "failed": int(node_fail.group(1)) if node_fail else None,
                "skipped": int(node_skip.group(1)) if node_skip else 0}
    if py:
        total = int(py.group(1))
        skipped = int(py_ok.group(1)) if py_ok and py_ok.group(1) else 0
        if py_failed:
            fields = dict((k, int(n)) for k, n in
                          re.findall(r"(failures|errors|skipped)=(\d+)", py_failed.group(1)))
            skipped = fields.get("skipped", 0)
            failed = fields.get("failures", 0) + fields.get("errors", 0)
            return {"tests_reported": total,
                    "passed": max(0, total - failed - skipped),
                    "failed": failed, "skipped": skipped}
        return {"tests_reported": total,
                "passed": total - skipped if py_ok else None,
                "failed": 0 if py_ok else None, "skipped": skipped}
    return {"tests_reported": None, "passed": None, "failed": None,
            "skipped": None}


def evaluate_run(label: str, exit_code: int, output: str) -> tuple[int, dict[str, int | None]]:
    """A command with zero tests, all-skipped/partial skips or bad counts must not PASS.

    The compilation-only S-BUILD is the sole batch without a test-count contract.
    This rejects Python unittest's successful exit code for 'Ran 0 tests'.
    """
    counts = summarize(output)
    if exit_code == 0 and label != "S-BUILD":
        if (counts["tests_reported"] is None or counts["tests_reported"] == 0
                or counts["failed"] is None or counts["failed"] != 0
                or counts["passed"] is None or counts["passed"] == 0
                or counts["skipped"] is None or counts["skipped"] != 0
                or counts["passed"] + counts["failed"] + counts["skipped"] != counts["tests_reported"]):
            return 126, counts  # VALIDATION_NO_TESTS_OR_UNTRUSTWORTHY_SUMMARY
    return exit_code, counts

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", choices=sorted(BATCHES), required=True)
    p.add_argument("--repo", type=Path, required=True,
                   help="Clean disposable clone/worktree root (not production)")
    p.add_argument("--expected-head", required=True,
                   help="Full immutable 40-hex reviewed PR head")
    p.add_argument("--run", action="store_true",
                   help="Actually run offline/build tests in isolated checkout")
    args = p.parse_args()
    repo = args.repo.expanduser().resolve()
    expected = args.expected_head.lower()
    if not re.fullmatch(r"[0-9a-f]{40}", expected):
        p.error("expected-head must be the full SHA1")
    if expected != EXPECTED[args.project]:
        raise RuntimeError("Requested SHA differs from reviewed historical contract."
                           " Update manifest by explicit review, not silently.")
    validate_handoff_manifest(
        Path(__file__).resolve().with_name("HISTORICAL_80_PERCENT_CODEX_JOBS_20261017.json"),
        args.project, expected)
    head = preflight(repo, args.project, expected)
    print(json.dumps({"project": args.project, "head": head,
                      "mode": "RUN" if args.run else "DRY_RUN",
                      "batches": [x[0] for x in BATCHES[args.project]]},
                     ensure_ascii=False))
    if not args.run:
        for label, rel, command in BATCHES[args.project]:
            print(label, "cwd="+rel, "argv="+json.dumps(command))
        return 0
    output_dir = Path(tempfile.mkdtemp(prefix="history-codex-"+args.project+"-"))
    results = []
    for label, rel, command in BATCHES[args.project]:
        cwd = repo / rel
        try:
            done = subprocess.run(command, cwd=cwd, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True,
                                  errors="replace", timeout=1800, check=False,
                                  env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
            rc, stdout = done.returncode, done.stdout
        except (OSError, subprocess.TimeoutExpired) as exc:
            rc, stdout = 125, repr(exc)
        logpath = output_dir / (label + ".log")
        # Write literal UTF-8 bytes: Windows text newline translation would
        # make the receipt digest differ from the on-disk log digest.
        logpath.write_bytes(stdout.encode("utf-8"))
        rc, counts = evaluate_run(label, rc, stdout)
        row = {"batch": label, "exit_code": rc,
               "log_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
               "counts": counts}
        results.append(row)
        print(json.dumps(row))
    receipt = {"schema": 1, "repo_head": head, "project": args.project,
               "source": "local-disposable-codex",
               "results": results,
               "no_live_gold_claim": True, "production_modified": False}
    (output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Local-only logs/receipt:", output_dir)
    print("Review/redact logs before any GitHub comment. Do not upload private fixtures.")
    return 0 if all(r["exit_code"] == 0 for r in results) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeError, OSError, ValueError) as exc:
        print("PRECHECK_BLOCKED:", exc, file=sys.stderr)
        raise SystemExit(2)
