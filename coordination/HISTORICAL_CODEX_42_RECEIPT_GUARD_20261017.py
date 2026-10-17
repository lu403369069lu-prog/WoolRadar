#!/usr/bin/env python3
"""Validate 42-family frozen offline Codex receipts; never certify production.

Separate from HISTORICAL_CODEX_RECEIPT_GUARD_20261017.py (legacy broad batches).
Fails closed on missing/duplicate families, skipped tests, raw log mismatch,
wrong SHA, unapproved argv, or logs without actual counted tests.
"""
from __future__ import annotations

import argparse
from hashlib import sha1, sha256
import json
from pathlib import Path
import re
import shlex
from typing import Any

HEADS = {"wool": "80c5ea18769c1312e5be5fd99a39e4f3d498c64f",
         "sam": "82bf36efa90cced8dafb56502812eb49f40515f3",
         "coord": "27796df5f9847c1bb5d48d2a445e418dfb3d8e96"}
PROJECT_NAMES = {"wool": "WoolRadar", "sam": "YinQieJi-SAM",
                 "coord": "WoolRadar-Coord"}
MANIFEST_GIT_BLOB = "96c71aad1e26e5bf7b0aa12ac1e4b62ddcb98744"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
LOGNAME = re.compile(r"test-\d{3}\.log\Z")
PYTHON_NAME = re.compile(r"python(?:\d+(?:\.\d+)?)?(?:\.exe)?\Z", re.I)


def git_blob_sha1(payload: bytes) -> str:
    return sha1(b"blob " + str(len(payload)).encode("ascii") + b"\x00" + payload).hexdigest()


