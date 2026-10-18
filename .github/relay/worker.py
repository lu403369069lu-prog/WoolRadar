#!/usr/bin/env python3
"""Bounded read-only tests + replay-safe durable checkpoints. Never auto-accept."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def save(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")

def queue_digest(queue):
    """Cross-platform canonical hash; Git checkout CRLF/LF must not change identity."""
    canonical = json.dumps(queue, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def source_sha(path):
    s = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True, timeout=10).strip()
    if not re.fullmatch(r"[a-f0-9]{40}", s):
        raise ValueError("invalid commit SHA")
    return s

def safe(argv):
    if not isinstance(argv, list) or len(argv) < 3 or not all(isinstance(a, str) for a in argv):
        return False
    if any(len(a) > 230 or re.search(r"[\x00-\x1f;$|&<>\x60]", a) for a in argv):
        return False
    if argv[:5] == ["python", "-m", "unittest", "discover", "-s"]:
        # Pin reviewed (discovery root, filename pattern) pairs; no arbitrary -s.
        allowed = {
            ("independent-quality/public-corpus-blind-dedup-20261016", "test_*.py"),
            ("tests", "test_apply_evidence_transaction.py"),
            ("tests", "test_developer_grant_negations.py"),
            ("tests", "test_developer_grant_project_scope.py"),
            ("tests", "test_notifications.py"),
            ("tests", "test_official_trace_stale_event.py"),
            ("tests", "test_official_trace.py"),
            ("tests", "test_public_corpus_dns_label_boundary_20261018.py"),
            ("tests", "test_public_corpus_identity.py"),
            ("tests", "test_public_corpus_timestamp.py"),
            ("tests", "test_public_corpus*.py"),
            ("tests", "test_public_sample*.py"),
            ("tests", "test_reindex_notification_collision.py"),
            ("tests", "test_reindex_snapshot.py"),
            ("tests", "test_reindex_upsert_serialization.py"),
        }
        return len(argv) == 8 and argv[6] == "-p" and (argv[5], argv[7]) in allowed
    if argv[:4] == ["node", "--import", "tsx", "--test"]:
        return len(argv) >= 5 and all(a.startswith("test/") and a.endswith(".test.ts") and ".." not in a for a in argv[4:])
    if argv[:2] == ["node", "--test"]:
        # WoolRadar historical families contain no approved Node fixtures.
        # Never allow arbitrary relative .test.mjs from a future queue edit.
        return False
    return False

def choose_recheck(state, families, regular_ids):
    """Prefer oldest independently failed subset, at most once per two revisions."""
    candidates = []
    for item in families:
        family_id = item["id"]
        prev = state.get("families", {}).get(family_id, {})
        if (family_id in regular_ids or not item["checks"]
                or item["disposition"] == "EXTERNAL_OR_POLICY_GATED"
                or prev.get("status") != "FORMAL_CHECK_FAILED_OR_BLOCKED"):
            continue
        last = prev.get("last_recheck_revision", -1000)
        if not isinstance(last, int) or state["revision"] - last < 2:
            continue
        candidates.append((last, family_id, item))
    return min(candidates)[2] if candidates else None


def parse_test_summary(output, exit_code):
    """An all-skipped or TODO-only test run is NOT formal evidence."""
    node_totals = re.findall(r"(?m)^# tests (\d+)\s*$", output)
    python_totals = re.findall(r"(?m)^Ran (\d+) tests?", output)
    if node_totals:
        total = int(node_totals[-1])
        def node_count(key):
            matches = re.findall(r"(?m)^# " + key + r" (\d+)\s*$", output)
            return int(matches[-1]) if matches else None
        passed = node_count("pass")
        failed = node_count("fail")
        skipped = node_count("skipped")
        todo = node_count("todo")
        cancelled = node_count("cancelled")
        # Node 22 reports each category. Missing/truncated summaries fail closed.
        complete = all(type(x) is int for x in (passed, failed, skipped, todo, cancelled))
        ok = (exit_code == 0 and total > 0 and complete and passed == total
              and failed == 0 and skipped == 0 and todo == 0 and cancelled == 0)
    elif python_totals:
        total = int(python_totals[-1])
        skipped_matches = re.findall(r"\\bskipped=(\\d+)\\b", output)
        skipped = int(skipped_matches[-1]) if skipped_matches else 0
        # unittest can exit 0 for @expectedFailure, whose terminal summary
        # is "OK (expected failures=1)". A test run without any genuine OK
        # marker can also exit 0. Neither is accepted as formal evidence.
        # Ambiguous multiple summaries fail closed instead of selecting one.
        ok_markers = [
            line.strip() for line in output.splitlines()
            if re.fullmatch(r"OK(?: \\(.*\\))?", line.strip())
        ]
        complete = (
            len(python_totals) == 1 and len(ok_markers) == 1
            and ok_markers[0] in ("OK", "OK (skipped=0)")
        )
        ok = exit_code == 0 and total > 0 and skipped == 0 and complete
        passed = total if ok else None
        failed = None
        todo = cancelled = 0
    else:
        total = passed = failed = skipped = todo = cancelled = None
        ok = False
    return {"status": "PASS" if ok else "FAIL", "exit_code": exit_code,
            "total": total, "passed": passed, "failed": failed,
            "skipped": skipped, "todo": todo, "cancelled": cancelled}


def test(argv, cwd, src):
    paths = [argv[5]] if argv[:5] == ["python", "-m", "unittest", "discover", "-s"] else [a for a in argv if a.endswith((".test.ts", ".test.mjs"))]
    if any(not (cwd / a).resolve().is_relative_to(src) for a in paths):
        raise ValueError("test path escapes candidate")
    cmd = [sys.executable] + argv[1:] if argv[0] == "python" else argv
    env = dict(os.environ)
    for k in ("GITHUB_TOKEN", "GH_TOKEN", "COPILOT_GITHUB_TOKEN", "OPENAI_API_KEY"):
        env.pop(k, None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, errors="replace", timeout=180, env=env)
        output = (proc.stdout + "\n" + proc.stderr)[-240000:]
        summary = parse_test_summary(output, proc.returncode)
        names = []
        if summary["status"] != "PASS":
            for line in output.splitlines():
                if line.startswith(("not ok ", "FAIL: ", "ERROR: ")):
                    names.append(re.sub(r"[^a-zA-Z0-9 _.:#()\-]", "?", line)[:150])
        return {**summary, "failed_test_names": names[:12]}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "BLOCKED", "error_kind": type(exc).__name__}

def evaluate(a):
    raw = Path(a.queue).read_bytes()
    q = json.loads(raw)
    s = load(Path(a.state) / "engine.json")
    if q.get("repo") != a.repo or s.get("repo") != a.repo or q.get("schema_version") != 1 or s.get("schema_version") != 1:
        raise ValueError("repository/schema mismatch")
    families = q["families"]
    if not 1 <= len(families) <= 60 or not 0 <= s["cursor"] < len(families):
        raise ValueError("invalid family queue/cursor")
    ids = [f["id"] for f in families]
    if len(ids) != len(set(ids)) or any(not re.fullmatch(r"(WR|SAM|COORD)-H\d\d", i) for i in ids):
        raise ValueError("invalid family IDs")
    for family in families:
        if len(family["checks"]) > 4 or not all(safe(cmd) for cmd in family["checks"]):
            raise ValueError("invalid formal test mapping: " + family["id"])
    src = Path(a.source).resolve()
    cwd = (src / q["source_subdir"]).resolve()
    if not cwd.is_dir() or not cwd.is_relative_to(src):
        raise ValueError("missing/unsafe source directory")
    # Repository tests require this ephemeral folder for TemporaryDirectory(dir=...).
    # This is the disposable Actions checkout, never the Windows production tree.
    if a.repo == "WoolRadar":
        (cwd / ".test-tmp").mkdir(exist_ok=True)
    sha = source_sha(src)
    n = min(a.limit, len(families))
    regular = [families[(s["cursor"] + i) % len(families)] for i in range(n)]
    priority = choose_recheck(s, families, {x["id"] for x in regular}) if n < 3 else None
    selected = ([priority] if priority else []) + regular
    results = []
    for item in selected:
        checks = []
        if item["disposition"] == "EXTERNAL_OR_POLICY_GATED":
            status = "EXTERNAL_GATE_NOT_EXECUTED"
        elif not item["checks"]:
            status = "NO_FORMAL_MAPPING_NOT_EXECUTED"
        else:
            for cmd in item["checks"]:
                checks.append({"argv": cmd, **test(cmd, cwd, src)})
            status = "FORMAL_SUBSET_PASS_NATIVE_PENDING" if all(c["status"] == "PASS" for c in checks) else "FORMAL_CHECK_FAILED_OR_BLOCKED"
        results.append({"id": item["id"], "goal": item["goal"], "status": status,
                        "external_gate": item.get("external_gate"), "checks": checks,
                        "strictly_complete": False, "business_accepted": False})
        print(json.dumps({"family": item["id"], "status": status,
                          "tests": [{"status": c["status"], "total": c.get("total"), "exit_code": c.get("exit_code")} for c in checks]}), flush=True)
    receipt = {"schema_version": 1, "repo": a.repo,
               "run_key": os.environ.get("GITHUB_RUN_ID", "0") + "/" + os.environ.get("GITHUB_RUN_ATTEMPT", "1"),
               "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
               "source_commit": sha, "source_ref": q["source_ref"], "queue_sha256": queue_digest(q),
               "previous_cursor": s["cursor"], "regular_count": n,
               "priority_recheck": priority["id"] if priority else None,
               "next_cursor": (s["cursor"] + n) % len(families),
               "results": results, "strict_new_acceptances": 0}
    save(a.output, receipt)
    print(json.dumps({"evaluation": "COMPLETE", "source_commit": sha, "count": n, "next_cursor": receipt["next_cursor"]}))

def persist(a):
    receipt = load(a.receipt)
    root = Path(a.state)
    state_path = root / "engine.json"
    s = load(state_path)
    if receipt.get("schema_version") != 1 or s.get("schema_version") != 1 or receipt.get("repo") != a.repo or s.get("repo") != a.repo:
        raise ValueError("invalid receipt/state")
    key = receipt.get("run_key", "")
    if not re.fullmatch(r"\d+/\d+", key) or not re.fullmatch(r"[a-f0-9]{40}", receipt.get("source_commit", "")):
        raise ValueError("invalid run identity/source")
    if key in s.get("processed_run_keys", []):
        print("IDEMPOTENT_REPLAY " + key)
        return
    if s["cursor"] != receipt["previous_cursor"]:
        raise ValueError("STALE_RECEIPT_REJECTED")
    if not 1 <= len(receipt["results"]) <= 3:
        raise ValueError("invalid receipt size")
    queue_path = Path(".github/relay/queue.json")
    queue = load(queue_path)
    if (queue.get("repo") != a.repo or queue.get("schema_version") != 1
            or receipt.get("source_ref") != queue.get("source_ref")
            or receipt.get("queue_sha256") != queue_digest(queue)
            or receipt.get("strict_new_acceptances") != 0):
        raise ValueError("receipt does not match trusted queue")
    families = queue["families"]
    n = receipt.get("regular_count", len(receipt["results"]))
    if type(n) is not int or not 1 <= n <= 3:
        raise ValueError("invalid regular rotation length")
    regular = [families[(s["cursor"] + i) % len(families)] for i in range(n)]
    priority = choose_recheck(s, families, {x["id"] for x in regular}) if n < 3 else None
    priority_id = priority["id"] if priority else None
    if receipt.get("priority_recheck") != priority_id:
        raise ValueError("invalid failed-family priority")
    expected = ([priority] if priority else []) + regular
    if len(expected) != len(receipt["results"]):
        raise ValueError("priority result length mismatch")
    if receipt.get("next_cursor") != (s["cursor"] + n) % len(families):
        raise ValueError("incorrect next cursor")
    for result, entry in zip(receipt["results"], expected):
        if result.get("id") != entry["id"] or result.get("goal") != entry["goal"]:
            raise ValueError("receipt task ID/order mismatch")
        commands = entry["checks"]
        checks = result.get("checks")
        if not isinstance(checks, list):
            raise ValueError("missing check evidence")
        if entry["disposition"] == "EXTERNAL_OR_POLICY_GATED":
            expected_status = "EXTERNAL_GATE_NOT_EXECUTED"
            if checks:
                raise ValueError("external-gate task executed")
        elif not commands:
            expected_status = "NO_FORMAL_MAPPING_NOT_EXECUTED"
            if checks:
                raise ValueError("unmapped task executed")
        else:
            if [x.get("argv") for x in checks] != commands:
                raise ValueError("test mapping mismatch")
            all_pass = all(x.get("status") == "PASS" and x.get("exit_code") == 0
                           and type(x.get("total")) is int and x["total"] > 0
                           and type(x.get("passed")) is int and x["passed"] == x["total"]
                           and x.get("failed") in (0, None) and x.get("skipped", 0) == 0
                           and x.get("todo", 0) == 0 and x.get("cancelled", 0) == 0
                           for x in checks)
            expected_status = ("FORMAL_SUBSET_PASS_NATIVE_PENDING" if all_pass
                               else "FORMAL_CHECK_FAILED_OR_BLOCKED")
        if result.get("status") != expected_status:
            raise ValueError("incorrect task disposition")
    if any(x.get("strictly_complete") is not False or x.get("business_accepted") is not False for x in receipt["results"]):
        raise ValueError("never auto-accept a family")
    # Attach the independent whole-source regression evidence to the durable
    # history. This is NOT a business/native acceptance gate.
    integration = load(Path(a.receipt).with_name("integration.json"))
    expected_integration = ([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
                            if a.repo == "WoolRadar" else ["npm", "test"])
    # The runner's absolute Python executable varies by host. Validate argv structure.
    integration_command = integration.get("command")
    valid_cmd = (isinstance(integration_command, list) and
                 ((a.repo == "WoolRadar" and len(integration_command) == 8
                   and integration_command[1:] == expected_integration[1:])
                  or (a.repo == "YinQieJi" and integration_command == expected_integration)))
    if (integration.get("schema_version") != 1 or integration.get("repo") != a.repo
            or not valid_cmd or integration.get("verified_business_complete") is not False
            or integration.get("status") not in ("PASS", "FAIL", "BLOCKED")):
        raise ValueError("invalid independent integration report")
    if integration["status"] == "PASS" and (
            integration.get("exit_code") != 0 or
            not isinstance(integration.get("total"), int) or integration["total"] <= 0 or
            integration.get("failed") not in (None, 0) or
            type(integration.get("passed")) is not int or
            integration["passed"] != integration["total"] or
            integration.get("skipped", 0) != 0 or
            integration.get("todo", 0) != 0 or
            integration.get("cancelled", 0) != 0):
        raise ValueError("forged integration success")
    receipt["integration"] = integration
    s["integration"] = {"status": integration["status"],
                        "source_commit": receipt["source_commit"],
                        "run_key": key, "total": integration.get("total"),
                        "passed": integration.get("passed"),
                        "failed": integration.get("failed")}
    s["cursor"] = receipt["next_cursor"]
    s["revision"] = s.get("revision", 0) + 1
    s["last_source_commit"] = receipt["source_commit"]
    s["last_run_key"] = key
    s["last_utc"] = receipt["generated_utc"]
    s.setdefault("processed_run_keys", []).append(key)
    s["processed_run_keys"] = s["processed_run_keys"][-250:]
    s.setdefault("families", {})
    for x in receipt["results"]:
        old = s["families"].get(x["id"], {})
        record = {"status": x["status"], "source_commit": receipt["source_commit"],
                  "run_key": key, "strictly_complete": False}
        if x["id"] == priority_id:
            record["last_recheck_revision"] = s["revision"]
        elif x["status"] == "FORMAL_CHECK_FAILED_OR_BLOCKED" and "last_recheck_revision" in old:
            record["last_recheck_revision"] = old["last_recheck_revision"]
        s["families"][x["id"]] = record
    save(state_path, s)
    with (root / "history.jsonl").open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(receipt, sort_keys=True, ensure_ascii=False) + "\n")
    print(json.dumps({"persisted_locally": True, "revision": s["revision"], "cursor": s["cursor"], "run_key": key}))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["evaluate", "persist"])
    ap.add_argument("--repo", required=True, choices=["WoolRadar", "YinQieJi"])
    ap.add_argument("--queue", default=".github/relay/queue.json")
    ap.add_argument("--source", default="candidate")
    ap.add_argument("--state", required=True)
    ap.add_argument("--output", default=".relay-report/receipt.json")
    ap.add_argument("--receipt", default=".relay-report/receipt.json")
    ap.add_argument("--limit", type=int, default=2)
    opt = ap.parse_args()
    if not 1 <= opt.limit <= 3:
        ap.error("limit must be 1-3")
    (evaluate if opt.mode == "evaluate" else persist)(opt)
