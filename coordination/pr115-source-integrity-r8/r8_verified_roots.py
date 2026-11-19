#!/usr/bin/env python3
"""Review-only WoolRadar test gate for its actual tracked source test roots.

This is an isolated candidate, not a replacement production or hosted CI gate.
"""
import argparse
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys

TEST_SUITES = (
    ("relay", ".github/relay", ".github/relay"),
    ("coordination-integrity", "coordination", "coordination"),
    ("original-coordination", "coordination/original-tests", None),
)
# Counts belong to this frozen PR113 source SHA only. A partial test run must
# not masquerade as complete even if unittest itself exits successfully.
EXPECTED_COUNTS = {"relay": 72, "coordination-integrity": 4,
                   "original-coordination": 48}
ALLOWED_ENV = {
    "APPDATA", "COMSPEC", "HOME", "HOMEDRIVE", "HOMEPATH", "LANG",
    "LC_ALL", "LC_CTYPE", "LOCALAPPDATA", "PATH", "PATHEXT", "SYSTEMROOT",
    "TEMP", "TMP", "TMPDIR", "TZ", "USERPROFILE", "WINDIR",
}


def run(source: Path, expected_sha: str, diagnostic_no_isolation: bool = False) -> dict:
    source = source.resolve()
    report = {"schema_version": 1, "diagnostic_no_isolation": diagnostic_no_isolation,
              "source_head": None,
              "checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "business_acceptance": False, "status": "BLOCKED", "suites": []}
    if not source.is_dir():
        report["error_kind"] = "INVALID_SOURCE_ROOT"
        return report
    if not re.fullmatch(r"[0-9a-f]{40}", expected_sha):
        report["error_kind"] = "INVALID_EXPECTED_SHA"
        return report
    env = {k: v for k, v in os.environ.items() if k.upper() in ALLOWED_ENV}
    # Isolated fixtures require byte-exact LF on Windows; enforce at git child level.
    env.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.autocrlf",
                "GIT_CONFIG_VALUE_0": "false"})
    def clean_source():
        head = subprocess.run(["git", "-C", str(source), "rev-parse", "HEAD"],
                              capture_output=True, text=True, env=env, timeout=15)
        status = subprocess.run(["git", "-C", str(source), "status", "--porcelain",
                                 "--untracked-files=all"], capture_output=True, text=True,
                                env=env, timeout=15)
        # status/diff trust index bits. Reject assume-unchanged, skip-worktree,
        # and fsmonitor-valid entries even when their present bytes are clean.
        # NUL delimiters avoid misreading filenames containing whitespace.
        for flag in ("-v", "-f"):
            index = subprocess.run(["git", "-C", str(source), "ls-files", flag, "-z"],
                                   capture_output=True, env=env, timeout=15)
            if (index.returncode != 0 or not index.stdout or
                    any(not row.startswith(b"H ") for row in index.stdout.split(b"\0") if row)):
                return False
        return (head.returncode == 0 and head.stdout.strip() == expected_sha
                and status.returncode == 0 and not status.stdout.strip())
    try:
        if not clean_source():
            report["error_kind"] = "SOURCE_SHA_OR_DIRTY_CHECKOUT"
            return report
    except (OSError, subprocess.TimeoutExpired):
        report["error_kind"] = "SOURCE_IDENTITY_CHECK_UNAVAILABLE"
        return report
    report["source_head"] = expected_sha

    # The original coordination suite contains a frozen eleven-file manifest.
    manifest_check = subprocess.run(
        [sys.executable, "-I", "-B", "-X", "utf8",
         str(source / "coordination" / "verify_original_suite.py")],
        cwd=source, env=env, capture_output=True, text=True, errors="replace",
        timeout=30)
    if (manifest_check.returncode != 0 or
            '"verified_original_files": 11' not in manifest_check.stdout):
        report["error_kind"] = "ORIGINAL_SUITE_MANIFEST_INVALID"
        return report

    for name, start, top in TEST_SUITES:
        if not clean_source():
            report["error_kind"] = "SOURCE_CHANGED_BEFORE_SUITE"
            return report
        start_dir = source / start
        top_dir = source / (top or start)
        item = {"suite": name, "status": "BLOCKED", "total": None, "exit_code": None}
        report["suites"].append(item)
        if (not start_dir.is_dir() or start_dir.is_symlink()
                or not start_dir.resolve().is_relative_to(source)
                or not top_dir.is_dir() or top_dir.is_symlink()
                or not top_dir.resolve().is_relative_to(source)
                or not list(start_dir.glob("test_*.py"))):
            item["error_kind"] = "INVALID_TEST_DISCOVERY_ROOT"
            return report

        # Explicit UTF-8 is needed for Git stdout containing this Windows
        # checkout's non-ASCII path.  -I alone uses the host's GBK locale.
        cmd = [sys.executable, *([] if diagnostic_no_isolation else ["-I"]),
               "-B", "-X", "utf8"]
        if top is None:
            # unittest discover cannot import the hyphenated original-tests
            # directory as a dotted module with -t root.  Use reviewed files
            # as top-level modules and explicitly seed the checked-out root.
            script = ("import sys,unittest; from pathlib import Path; "
                      f"root=Path({str(source)!r}); sys.path.insert(0,str(root)); "
                      "suite=unittest.TestLoader().discover(str(root/'coordination/original-tests'),pattern='test_*.py'); "
                      "result=unittest.TextTestRunner(verbosity=2).run(suite); "
                      "sys.exit(0 if result.wasSuccessful() else 1)")
            cmd += ["-c", script]
        else:
            cmd += ["-m", "unittest", "discover", "-s", str(start_dir),
                    "-t", str(top_dir), "-p", "test_*.py", "-v"]
        try:
            proc = subprocess.run(cmd, cwd=source, env=env, capture_output=True,
                                  text=True, errors="replace", timeout=180)
        except (OSError, subprocess.TimeoutExpired) as exc:
            item["error_kind"] = type(exc).__name__
            return report
        output = (proc.stdout + "\n" + proc.stderr)[-100000:]
        matches = list(re.finditer(r"(?m)^Ran (\d+) tests? in ", proc.stderr))
        count = int(matches[-1].group(1)) if matches else None
        # A successful subprocess with skipped/expected-failed tests does not
        # satisfy a complete source acceptance gate.  Require one summary.
        ok = (proc.returncode == 0 and len(matches) == 1
              and count == EXPECTED_COUNTS[name]
              and re.search(r"(?m)^Ran \d+ tests? in [^\r\n]+\r?\n"
                                       r"\s*OK\s*\Z", proc.stderr) is not None)
        item.update({"status": "PASS" if ok else "FAIL",
                     "total": count, "exit_code": proc.returncode})
        if not ok:
            # Debug output remains local and is intentionally excluded from published evidence.
            (Path(__file__).resolve().parent / f"{name}-{'unisolated-' if diagnostic_no_isolation else ''}local-debug.log").write_text(
                output, encoding="utf-8")
            report["status"] = "FAIL"
            report["error_kind"] = "TEST_EXECUTION_OR_SUMMARY_FAILED"
            return report

    report["status"] = "PASS"
    report["total"] = sum(s["total"] for s in report["suites"])
    if not clean_source():
        report["status"] = "BLOCKED"
        report["error_kind"] = "SOURCE_CHANGED_DURING_TEST"
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--diagnostic-no-isolation", action="store_true")
    args = parser.parse_args()
    result = run(args.source, args.expected_sha, args.diagnostic_no_isolation)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "total": result.get("total"),
                      "suites": result["suites"]}, ensure_ascii=False))
    # Exit zero only if all intended suites are present and passed.
    raise SystemExit(0 if result["status"] == "PASS" else 1)
