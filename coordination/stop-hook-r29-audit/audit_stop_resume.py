"""Isolated executable regression for the installed Codex Stop evaluator.

Uses synthetic session JSON and rollout files. Never invokes the live Stop hook.
"""
import argparse
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path


CASES = [
    ("active_resume", "active", ["继续干"], "block"),
    ("active_pause", "active", ["暂停"], "allow"),
    ("active_indirect_pause", "active", ["继续干", "现在先别干了"], "allow"),
    ("active_negative_resume", "active", ["继续干", "先不要继续执行"], "allow"),
    ("paused_then_resume", "paused", ["先暂停", "继续干"], "block"),
    ("paused_stays_paused", "paused", ["先暂停"], "allow"),
    ("active_conditional_pause", "active", ["完成后阶段性停止"], "block"),
    ("question_is_not_pause", "active", ["停了？继续干"], "block"),
]


def evaluate(module, name, disposition, messages, expectation):
    # Keep synthetic fixtures inside this workspace: the managed Windows sandbox
    # can deny writes to the platform's usual %TEMP% location.
    with tempfile.TemporaryDirectory(prefix="codex-stop-audit-", dir=Path(__file__).resolve().parent) as tmp:
        root = Path(tmp)
        outbox = root / "_outbox"
        outbox.mkdir()
        transcript = root / "rollout.jsonl"
        transcript.write_text("".join(json.dumps({
            "type": "event_msg",
            "payload": {"type": "user_message", "message": msg},
        }, ensure_ascii=False) + "\n" for msg in messages), encoding="utf-8")
        entry = {
            "schema_version": 1,
            "disposition": disposition,
            "project": str(root),
            "pending_requirements": ["VERIFY-1"],
            "actionable_tasks": ["Continue independently authorized task"],
        }
        if disposition == "paused":
            entry["user_pause_evidence"] = {"text": "先暂停", "date": "2026-10-22"}
        (outbox / "stop-continuity-handoff.json").write_text(
            json.dumps({"sessions": {"synthetic-sid": entry}}, ensure_ascii=False),
            encoding="utf-8",
        )
        event = {"session_id": "synthetic-sid", "cwd": str(root),
                 "hook_event_name": "Stop", "transcript_path": str(transcript)}
        actual = module.decide(event)
        observed = "block" if actual.get("decision") == "block" else "allow"
        return {"case": name, "latest_user": messages[-1],
                "state": disposition, "expected": expectation,
                "observed": observed, "correct": observed == expectation}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("module", type=Path)
    parser.add_argument("--expect-mismatch", type=int, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    source = args.module.read_bytes()
    spec = importlib.util.spec_from_file_location("isolated_codex_stop_evaluator", args.module)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    results = [evaluate(mod, *c) for c in CASES]
    mismatches = sum(not r["correct"] for r in results)
    report = {"kind": "isolated-stop-gate-regression",
              "source": str(args.module),
              "source_sha256": hashlib.sha256(source).hexdigest(),
              "count": len(results), "mismatches": mismatches,
              "expected_mismatches": args.expect_mismatch,
              "cases": results,
              "installed_hook_mutated": False,
              "live_stop_event_invoked": False}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for row in results:
        print(f"{'PASS' if row['correct'] else 'FAIL'} {row['case']}: expected={row['expected']} observed={row['observed']}")
    print(f"TOTAL={len(results)} MISMATCH={mismatches} EXPECTED={args.expect_mismatch}")
    return 0 if mismatches == args.expect_mismatch else 1


if __name__ == "__main__":
    raise SystemExit(main())
