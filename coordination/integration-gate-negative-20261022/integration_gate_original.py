#!/usr/bin/env python3
"""Read-only original-source integration gate; persists bounded evidence, never accepts business work."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from worker import parse_test_summary

def run(args):
    root = Path(args.source).resolve()
    if args.repo == "WoolRadar":
        cwd = root
        (cwd / ".test-tmp").mkdir(exist_ok=True)
        cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
    else:
        cwd = root / "SAM" / "snapshot"
        cmd = ["npm", "test"]
    if not cwd.is_dir() or not cwd.is_relative_to(root):
        raise RuntimeError("invalid integration source checkout")
    env = dict(os.environ)
    for key in ("GITHUB_TOKEN", "GH_TOKEN", "COPILOT_GITHUB_TOKEN", "OPENAI_API_KEY"):
        env.pop(key, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    base = {
        "schema_version": 1, "repo": args.repo,
        "command": cmd, "source_subdir": "." if args.repo == "WoolRadar" else "SAM/snapshot",
        "verified_business_complete": False,
        "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat()
    }
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True,
                              text=True, errors="replace", timeout=600, check=False)
        output = (proc.stdout + "\n" + proc.stderr)[-400000:]
        summary = parse_test_summary(output, proc.returncode)
        failure_names = []
        if summary["status"] != "PASS":
            for line in output.splitlines():
                if line.startswith(("not ok ", "FAIL: ", "ERROR: ")):
                    failure_names.append(re.sub(r"[^a-zA-Z0-9 _.:#()\-]", "?", line)[:150])

        details = []
        active = None
        for line in output.splitlines():
            if line.startswith("not ok "):
                if active is not None:
                    details.append(active)
                active = {"test": re.sub(r"[^a-zA-Z0-9 _.:#()\-]", "?", line)[:160],
                          "signals": []}
            elif active is not None and len(active["signals"]) < 7:
                trimmed = line.strip()
                if trimmed.startswith(("error:", "code:", "name:", "expected:",
                                        "actual:", "failureType:", "location:")):
                    safe = re.sub(r"[^a-zA-Z0-9 _.:#()\-]", "?", trimmed)[:200]
                    active["signals"].append(safe)
        if active is not None:
            details.append(active)
        base.update({**summary, "failed_test_names": failure_names[:30],
                     "failure_details": details[:30]})
    except (OSError, subprocess.TimeoutExpired) as exc:
        base.update({"status": "BLOCKED", "error_kind": type(exc).__name__})
    dest = Path(args.output)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(base, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"integration": base["status"], "test_count": base.get("total"),
                      "pass": base.get("passed"), "failed": base.get("failed"),
                      "command": cmd}), flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, choices=["WoolRadar", "YinQieJi"])
    parser.add_argument("--source", default="candidate")
    parser.add_argument("--output", default=".relay-report/integration.json")
    run(parser.parse_args())
