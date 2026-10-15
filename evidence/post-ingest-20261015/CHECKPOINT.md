# Post-ingest evidence and trace consistency — integration checkpoint

**Date**: 2026-10-15. **Executor**: interactive ChatGPT GitHub connector (NOT unattended Scheduled). **Status**: IN_PROGRESS / draft. **Stack base**: Codex draft PR #21 exact commit `38f523712b9db23515bb6d56b08d9a2910b4be5c`; PR #21 itself stacks on #20, #19, #18, #17, #16 and #15. PR #13 collector and PR #14 historical-noise/report remain independent: never auto merge.

## End-to-end defect and implementation

1. **Supplemental official evidence**: `Pipeline.apply_evidence` formerly used independently committed `get_event → add_evidence → evaluate → set_status → queue_verified` operations. `Database.reindex(review)` can merge and DELETE the same event ID between reads/writes, causing a foreign-key error or partial recorded evidence. Fixed by enclosing only local database operations in the existing `candidate_transaction()` with the same `BEGIN IMMEDIATE` reservation used by Codex PR #21's candidate ingestion. Network fetch and notification delivery remain outside the transaction. A stale ID *before* reservation is rejected by `get_event` (no blind survivor reassignment).
2. **Official trace lifecycle**: `OfficialTracer.trace` can begin after its event ID has been merged, or finish after a concurrent merge following its remote page read. It now emits and saves an explicit `STALE_EVENT_ID / EVENT_MERGED_OR_REMOVED` record instead of crashing the node or falsely declaring an old event verified. No network calls were added.
3. **Node health**: when a traced official event is stale, `Pipeline.ingest_node` adds a synthetic FAILED source-status `STALE_EVENT_ID` so a node that otherwise handled candidates reports `PARTIAL`, not `OK`. This does not fabricate entitlement or reissue a stale verified notice.

## Test evidence — careful boundaries

- Actual isolated Linux Python3.13 / WAL SQLite behavioral reproducer: `python review_apply_evidence_race_probe.py -v` → **2/2 pass, exit 0**. One test confirms *old* disconnected read-and-write allows concurrent reviewed merge to finish first and then raises `sqlite3.IntegrityError`; the paired model holds `BEGIN IMMEDIATE` and blocks migration until its evidence insert is complete. This test is a small faithful SQL/race model, **not** an execution of all GitHub repo modules.
- Formal repository tests committed (NOT EXECUTED at this PR head):
  - `tests/test_apply_evidence_transaction.py`: 3 temporary SQLite tests (reindex exclusion and official evidence retention, rollback+retry, stale merged ID fail-closed).
  - `tests/test_official_trace_stale_event.py`: 5 tests (old ID at trace start, old ID at trace completion, healthy control, pipeline PARTIAL status, healthy node control). The tests intentionally use mocks to prohibit outbound network requests.
- Remote GitHub path/blob readback confirms the actual files and commits. No CI workflow exists under `.github/workflows/` at this branch HEAD; therefore there is **no official CI pass for PR #22**, and the new 8 tests should be treated as unverified until a full isolated checkout runs them.
- Codex PR #21 previously reported **211/211 formal baseline tests** and **231/231 temporary PR13+PR14 composition tests**. Those results were produced on PR #21's different exact SHA and **must not be used as PR #22's results**.
- Neither OpenAI Scheduled Github write nor machine V3 task claiming was used; no production, PLC, paid API, rollout, or automatic merge.

## Exact next action / acceptance gates

A. In an isolated checkout of this draft PR head run: `python -X utf8 -m unittest discover -s tests -v`. Record full stdout/stderr, exit code, count, skipped, flaky retries and SHA. Pay special attention to the 3+5 newly added tests, Windows temp SQLite resource closing, and `OfficialTracer` construction without network.
B. Compare merged runtime with the precise source-vector of PR #13 collector and PR #14 noise/report, and check `Pipeline.ingest_node` and official trace health/report propagation. Source-vector pass alone is not a real Git merge.
C. Investigate **remaining** race: event ID can merge between the initial `OfficialTracer.trace` source discovery and the start of `Pipeline.apply_evidence()`; now auditable and fail-closed, but no trusted old→survivor ID resolution/retry exists. Also verify official-trace output file atomicity and reader races before considering production use.
D. Confirm historical SQLite copy-only reindex/backup/rollback, notification idempotency, held-out business precision/recall and end-to-end original task goals. Treat these as open; no 95% claim.

