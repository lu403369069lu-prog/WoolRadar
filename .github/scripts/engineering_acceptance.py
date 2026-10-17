#!/usr/bin/env python3
"""Read-only, fail-closed engineering checkpoint. Never self-commits or merges."""
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path.cwd()
OUT = ROOT / ".engineering-acceptance"
OUT.mkdir(exist_ok=True)
REPO = os.environ.get("GITHUB_REPOSITORY", "")
IS_SAM = REPO.endswith("/YinQieJi") or (ROOT / "SAM/snapshot").is_dir()
GROUPS = {
    "SAM-H17": [
        ["node", "--test", "tools/atomic-write.test.mjs", "tools/build-release-manifest.synthetic.test.mjs", "tools/migrate-release-041.synthetic.test.mjs"],
    ],
    "SAM-H14": [
        ["node", "--test", "../independent-review/20261016-0904-audit-coverage/holdout_identity_check.test.mjs", "../independent-review/20261016-0904-audit-coverage/holdout_identity_cli.test.mjs"],
    ],
    "SAM-H05-H19": [
        ["npm", "run", "build"],
        ["npm", "test"],
    ],
} if IS_SAM else {
    "WR-H07-H08": [
        [sys.executable, "-m", "unittest", "discover", "-s", "independent-quality/public-corpus-blind-dedup-20261016", "-p", "test_*.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_public_corpus*.py"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_public_sample*.py"],
    ]
}
cwd = ROOT / "SAM/snapshot" if IS_SAM else ROOT
if not IS_SAM:
    (ROOT / ".test-tmp").mkdir(exist_ok=True)
records = {}
for group, commands in GROUPS.items():
    tests = []
    for i, command in enumerate(commands):
        logname = group + "-" + str(i) + ".log"
        try:
            proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=480, check=False)
            status = "PASS" if proc.returncode == 0 else "FAIL"
            (OUT / logname).write_text(proc.stdout[-150000:] + "\n--- stderr ---\n" + proc.stderr[-150000:], encoding="utf-8")
            tests.append({"command": command, "status": status, "exit_code": proc.returncode, "log": logname})
        except (OSError, subprocess.TimeoutExpired) as exc:
            (OUT / logname).write_text(str(exc), encoding="utf-8")
            tests.append({"command": command, "status": "BLOCKED", "log": logname})
    records[group] = {
        "checks": tests,
        "status": "PARTIAL_NEEDS_NATIVE_AND_BUSINESS_GATES" if all(x["status"] == "PASS" for x in tests) else "BLOCKED_OR_FAILED",
        "strictly_complete": False
    }
receipt = {
    "schema_version": 1,
    "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "repository": REPO,
    "commit": os.environ.get("GITHUB_SHA"),
    "run_id": os.environ.get("GITHUB_RUN_ID"),
    "groups": records,
    "policy": "Passing CI does not prove production, Windows, frozen corpus or business acceptance. No auto-merge."
}
(OUT / "checkpoint.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({k: v["status"] for k,v in records.items()}))
sys.exit(0 if all(all(c["status"] == "PASS" for c in v["checks"]) for v in records.values()) else 1)
