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
