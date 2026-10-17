# Historical-first continuation gate, 2026-10-17

**HISTORICAL_RECOVERY_CLOSED=false | HISTORICAL_PRIORITY=1 | NO_NEW_UNRELATED_FEATURE_FIRST**

This is the user's explicit preference for every next '继续' and the four hourly engineering tasks. No notification changes. It is a durable priority checkpoint, not a promise that ChatGPT can run asynchronously outside a Scheduled task.

## Read first

- [WoolRadar 19 historic discovery/quality families](SCHEDULED_HISTORICAL_ENGINEERING_RECOVERY_20261017.md), original old SQL/WAL files in independent-quality/historical-scheduled-20261015, Issue #2, main Draft PR23, own PR35/37.
- [SAM 24 historic families](https://github.com/lu403369069lu-prog/YinQieJi/blob/1039112335c7db3fd34d2e1d9f0c69da37840918/SAM/independent-review/SCHEDULED_HISTORICAL_ENGINEERING_RECOVERY_20261017.md), Issue #1, main PR5, archival PR10 and stacked code PR11/12/13/14.
- [All-PR and Issue-comment census](HISTORICAL_GITHUB_CENSUS_20261017.json): actually fetched **49 PRs (Wool 35, SAM 14), 200 comments across the three long-term Issues**, with 109 detectable event_key markers; a PR/Issue reference never alone proves Scheduled-origin write.
- [Machine state for all 50 recovered families](HISTORICAL_RECOVERY_MACHINE.json) — authoritative per-family next-action status; do not use old static PR SHAs without live readback.
- [Coordination/relay 7 historic families](SCHEDULED_HISTORICAL_RELAY_ASSETS_20261017.md): existing Draft PR6–12 are real code/review assets, not main PR23 nor fully autonomous agent handoff; prevent duplicate integration.
- [Scheduled activity/provenance ledger](SCHEDULED_RESULTS_LEDGER_20261017.md) and [coordination Issue #3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3), latest V3 state.json owner/lease/fence.

## Completed discoverability sweep vs still-unavailable history

- Full recursive personal Library metadata sweep returned 25 entries, 14 in the Oct14-17 date window; every visible named old .patch/.py/.md was inspected; two ZIPs were opened and classify as earlier setup/Windows audit, not hourly source fixes.
- Original three SQL/WAL atomicity assets could only be read as indexed text, not raw-byte materialized. The new GitHub text transcriptions are one final newline shorter, so **not** byte-identical raw archives. Original personal Library files remain intact.
- Task metadata shows run times and enablement, **not** all past task bodies, attachments, or GitHub write receipts. 35+ previously traceable hourly rounds are a lower bound; unattended Scheduled GitHub successful writes remain NOT_VERIFIED.
- Do not claim all hourly history has been read; missing log bodies and inaccessible original artifacts must be tagged SOURCE_UNAVAILABLE.

## For each next continuation and hourly task

1. RELOAD both inventories, old checkpoints, Issues, exact PR SHAs and V3 ownership. Search for newly accessible historical code/test or commits before working on unrelated new features.
2. Reconcile each old family to its original file/ref/SHA; record historic result vs freshly rerun test. Assign RESTORED_EXACT, RESTORED_TEXT_ONLY, SUPERSEDED_NEEDS_REGRESSION, STAGED_DRAFT_TEST_PENDING, UNFIXED_REPRODUCIBLE, CANDIDATE_UNVERIFIED or SOURCE_UNAVAILABLE.
3. For any actionable historical item, inspect **current real code first**, deduplicate prior PRs, then recover a source/test patch, execute authentic isolated tests, upload to permitted independent Draft branch and corresponding Issue, remote-readback the exact blob. If Scheduled write blocked, preserve the full patch and test in its user-visible task result; never bypass the block.
4. Repeat the same historic recovery/integration cycle until every accessible candidate has clear disposition. No empty periodic status narrative. If no new original evidence exists, run exact-current formal regression for already restored historic fixes before new unrelated work.
5. Only set HISTORICAL_RECOVERY_CLOSED=true after every **accessible** historical source is indexed and every actionable recovered item either staged with tests or explicitly BLOCKED with reproducible steps. ALL_SCHEDULED_RUN_LOGS_COMPLETE must remain UNKNOWN unless the full past task execution history is actually obtained. Global project release and three independent final rounds are separate gates.

No Work/Codex/paid API/new paid GitHub runners, no V3 ownership override, auto-merge, production Windows/PLC/SQLite changes, private source export, actual account claims or payment.


## 2026-10-17 interactive handoff priority after hourly pause

The user's exact demand is **the currently active ordinary chat should bulk-disposition ≥80% of previously recorded 50 historical engineering families and write GitHub**, NOT leave the work to hourly Scheduled. Four enabled hourly engineering automations have been explicitly **paused** through automation updates (:00 Wool, :10 SAM, :30 SAM QA, :40 coordinator); the daily 09:30 public benefits brief remains enabled. The paused hourly jobs had no verified direct GitHub write access and should not be silently resumed to "continue work".

Current deliverables:
- [Every one of 50 families assigned a precise status, 42 SHA-verified local Codex test-file entrypoints, 8 separate external/human/Scheduled blockers](HISTORICAL_80_PERCENT_CODEX_HANDOFF_20261017.md).
- [Machine-readable 50-family jobs](HISTORICAL_80_PERCENT_CODEX_JOBS_20261017.json) includes actual Git test blobs, branch/source SHA, cwd, specific command, prior historic status, and hard gate. Every **42/42 target path truly exists** at the reviewed exact repo head. The earlier missing PR9 frozen teacher assets have now all **nine** been transplanted byte-for-byte from [SAM PR9](https://github.com/lu403369069lu-prog/YinQieJi/pull/9) into [SAM PR15](https://github.com/lu403369069lu-prog/YinQieJi/pull/15) SHA `82bf36efa90cced8dafb56502812eb49f40515f3`.
- [Offline SHA-locked Codex batch runner](HISTORICAL_CODEX_BATCH_RUNNER_20261017.py) defaults to dry-run, must be executed only against clean/disposable clone, will not install/push/merge or modify production. Three groups Wool/SAM/Coord test. SHA mismatch refuses, logs stay local until human redaction.
- GitHub issue handoffs: [Wool Issue2](https://github.com/lu403369069lu-prog/WoolRadar/issues/2#issuecomment-6228653268), [SAM Issue1](https://github.com/lu403369069lu-prog/YinQieJi/issues/1#issuecomment-6228653762), [Coord Issue3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3#issuecomment-6228654199).

**Truth in metrics**: 42/50=84% **actionable local-acceptance handoff** at named immutable refs; it is not 42/50 actual executable tests completed, not an engineering release acceptance rate, not 80% of historical bugs fixed. Historical recovery remains `HISTORICAL_RECOVERY_CLOSED=false`. The same 8 gold/policy/human blockers require real source/consent; no evidence permits this chat to mark them green. 61 SAM positives still only 10 source-grounded answered, Wool fresh holdout recall25% and signed actual daily report still disconnected. User wants current **interactive** GitHub writeback, not hourly Tasks. Future "继续": first ingest new exact-SHA sanitized Codex local batch receipts; if no receipts, work remaining actual source patches in interactive session, and never restart broad inventory from scratch or falsely promise autonomous background execution.
