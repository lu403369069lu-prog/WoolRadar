"""Offline standard-library dispatcher. Advisory decisions only: no network, no agents."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{40}\Z")
TASK = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,79}\Z")
PROJECTS = {"SAM": ("lu403369069lu-prog/YinQieJi", 1),
            "WoolRadar": ("lu403369069lu-prog/WoolRadar", 2)}
EVENT_TYPES = {"evidence_ready", "review_requested", "review_completed",
               "blocked", "quota_warning", "quota_restored"}


def validate(event: dict) -> dict:
    if not isinstance(event, dict):
        raise ValueError("EVENT_NOT_OBJECT")
    project = event.get("project")
    if project not in PROJECTS:
        raise ValueError("UNKNOWN_PROJECT")
    repo, issue = PROJECTS[project]
    if event.get("repository") != repo or type(event.get("issue")) is not int or event["issue"] != issue:
        raise ValueError("SOURCE_SCOPE_MISMATCH")
    task, kind, sha = event.get("task_id"), event.get("event_type"), event.get("head_sha")
    if not isinstance(task, str) or not TASK.fullmatch(task):
        raise ValueError("INVALID_TASK_ID")
    if kind not in EVENT_TYPES:
        raise ValueError("UNTRUSTED_EVENT_TYPE")
    if not isinstance(sha, str) or not SHA.fullmatch(sha):
        raise ValueError("FULL_LOWERCASE_HEAD_SHA_REQUIRED")
    evidence = event.get("evidence_url")
    if evidence is not None and (not isinstance(evidence, str)
                                 or not evidence.startswith(f"https://github.com/{repo}/")
                                 or len(evidence) > 2048):
        raise ValueError("INVALID_EVIDENCE_URL")
    return {"project": project, "repository": repo, "issue": issue,
            "task_id": task, "head_sha": sha, "event_type": kind,
            "event_key": f"{project}/{task}/{sha}/{kind}", "evidence_url": evidence}


def decide(event: dict, quota_paused: bool) -> tuple[str, str]:
    kind = event["event_type"]
    if kind == "quota_warning":
        return "quota_paused", "do_not_trigger_codex"
    if kind == "quota_restored":
        return "needs_approval", "ask_user_to_confirm_quota_restoration"
    if kind == "blocked":
        return "blocked", "record_blocker"
    if kind == "evidence_ready":
        return "evidence_ready", "request_remote_read_only_review"
    if kind == "review_requested":
        return (("quota_paused", "defer_local_execution") if quota_paused
                else ("claimed", "remote_read_only_review"))
    return "independently_reviewed", "request_human_approval_before_merge"


def dispatch(db_path: Path, events: list[dict], dry_run: bool = False) -> dict:
    if not isinstance(events, list):
        raise ValueError("EVENT_BATCH_NOT_LIST")
    validated = [validate(e) for e in events]
    seen: dict[str, str] = {}
    for item in validated:
        digest = hashlib.sha256(json.dumps(item, sort_keys=True).encode()).hexdigest()
        key = item["event_key"]
        if key in seen and seen[key] != digest:
            raise ValueError("CONFLICTING_DUPLICATE_EVENT_KEY")
        seen[key] = digest
    if dry_run:
        # A preview must not create a database or even its parent directory.
        # Clone existing state into memory using a read-only connection, so
        # duplicate checks match the real run without touching persistent data.
        conn = sqlite3.connect(":memory:", timeout=10, isolation_level=None)
        if db_path.exists():
            try:
                source_uri = db_path.resolve().as_uri() + "?mode=ro"
                with closing(sqlite3.connect(source_uri, uri=True, timeout=10)) as source:
                    source.backup(conn)
            except Exception:
                conn.close()
                raise
    else:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), timeout=10, isolation_level=None)
    try:
        conn.execute("PRAGMA busy_timeout=10000")
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("CREATE TABLE IF NOT EXISTS processed (event_key TEXT PRIMARY KEY, payload_hash TEXT NOT NULL, state TEXT NOT NULL, action TEXT NOT NULL)")
        conn.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        row = conn.execute("SELECT value FROM settings WHERE key='quota_paused'").fetchone()
        quota_paused = row is None or row[0] == "1"
        decisions = []
        for item in validated:
            key = item["event_key"]
            digest = seen[key]
            previous = conn.execute("SELECT payload_hash FROM processed WHERE event_key=?", (key,)).fetchone()
            if previous:
                if previous[0] != digest:
                    raise ValueError("EVENT_KEY_PAYLOAD_CHANGED")
                decisions.append({"event_key": key, "result": "duplicate_noop"})
                continue
            state, action = decide(item, quota_paused)
            decisions.append({"event_key": key, "result": "new", "state": state, "action": action})
            if item["event_type"] == "quota_warning":
                quota_paused = True
            conn.execute("INSERT INTO processed VALUES (?,?,?,?)", (key, digest, state, action))
        conn.execute("INSERT OR REPLACE INTO settings VALUES ('quota_paused',?)", ("1" if quota_paused else "0",))
        conn.execute("ROLLBACK" if dry_run else "COMMIT")
        return {"quota_paused": quota_paused, "dry_run": dry_run, "decisions": decisions}
    except Exception:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    print(json.dumps(dispatch(args.state, json.loads(args.input.read_text(encoding="utf-8")),
                              args.dry_run), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
