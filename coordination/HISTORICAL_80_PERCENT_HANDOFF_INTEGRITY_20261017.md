# 50-family Codex handoff structural integrity recheck — 2026-10-17

Checked GitHub live content of the original machine manifest (blob `dcabb20769b91a0d0f3dfcad186fd6db15f2ca39`), its Markdown handoff (blob `bfe941077e1914b840bb2e1b2e5cce755d713100`) and batch runner (blob `b494db0b5036a99058376859b958fcfbc8a36483`) at branch `chatgpt/scheduled-checkpoint-contract-20261016`.

## Machine manifest structural audit (performed in interactive chat, not Scheduled)
- Exactly **50 jobs**, 42 `READY_FOR_LOCAL_CODEX`, 8 `EXTERNAL_OR_POLICY_GATED`.
- Exactly **39 distinct nonempty run_command strings** among the 42 ready jobs.
- **42/42** ready jobs have `run_command`, `verified_test_path`, and `verified_test_blob` populated.
- **50/50** jobs' `required_head_sha` exactly matches the corresponding manifest `immutable_refs` SHA (W for WoolRadar, S for `YinQieJi-SAM`, C for WoolRadar-Coord).
- 12 batch groups: W-DB 6, W-DATA 6, W-GRANT 3, W-EXTERNAL 4; S-AUDIT 8, S-CARDS 1, S-WB 6, S-EXTERNAL 3, S-EVAL 4, S-RELEASE 2; C-CORE 6, C-EXTERNAL 1.
- **Important validation correction:** initial one-off audit erroneously matched project name `SAM` rather than the actual manifest string `YinQieJi-SAM`, generating 24 spurious SHA mismatch errors. Corrected independent rerun showed **zero SHA mismatches**. This was an audit expression error, NOT a source manifest error.

## What has NOT been established
- This pass checked the manifest's **internal structural coherence**, not that every Git blob has been freshly re-fetched or every command has been executed on the immutable checkout during this turn.
- The 42 ready jobs are **handoff entries**, not 42 successfully executed acceptance tests, and the 39 unique commands are not 39 verified green results.
- Windows Node24/26, real direct+stdio MCP, SAM 61-question / 522-source approved gold, WoolRadar independent fresh blind sample and production report bridge remain unverified or externally gated.
- No production access, merge, deployment, task reactivation or private data export occurred. Four hourly engineering tasks were disabled in this chat; daily 09:30 opportunity brief remains enabled.

## Next action for local Codex
Use `coordination/HISTORICAL_80_PERCENT_CODEX_HANDOFF_20261017.md` and `coordination/HISTORICAL_CODEX_BATCH_RUNNER_20261017.py` in a disposable checkout at exact manifest SHA. Record per-family `source_head | command | exit | pass/fail/skip | log_sha256 | disposition`, keeping test totals deduplicated. Never treat `READY_FOR_LOCAL_CODEX` as `PASS`. If immutable heads differ, stop and explicitly reconcile before running. Feed receipts back to WoolRadar Issue #2, YinQieJi Issue #1 and coordinator Issue #3.

## Follow-up blocker: runner/manifest cross-file SHA guard

2026-10-17 interactive follow-up independently re-fetched the runner blob `8dd067055447eb19afde71a707466d02c6526ec0`. It checks an internal `EXPECTED` SHA but **does not read the adjacent 50-family JSON manifest before invoking tests**. Proposed change: parse `HISTORICAL_80_PERCENT_CODEX_JOBS_20261017.json`, require `total_families==50`, `len(jobs)==50`, and require `immutable_refs[{wool:W,sam:S,coord:C}].sha == expected`; fail before subprocess invocation if any mismatch. Add a negative test with a deliberately altered manifest SHA, and a missing-manifest negative test. This is **not fixed**: GitHub code write was safety-blocked, so do not claim implementation or formal tests passed. No bypass attempted.