**Milestone**: M1_WOOLRADAR_INTEGRATION; status=IN_PROGRESS. New PR #22 is one coherent post-ingest continuation, not a release claim.

## Continuation — official page fetch versus merge exact classification

A further review followed the rare boundary where `fetch_public_page()` succeeds and `Pipeline.apply_evidence()` raises `KeyError` because `review_campaign/reindex` removed the old event ID while HTTP was in progress. The prior generic `except Exception` would misclassify that as a fetch failure, and a mocked but still present ID could lead to an incorrectly ordinary final status. The current code catches `KeyError` **only around supplemental evidence application**, appends a `STALE_EVENT_ID` reference entry, stops further page reads, and guarantees final status `STALE_EVENT_ID/EVENT_MERGED_OR_REMOVED`. It never invents evidence on a replacement ID or turns a real HTTP error into a stale event.

Added another formal in-repo regression test for successful mocked public fetch with `apply_evidence` rejecting a merged ID, including audited persistent report and no stored proof. **Formal regression definitions are now 9 in total (3 supplemental + 6 tracer/node)**, none has been run on exact complete repo SHA. The independently run 2/2 WAL SQL behavior model remains the only claimed executable check for this draft until the full test run occurs.


## Global continuation — ID reuse and notification collision hardening (latest)

The 2026-10-15 one-time **read-only Scheduled** run independently reproduced both SQLite `INTEGER PRIMARY KEY` recycling and an unlocked outbox-snapshot identity hazard, and supplied candidate exact-module diffs and tests. The interactive ChatGPT session *reviewed and separately committed* them to this original PR, without pretending Scheduled wrote GitHub.

- `core/db.py`: `reindex()` now reconciles duplicate `(event_id,batch_id,channel)` notice collisions so a confirmed `SENT` cannot silently downgrade to `PENDING`, and an in-flight `CLAIMED` loser cannot silently reset to immediately sendable. New `tests/test_reindex_notification_collision.py` (3 formal tests). Direct SQLite migration SQL behavior model: **5/5 pass exit0** after change; 3/3 pre-fix failure-mode reproductions established the former loss of state.
- `core/notify.py`: exact GitHub blob `926d69eabed379653f542d35e86f377fc6c726b7` matches the locally tested exact-source module after the fix. Snapshot identity is revalidated and pinned into the SQL claim; post-send update checks claim lease/attempt and identity to avoid treating a recycled ID as an unrelated new notice. Two new cases in `tests/test_notify_reindex_transaction.py`. Local exact-module regression **4/4 pass exit0**; no true Telegram or full repository execution.
- `core/pipeline.py` and `core/official_trace.py`: pin a four-field event identity at ingestion and enforce it at trace entry, evidence write under SQLite reservation, and final read. A merged-away highest row ID can be recycled; pre-existing mere numeric existence checks could attach old official evidence to a different new campaign. Two additional cases in `tests/test_official_trace_stale_event.py`. Independent SQLite row-reuse/protection probes **8/8 pass exit0**, but full exact remote database/module tests not yet executed.
- Across this draft, formal Python tests in the 4 newly added/changed files currently define **18 test methods** (3 evidence +8 trace/health +4 outbox +3 collision). Source code and formal tests are committed, but **these 18 formal repository tests were not executed as one complete PR head**. Never add unrelated isolated denominators to claim 18/18 or full baseline green.

The related [draft PR#23](https://github.com/lu403369069lu-prog/WoolRadar/pull/23) composes upstream PR#13 collector quality with this stack and seven new freebie-intent tests (separate extracted-function 17/17 pass exit0). PR#14 CLI/report/noise-audit composition encountered an explicit platform safety refusal; its source files remain **unintegrated**, not silently dropped or bypassed.

### Strict outstanding gates
1. Obtain complete isolated private checkout at exact latest PR22 HEAD and run `python -X utf8 -m unittest discover -s tests -v` (Windows and Linux), record exit, passing/failing counts and skips. Re-run after PR23 integration source vectors.
2. Exercise actual `Database.review_campaign/reindex`, outbox transfer, sent-state precedence, and rowid-reuse control with a copy of a historical SQLite database. Validate backup/restore/rollback, not live database.
3. Verify local file delivery receipt filename reuse and outbound send-before-row-delete ambiguity. At-least-once delivery remains possible under ambiguous external sends; no exactly-once promise.
4. Finish PR14 approved source composition, real holdout eligibility/quality, SAM PR3 actual full Node build/Windows focused32 and R5 acceptance. Original full project goal remains IN_PROGRESS.
