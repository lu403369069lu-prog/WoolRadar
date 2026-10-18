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
        matches = re.findall(r"Ran (\d+) tests?", output)
        node_total = re.findall(r"(?m)^# tests (\d+)\s*$", output)
        node_pass = re.findall(r"(?m)^# pass (\d+)\s*$", output)
        node_fail = re.findall(r"(?m)^# fail (\d+)\s*$", output)
        total = int(matches[-1]) if matches else int(node_total[-1]) if node_total else None
        passed = int(node_pass[-1]) if node_pass else total if proc.returncode == 0 else None
        failures = int(node_fail[-1]) if node_fail else None
        failure_names = []
        if proc.returncode != 0:
            for line in output.splitlines():
                if line.startswith(("not ok ", "FAIL: ", "ERROR: ")):
                    failure_names.append(re.sub(r"[^a-zA-Z0-9 _.:#()\-]", "?", line)[:150])
        ok = proc.returncode == 0 and total is not None and total > 0 and failures in (None, 0)
        base.update({"status": "PASS" if ok else "FAIL", "exit_code": proc.returncode,
                     "total": total, "passed": passed, "failed": failures,
                     "failed_test_names": failure_names[:30]})
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
