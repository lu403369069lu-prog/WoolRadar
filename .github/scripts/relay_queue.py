#!/usr/bin/env python3
"""Deterministic read-only queue checkpoint; never claims ChatGPT was awakened."""
import datetime as dt
import json
import os
from pathlib import Path

manifest = Path(os.environ.get("BACKLOG_MANIFEST", "ledger/coordination/HISTORICAL_ALL_50_FAMILY_STATUS_20261017.json"))
output = Path(".relay-checkpoint")
output.mkdir(exist_ok=True)
state = {
    "schema_version": 1,
    "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    "run_id": os.environ.get("GITHUB_RUN_ID"),
    "run_sha": os.environ.get("GITHUB_SHA"),
    "source_manifest": str(manifest),
    "mode": "READ_ONLY_NO_AGENT_NO_GITHUB_WRITE",
    "checkpoint_persisted_to_git": False,
}
if not manifest.is_file():
    state.update(status="BLOCKED", reason="Historical manifest unavailable")
else:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    families = data.get("family_records", [])
    ready = [x for x in families if x.get("disposition") == "READY_FOR_LOCAL_CODEX"]
    external = [x for x in families if x.get("disposition") == "EXTERNAL_OR_POLICY_GATED"]
    state.update(
        status="INVENTORIED_NOT_EXECUTED",
        total=len(families),
        ready_count=len(ready),
        external_count=len(external),
        strict_business_accepted=0,
        next_candidates=[{"family_id": x["family_id"], "goal": x["goal"], "qualification": x.get("qualification")} for x in ready[:5]],
        action_required="A ChatGPT interactive or scheduled run must explicitly claim a candidate and verify a write; this workflow does not invoke ChatGPT.",
    )
(output / "relay.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(state, ensure_ascii=False))
if state["status"] == "BLOCKED":
    raise SystemExit(1)