def load_verified_manifest(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    if git_blob_sha1(payload) != MANIFEST_GIT_BLOB:
        raise ValueError("WRONG_IMMUTABLE_MANIFEST_BLOB")
    obj = json.loads(payload.decode("utf-8"))
    jobs = obj.get("jobs")
    if (not isinstance(jobs, list) or len(jobs) != 50
            or obj.get("total_families") != 50
            or obj.get("ready_for_local_codex") != 42):
        raise ValueError("WRONG_HISTORICAL_JOB_DENOMINATOR")
    if len({j.get("family_id") for j in jobs}) != 50:
        raise ValueError("DUPLICATE_MANIFEST_FAMILIES")
    if sum(j.get("disposition") == "READY_FOR_LOCAL_CODEX" for j in jobs) != 42:
        raise ValueError("WRONG_READY_JOB_COUNT")
    for project, key in (("wool", "W"), ("sam", "S"), ("coord", "C")):
        if obj.get("immutable_refs", {}).get(key, {}).get("sha") != HEADS[project]:
            raise ValueError("IMMUTABLE_HEAD_DRIFT")
    return obj


def command_key(cwd: str, args: list[str]) -> tuple[str, tuple[str, ...]]:
    if not isinstance(args, list) or not args or not all(isinstance(a, str) for a in args):
        raise ValueError("MALFORMED_ARGV")
    if args[0] == "node":
        if (args[:2] != ["node", "--test"]
                and args[:4] != ["node", "--import", "tsx", "--test"]):
            raise ValueError("UNAPPROVED_NODE_COMMAND")
        return (cwd, tuple(args))
    basename = args[0].replace("\\", "/").split("/")[-1]
    if not PYTHON_NAME.fullmatch(basename) or args[1:5] != ["-B", "-m", "unittest", "discover"]:
        raise ValueError("UNAPPROVED_PYTHON_COMMAND")
    return (cwd, tuple(["python", *args[1:]]))


def expected_commands(manifest: dict[str, Any], project: str) -> dict[tuple[str, tuple[str, ...]], set[str]]:
    out: dict[tuple[str, tuple[str, ...]], set[str]] = {}
    for job in manifest["jobs"]:
        if (job.get("project") != PROJECT_NAMES[project]
                or job.get("disposition") != "READY_FOR_LOCAL_CODEX"):
            continue
        raw = job["run_command"]
        expected = command_key(job["local_cwd"], shlex.split(raw))
        out.setdefault(expected, set()).add(job["family_id"])
    return out


def parse_actual_log_counts(raw: bytes) -> dict[str, int] | None:
    """Read the actual aggregate, never trust receipt counts alone."""
    try:
        output = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None
    node_tests = re.findall(r"(?m)^# tests (\d+)[ \t]*$", output)
    py_tests = re.findall(r"(?m)^Ran (\d+) tests? in [\d.]+s[ \t]*$", output)
    # Never pick the last green summary after an earlier failed/skipped suite;
    # one subprocess must present exactly ONE unambiguous framework aggregate.
    if node_tests and py_tests:
        return None
    if len(node_tests) == 1:
        fields: dict[str, int] = {"tests": int(node_tests[0])}
        for field, keyword in (("passed", "pass"), ("failed", "fail"),
                               ("skipped", "skipped")):
            hits = re.findall(r"(?m)^# " + keyword + r" (\d+)[ \t]*$", output)
            if len(hits) != 1:
                return None
            fields[field] = int(hits[0])
        return fields
    if node_tests:
        return None
    if len(py_tests) == 1:
        total = int(py_tests[0])
        ok = re.findall(r"(?m)^OK(?:[ \t]*\(skipped=(\d+)\))?[ \t]*$", output)
        failed = re.findall(r"(?m)^FAILED \(([^)]*)\)[ \t]*$", output)
        if len(ok) + len(failed) != 1:
            return None
        if failed:
            kv = {k: int(v) for k, v in
                  re.findall(r"(failures|errors|skipped)=(\d+)", failed[0])}
            bad = kv.get("failures", 0) + kv.get("errors", 0)
            skip = kv.get("skipped", 0)
            return {"tests": total, "passed": max(0, total - bad - skip),
                    "failed": bad, "skipped": skip}
        skip = int(ok[0]) if ok[0] else 0
        return {"tests": total, "passed": total - skip,
                "failed": 0, "skipped": skip}
    return None


def review(data: dict[str, Any], manifest: dict[str, Any], logdir: Path | None) -> dict[str, Any]:
    errors: list[str] = []
    project = data.get("project")
    if not isinstance(project, str):
        project = None
    expected = expected_commands(manifest, project) if project in HEADS else {}
    if project not in HEADS:
        errors.append("UNKNOWN_PROJECT")
    elif data.get("repo_sha") != HEADS[project]:
        errors.append("HEAD_MISMATCH")
    if data.get("schema_version") != 1 or data.get("source") != "disposable-local-codex":
        errors.append("UNTRUSTED_PROVENANCE")
    if data.get("no_real_gold_claim") is not True:
        errors.append("UNSAFE_REAL_GOLD_CLAIM")
    if data.get("production_modified") is not False:
        errors.append("UNSAFE_PRODUCTION_STATE")
    runtime = data.get("runtime")
    if (not isinstance(runtime, dict) or not isinstance(runtime.get("python"), str)
            or not isinstance(runtime.get("platform"), str)):
        errors.append("MISSING_RUNTIME")
    if project == "sam" and (not isinstance(runtime, dict)
                             or not isinstance(runtime.get("node"), str)
                             or not runtime["node"].startswith("v")):
        errors.append("MISSING_NODE_VERSION")
    if logdir is None:
        errors.append("NO_LOG_DIRECTORY")
    results = data.get("results")
    if not isinstance(results, list):
        results = []
        errors.append("INVALID_RESULTS")
    if data.get("unique_commands") != len(results):
        errors.append("COMMAND_COUNT_MISMATCH")
    seen: set[tuple[str, tuple[str, ...]]] = set()
    seen_family: set[str] = set()
    seen_logs: set[str] = set()
    for row in results:
        if not isinstance(row, dict):
            errors.append("MALFORMED_ROW")
            continue
        family_ids = row.get("family_ids")
        if (not isinstance(family_ids, list) or not family_ids
                or any(not isinstance(x, str) for x in family_ids)
                or len(set(family_ids)) != len(family_ids)):
            errors.append("MALFORMED_FAMILIES")
            continue
        if any(x in seen_family for x in family_ids):
            errors.append("DUPLICATE_FAMILY")
        seen_family.update(family_ids)
        try:
            key = command_key(row.get("cwd"), row.get("argv"))
            if key in seen:
                errors.append("DUPLICATE_COMMAND")
            seen.add(key)
            if key not in expected:
                errors.append("UNEXPECTED_COMMAND")
            elif set(family_ids) != expected[key]:
                errors.append("FAMILY_COMMAND_MISMATCH")
        except (ValueError, TypeError):
            errors.append("INVALID_COMMAND")
        filename = row.get("local_log")
        if not isinstance(filename, str) or not LOGNAME.fullmatch(filename):
            errors.append("UNSAFE_LOG_FILENAME")
        elif filename in seen_logs:
            errors.append("DUPLICATE_LOG_FILENAME")
        else:
            seen_logs.add(filename)
            if logdir is not None:
                try:
                    logpath = logdir / filename
                    if (logpath.is_symlink() or
                            not logpath.resolve().is_relative_to(logdir.resolve())):
                        errors.append("UNSAFE_LOG_SYMLINK_OR_ESCAPE")
                    else:
                        contents = logpath.read_bytes()
                        if sha256(contents).hexdigest() != row.get("sha256"):
                            errors.append("LOG_SHA256_MISMATCH")
                        actual_counts = parse_actual_log_counts(contents)
                        if actual_counts is None:
                            errors.append("LOG_HAS_NO_GENUINE_TEST_SUMMARY")
                        elif actual_counts != row.get("counts"):
                            errors.append("LOG_COUNTS_DISAGREE_WITH_RECEIPT")
                except (OSError, ValueError):
                    errors.append("MISSING_RAW_LOG")
        if not isinstance(row.get("sha256"), str) or not HEX64.fullmatch(row["sha256"]):
            errors.append("INVALID_LOG_SHA256")
        if isinstance(row.get("exit_code"), bool) or row.get("exit_code") != 0:
            errors.append("NONZERO_EXIT")
        if row.get("status") != "PASS":
            errors.append("NONPASS_OR_PARTIAL_STATUS")
        c = row.get("counts")
        if not isinstance(c, dict):
            errors.append("MISSING_COUNTS")
        else:
            vals = [c.get(k) for k in ("tests", "passed", "failed", "skipped")]
            if any(not isinstance(v, int) or isinstance(v, bool) for v in vals):
                errors.append("UNPARSEABLE_COUNTS")
            else:
                total, passed, failed, skipped = vals
                if total <= 0 or passed <= 0 or failed != 0 or skipped != 0:
                    errors.append("NO_COMPLETE_GREEN_TESTS")
                if passed + failed + skipped != total:
                    errors.append("INCONSISTENT_COUNTS")
    all_expected = set().union(*expected.values()) if expected else set()
    if seen_family != all_expected:
        errors.append("INCOMPLETE_FAMILY_COVERAGE")
    if seen != set(expected):
        errors.append("INCOMPLETE_COMMAND_COVERAGE")
    if data.get("tested_families") != len(all_expected):
        errors.append("FAMILY_COUNT_MISMATCH")
    return {
        "project": project,
        "head": data.get("repo_sha"),
        "families_expected": len(all_expected),
        "families_claimed": len(seen_family),
        "unique_commands_expected": len(expected),
        "unique_commands_claimed": len(seen),
        "local_full_family_receipt_accepted": len(errors) == 0,
        "errors": sorted(set(errors)),
        "business_gold_accepted": False,
        "historical_recovery_closed": False,
        "windows_node24_and_26_both_verified": False,
        "safe_next_action": "Review redacted per-family results and all platform/real-gold gates; never auto merge."
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    args = p.parse_args()
    manifest = load_verified_manifest(args.manifest)
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    result = review(receipt, manifest, args.receipt.parent)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["local_full_family_receipt_accepted"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
