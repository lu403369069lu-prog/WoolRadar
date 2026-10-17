#!/usr/bin/env python3
"""Offline per-family acceptance runner for the frozen 50-family GitHub handoff.

DEFAULT: dry-run only. --run is explicit. No checkout, git writes, installations,
network calls, PR merging, credential reads, production DB access, or GitHub posts.
Run only in a disposable *clean* worktree of the manifest's exact commit SHA.
All failures and skips are recorded as NON-PASS, never silently promoted.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
import platform
from pathlib import Path, PurePosixPath
import re
import shlex
import subprocess
import sys
import tempfile
from typing import Any

PINNED = {
    "wool": ("W", "WoolRadar", "lu403369069lu-prog/WoolRadar",
             "80c5ea18769c1312e5be5fd99a39e4f3d498c64f"),
    "sam": ("S", "YinQieJi-SAM", "lu403369069lu-prog/YinQieJi",
            "82bf36efa90cced8dafb56502812eb49f40515f3"),
    "coord": ("C", "WoolRadar-Coord", "lu403369069lu-prog/WoolRadar",
              "27796df5f9847c1bb5d48d2a445e418dfb3d8e96"),
}
HEX40 = re.compile(r"[a-f0-9]{40}\Z")
TESTPY = re.compile(r"test_[a-zA-Z0-9_-]+\.py\Z")
TESTNODE = re.compile(r"[a-zA-Z0-9_./-]+\.test\.(?:ts|mjs)\Z")
EXPECTED_FAMILIES = 50
EXPECTED_READY = 42
MANIFEST_BLOB_SHA1 = "96c71aad1e26e5bf7b0aa12ac1e4b62ddcb98744"


class Blocked(ValueError):
    pass


def git(repo: Path, *args: str) -> str:
    p = subprocess.run(["git", *args], cwd=repo, text=True, errors="replace",
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    if p.returncode:
        raise Blocked("git preflight blocked (exit %s): %s" %
                      (p.returncode, p.stderr[:160]))
    return p.stdout.strip()


def in_repo(repo: Path, rel: str) -> Path:
    p = PurePosixPath(rel)
    if not rel or p.is_absolute() or ".." in p.parts or "\\" in rel:
        raise Blocked("Unsafe relative path in manifest: %r" % rel)
    full = (repo / rel).resolve()
    if not full.is_relative_to(repo):
        raise Blocked("Path escapes checkout: %r" % rel)
    return full


def safe_checkout(repo: Path, expected: str, project: str) -> None:
    resolved = repo.resolve()
    spelling = str(resolved).replace("/", "\\").casefold().rstrip("\\")
    if (spelling == "c:\\woolradar" or spelling.startswith("c:\\woolradar\\")
            or any(part in {"production", "twincat", "appdata", "sam_local"}
                   for part in (x.casefold() for x in resolved.parts))):
        raise Blocked("Potential production/user-data location; use a disposable clone")
    top = Path(git(resolved, "rev-parse", "--show-toplevel")).resolve()
    if top != resolved:
        raise Blocked("The supplied --repo is not the exact Git worktree root")
    got = git(resolved, "rev-parse", "HEAD")
    if got != expected:
        raise Blocked("Commit mismatch: expected %s, got %s" % (expected, got))
    if git(resolved, "status", "--porcelain"):
        raise Blocked("Dirty checkout: use a clean disposable clone/worktree")
    sentinel = ("SAM/snapshot/package.json" if project == "sam" else
                "coordination/relay.py" if project == "coord" else
                "core/public_corpus.py")
    if not in_repo(resolved, sentinel).is_file():
        raise Blocked("Wrong project: missing " + sentinel)


def validate_command(job: dict[str, Any], repo: Path) -> tuple[str, list[str]]:
    command = job["run_command"]
    if not isinstance(command, str):
        raise Blocked(job["family_id"] + ": missing command")
    args = shlex.split(command, posix=True)
    expected_path = job["verified_test_path"]
    if len(args) == 10 and args[:6] == ["python", "-B", "-m", "unittest", "discover", "-s"]:
        if len(args) != 10 or args[7] != "-p" or args[9] != "-v":
            raise Blocked(job["family_id"] + ": unexpected unittest command shape")
        rel_directory, name = args[6], args[8]
        if not TESTPY.fullmatch(name):
            raise Blocked(job["family_id"] + ": unsafe test pattern")
        target = str(PurePosixPath(rel_directory) / name)
        if target != expected_path:
            raise Blocked(job["family_id"] + ": command targets %s but proof is %s" %
                          (target, expected_path))
        return job["local_cwd"], [sys.executable, *args[1:]]
    if args[:2] == ["node", "--test"] and len(args) == 3:
        relative_test = args[2]
    elif args[:4] == ["node", "--import", "tsx", "--test"] and len(args) == 5:
        relative_test = args[4]
    else:
        raise Blocked(job["family_id"] + ": command not on offline allowlist")
    if not TESTNODE.fullmatch(relative_test):
        raise Blocked(job["family_id"] + ": unsafe Node test path")
    cwd = in_repo(repo, job["local_cwd"])
    target = (cwd / relative_test).resolve()
    expected = in_repo(repo, expected_path)
    if target != expected:
        raise Blocked(job["family_id"] + ": Node command/test path mismatch")
    return job["local_cwd"], args


def load_and_validate(path: Path, project: str, repo: Path) -> list[dict[str, Any]]:
    raw = path.read_bytes()
    # Do not accept a silently edited plan even when its commands stay allowlisted.
    blob_sha1 = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw).hexdigest()
    if blob_sha1 != MANIFEST_BLOB_SHA1:
        raise Blocked("Manifest byte SHA differs from frozen reviewed Git blob")
    manifest = json.loads(raw.decode("utf-8"))
    if manifest.get("total_families") != EXPECTED_FAMILIES:
        raise Blocked("Wrong manifest family denominator")
    if manifest.get("ready_for_local_codex") != EXPECTED_READY:
        raise Blocked("Wrong manifest ready denominator")
    jobs = manifest.get("jobs")
    if not isinstance(jobs, list) or len(jobs) != EXPECTED_FAMILIES:
        raise Blocked("Manifest jobs != 50")
    names = [j.get("family_id") for j in jobs]
    if len(set(names)) != EXPECTED_FAMILIES:
        raise Blocked("Duplicate/invalid family ID")
    if sum(j.get("disposition") == "READY_FOR_LOCAL_CODEX" for j in jobs) != EXPECTED_READY:
        raise Blocked("Ready job count drift")
    for token, (key, _, full_name, head) in PINNED.items():
        v = manifest.get("immutable_refs", {}).get(key, {})
        if v.get("sha") != head or v.get("repo") != full_name:
            raise Blocked("Frozen manifest SHA/repo changed for " + token)
    key, project_name, full_name, sha = PINNED[project]
    selected = []
    for job in jobs:
        family = job["family_id"]
        source_project = next((token for token, (_, p, _, _) in PINNED.items()
                               if p == job.get("project")), None)
        if source_project is None:
            raise Blocked("Unknown family project: %s" % family)
        _, _, owner, expected_sha = PINNED[source_project]
        if job.get("repo") != owner or job.get("required_head_sha") != expected_sha:
            raise Blocked("Family repository / SHA drift: " + family)
        if job.get("disposition") != "READY_FOR_LOCAL_CODEX":
            if job.get("run_command") is not None:
                raise Blocked("External gate carries executable command: " + family)
            continue
        if not job.get("verified_test_path") or not HEX40.fullmatch(str(job.get("verified_test_blob", ""))):
            raise Blocked("Missing exact code/test proof: " + family)
        # Check command-vs-source path for every ready family, even other projects.
        # Actual local blob comparison is only possible on the checked-out project.
        if source_project == project:
            if job["local_cwd"] != manifest["immutable_refs"][key]["cwd"]:
                raise Blocked("Wrong execution CWD: " + family)
            relcwd, argv = validate_command(job, repo)
            path = job["verified_test_path"]
            actual = in_repo(repo, path)
            if not actual.is_file():
                raise Blocked("Test not found on exact head: " + path)
            git_blob = git(repo, "rev-parse", "HEAD:" + path)
            disk_blob = git(repo, "hash-object", "--", path)
            if git_blob != job["verified_test_blob"] or disk_blob != git_blob:
                raise Blocked("Proof blob mismatch for " + family)
            selected.append({"family": family, "batch": job["batch"],
                             "cwd": relcwd, "argv": argv, "proof_blob": git_blob})
    return selected


def counts(text: str) -> dict[str, int | None]:
    # Parse only the last official aggregate, not subtests or arbitrary words.
    node = re.findall(r"(?m)^# tests (\d+)\s*$", text)
    if node:
        def latest(k: str) -> int | None:
            a = re.findall(r"(?m)^# " + k + r" (\d+)\s*$", text)
            return int(a[-1]) if a else None
        return {"tests": int(node[-1]), "passed": latest("pass"),
                "failed": latest("fail"), "skipped": latest("skipped")}
    py = re.findall(r"(?m)^Ran (\d+) tests? in [\d.]+s", text)
    if py:
        total = int(py[-1])
        ok = re.findall(r"(?m)^OK(?:\s*\(skipped=(\d+)\))?\s*$", text)
        failure = re.findall(r"(?m)^FAILED \(([^)]*)\)", text)
        if ok:
            skipped = int(ok[-1]) if ok[-1] else 0
            return {"tests": total, "passed": total - skipped, "failed": 0,
                    "skipped": skipped}
        if failure:
            pieces = dict((k, int(n)) for k, n in
                          re.findall(r"(failures|errors|skipped)=(\d+)", failure[-1]))
            fail = pieces.get("failures", 0) + pieces.get("errors", 0)
            skipped = pieces.get("skipped", 0)
            return {"tests": total, "passed": max(total - fail - skipped, 0),
                    "failed": fail, "skipped": skipped}
    return {"tests": None, "passed": None, "failed": None, "skipped": None}


def verdict(exit_code: int, c: dict[str, int | None]) -> str:
    if exit_code == 125:
        return "EXECUTION_ERROR"
    if exit_code != 0:
        return "TEST_FAILED"
    if c["tests"] is None or c["tests"] == 0:
        return "BLOCKED_ZERO_OR_UNKNOWN_TESTS"
    if c["passed"] is None or c["passed"] == 0:
        return "BLOCKED_ALL_SKIPPED_OR_UNKNOWN_PASS"
    if c["failed"] is None or c["failed"] > 0:
        return "TEST_FAILED_OR_UNPARSEABLE"
    if c["skipped"] is None or c["skipped"] > 0:
        return "PARTIAL_SKIPPED_NOT_ACCEPTED"
    if c["passed"] + c["failed"] + c["skipped"] != c["tests"]:
        return "BLOCKED_COUNT_INCONSISTENCY"
    return "PASS"



def audit_raw_log(raw: bytes, exit_code: int) -> tuple[dict[str, int | None], str]:
    """Validate exact child-output bytes. Malformed UTF-8 cannot prove green."""
    try:
        stat = counts(raw.decode("utf-8"))
    except UnicodeDecodeError:
        return counts(""), "BLOCKED_NON_UTF8_LOG"
    return stat, verdict(exit_code, stat)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", choices=tuple(PINNED), required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--family", action="append", default=[],
                        help="Optional family ID; may be repeated; default all ready in project")
    parser.add_argument("--run", action="store_true",
                        help="Explicitly run offline tests in disposable checkout")
    args = parser.parse_args()
    repo = args.repo.expanduser().resolve()
    expected = PINNED[args.project][3]
    safe_checkout(repo, expected, args.project)
    entries = load_and_validate(args.manifest, args.project, repo)
    if args.family:
        unknown = set(args.family) - {e["family"] for e in entries}
        if unknown:
            raise Blocked("Selected families are not ready in project: " +
                          ",".join(sorted(unknown)))
        entries = [e for e in entries if e["family"] in set(args.family)]
    if not entries:
        raise Blocked("No verifiable ready tasks in selected project")
    unique: dict[tuple[str, tuple[str, ...]], list[str]] = {}
    for e in entries:
        unique.setdefault((e["cwd"], tuple(e["argv"])), []).append(e["family"])
    plan = [{"families": ids, "cwd": cwd, "argv": list(cmd)}
            for (cwd, cmd), ids in unique.items()]
    print(json.dumps({"mode": "RUN" if args.run else "DRY_RUN", "project": args.project,
                      "head": expected, "ready_families": len(entries),
                      "unique_test_commands": len(plan), "plan": plan},
                     ensure_ascii=False))
    if not args.run:
        return 0
    output = Path(tempfile.mkdtemp(prefix="codex-history-manifest-"))
    # Redirect ordinary user-profile/temp resolution away from the host profile.
    scratch_home = output / "home"
    scratch_temp = output / "temp"
    scratch_home.mkdir()
    scratch_temp.mkdir()
    scrub = re.compile(r"(TOKEN|PASSWORD|SECRET|API_KEY|CREDENTIAL|AUTH|COOKIE|PRIVATE)", re.I)
    child_env = {k: v for k, v in os.environ.items() if not scrub.search(k)}
    child_env.update({"HOME": str(scratch_home), "USERPROFILE": str(scratch_home),
                      "APPDATA": str(scratch_home / "AppData"),
                      "LOCALAPPDATA": str(scratch_home / "LocalAppData"),
                      "TMP": str(scratch_temp), "TEMP": str(scratch_temp),
                      "TMPDIR": str(scratch_temp), "PYTHONDONTWRITEBYTECODE": "1",
                      # Avoid locale-specific Windows cp936/cp1252 stderr encoding.
                      "PYTHONIOENCODING": "utf-8"})
    child_env.pop("NODE_OPTIONS", None)
    runtime = {"python": sys.version.split()[0], "platform": platform.platform(),
               "os": os.name, "node": None}
    if args.project == "sam":
        try:
            runtime["node"] = subprocess.run(["node", "--version"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, timeout=10, env=child_env).stdout.strip()
        except (OSError, subprocess.TimeoutExpired):
            runtime["node"] = "NOT_AVAILABLE"
    receipts = []
    for i, item in enumerate(plan, 1):
        rc = 125
        raw = b""
        try:
            proc = subprocess.run(item["argv"], cwd=in_repo(repo, item["cwd"]),
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  timeout=900, env=child_env)
            rc, raw = proc.returncode, proc.stdout
        except (OSError, subprocess.TimeoutExpired) as exc:
            raw = ("%s: %s" % (type(exc).__name__, exc)).encode("utf-8")
        # Logs/digests describe the child's original bytes, never replacements.
        logname = "test-%03d.log" % i
        (output / logname).write_bytes(raw)
        stat, status = audit_raw_log(raw, rc)
        row = {"family_ids": item["families"], "cwd": item["cwd"],
               "argv": item["argv"], "exit_code": rc, "counts": stat,
               "status": status, "sha256": hashlib.sha256(raw).hexdigest(),
               "local_log": logname}
        receipts.append(row)
        print(json.dumps(row, ensure_ascii=False))
    receipt = {"schema_version": 1, "source": "disposable-local-codex",
               "created_at_utc": datetime.now(timezone.utc).isoformat(),
               "repo_sha": expected, "project": args.project,
               "runtime": runtime,
               "tested_families": len(entries), "unique_commands": len(plan),
               "results": receipts, "no_real_gold_claim": True,
               "production_modified": False}
    (output / "receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print("RECEIPT_DIRECTORY:", output)
    print("Review/redact local logs before linking a GitHub Issue; never auto-upload.")
    return 0 if all(x["status"] == "PASS" for x in receipts) else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Blocked, OSError, ValueError, subprocess.SubprocessError) as err:
        print("PRECHECK_BLOCKED:", err, file=sys.stderr)
        raise SystemExit(2)
