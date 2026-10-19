#!/usr/bin/env python3
"""Run the real WoolRadar combined suite and reject successful-but-skipped runs.

This is an isolated CI gate only; it never marks a business family accepted.
"""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import sys

from worker import parse_test_summary, source_sha


def strict_summary(output, returncode):
    result = parse_test_summary(output, returncode)
    complete = (
        result["status"] == "PASS"
        and type(returncode) is int and returncode == 0
        and type(result.get("total")) is int and result["total"] > 0
        and type(result.get("passed")) is int
        and result["passed"] == result["total"]
        and all(type(result.get(k)) is int and result[k] == 0
                for k in ("skipped", "todo", "cancelled"))
    )
    return {**result, "status": "PASS" if complete else "FAIL"}


def run(source, expected_sha, report):
    root = source.resolve(strict=True)
    actual = source_sha(root)
    if actual != expected_sha:
        raise ValueError("COMBINED_SOURCE_SHA_MISMATCH")
    script = root / "independent-quality" / "delivery-bridge-20261016" / "run_combined_tests.py"
    if not script.is_file():
        raise FileNotFoundError("reviewed combined test runner missing")
    env = os.environ.copy()
    for key in ("GITHUB_TOKEN", "GH_TOKEN", "COPILOT_GITHUB_TOKEN", "OPENAI_API_KEY"):
        env.pop(key, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    command = [sys.executable, "-B", "-X", "utf8", str(script)]
    result = {"schema_version": 1, "repo": "WoolRadar", "source_commit": actual,
              "run_key": os.getenv("GITHUB_RUN_ID", "0") + "/" + os.getenv("GITHUB_RUN_ATTEMPT", "1"),
              "command": command, "verified_business_complete": False,
              "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
    try:
        proc = subprocess.run(command, cwd=root, env=env, capture_output=True,
                              encoding="utf-8", errors="strict", timeout=600, check=False)
        sys.stdout.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        result.update(strict_summary(proc.stdout + "\n" + proc.stderr, proc.returncode))
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as exc:
        result.update({"status": "BLOCKED", "error_kind": type(exc).__name__})
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"combined_gate": result["status"], "source_commit": actual,
                      "total": result.get("total"), "passed": result.get("passed"),
                      "skipped": result.get("skipped"), "runner_exit": result.get("exit_code")}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--report", type=Path, required=True)
    a = parser.parse_args()
    raise SystemExit(run(a.source, a.expected_sha, a.report))
