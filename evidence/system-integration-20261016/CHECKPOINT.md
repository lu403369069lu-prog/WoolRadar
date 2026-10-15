# WoolRadar system integration — active checkpoint, 2026-10-16

Original P06 and release readiness remain IN_PROGRESS. The three required final independent rounds have NOT started: core business/source/field acceptance is still incomplete.

## Exact source and integration

- PR22 latest cold-read head e03674ec3a4ee5df27047e91af5d972495574bde. Restored a real isolated Git worktree with exact commit and 138 blob/20 tree identities. Local imported history is shallow at that commit; remote and existing history were not rewritten.
- Maintain existing PR23, expected parent 68b018965491911f2ab4943bc760eaeaa6eea710. Its collector and two tests incorporate PR13 b18619212b0a760b2200f0f2e2b01adf603cbe83; retain newer PR22 db/notify/trace/test code instead of restoring PR23's older copies.
- PR14 f4cf71ef5df5c3ee6b2c70b46c29cb6bd4bb650d CLI/noise/report/tests are now composed. No GitHub PR was merged, no new production branch deployed, no paid API or real external message invoked.

## Executed evidence

- Exact PR22 formal Windows suite:233 tests,0 skip,exit1,one missing test helper. Minimal helper repair preserves all old assertions:233 pass,exit0,13.423s.
- Latest22 plus existing23 collector and14 noise/report formal full suite:263 pass,0 skip,exit0,15.421s.
- Independent review then reproduced P1 dual-CLAIMED lease loss (fake sender called again), P2 identical trace record publication false collision, and coordinator P1 report event/evidence identity swap after actual rowid reuse.
- New race contracts were run red before changes. Repair: keep max lease/attempt history for both CLAIMED rows; publish complete immutable trace bytes atomically and atomically replace latest view; build/revalidate all report DB data in one reserved connection before file rendering.
- Formal combined suite after repairs:268 pass,0 skip,exit0,15.659s. A hard-link-based publication first passed outside the restrictive sandbox but failed with WinError5 in the independent restricted runtime. Removed that dependency: kernel file lock plus full temporary-file atomic replacement. Final full suite268 pass,0 skip,exit0,15.845s. The same previously failing restricted interpreter independently passes13 focused tests/1.718s and6 extra checks, including two real publishing processes and recovery after lock holder os._exit(17). Earlier failed review is retained. This is a real combined run, not a sum of branch totals. No release success claimed.
- Read-only production SQLite backup into private local-only snapshot; sanitized copy110 events/213 evidence/170 SENT notices/650 runs. Preview2 old keys/0 merges; migration preserved every table count, notification states and FK/integrity; backup and restored semantic dumps exactly match pre-migration sanitized snapshot. Second migration0 merges. Rendered110-event report from private copy. Previously wrongly merged-away vendors cannot be recovered by this test.

## Next executable work

### Subsequent screening corrections

The fallback award/free-start/coupon branch could revive ended offers or requests. Six new contracts first showed4 failures. Its guard repair then exposed two documented P2 boundaries: direct/brand semicolon clauses could ignore a trailing closure, and an explicit new credit program after an old program ended was rejected. Six additional contracts first showed3 failures. All matching branches now share statement qualification and permit a clearly explicit new-program transition after a semicolon. Full combined Windows suite280/0 skipped/exit0/15.984s; independent45 focused methods plus11 prior positive/negative cases passed. These are development regressions, not holdout or95% accuracy evidence. Source collector SHA25617f2ed0553bc93b8028fd54a0f3733d53803a021695e97ff6ec0821af1ef9f14.

The user's shared5h quota rule is verified from the coordinator's current user turn: below20%, three existing sessions checkpoint/upload and verify, release to ready using the validated protocol, then wait for all three actual upload receipts and coordinator resume. Once per reset cycle1792107327; no quota reset or paid route. Current local receipt is _outbox/quota-barrier-1792107327.json. Do not start a large new unit near the threshold or call a preventative release quota_paused. Independent real holdout has not started; raw source metadata inventory is not an evaluation.

1. Independent fix review is complete for the repaired concurrency boundaries. Publish checkpoint to existing PR23 with CAS and record exact SHA/commands/exit in Issue2 and V3. Never overwrite a newer remote head. A new report test initially expected UNKNOWN instead of the schema default DISCOVERED; corrected that expectation while preserving identity/evidence/concurrency assertions, with the intermediate failed output retained.
2. Freeze new real public-source samples before labels and code evaluation. The45-row October14 development set was used to fit PR13 and is NOT independent holdout. Report precision/recall/FP/FN/pairwise dedup denominators and unknown cases; no95% claim from tiny positives.
3. Inspect report truth, availability/deadline/capacity/region/card conditions/noise and duplicates on isolated copied data; preserve unknown eligibility. Public official source proof does not establish this user's eligibility.
4. Recheck five original-node and Windows schedule contracts READ ONLY. No production code/DB/task changes, no reboot/sleep/control actions. Original full upstream OpenMagpie PostgreSQL/model/Web and other runtime/source limits remain; don't repeat failed download or canceled Reddit registration.
5. After all core acceptance gates pass, perform3 independent final rounds: data/concurrency/recovery; business/real sources/report; full regression/compatibility/security/performance/release. None is complete merely because unit tests pass.

## Local-only boundaries

Raw and sanitized DBs, backups, live logs and raw reports remain local. Shared files include code, formal tests and redacted small evidence only. No cookies/auth profiles/tokens/account data. Source-budget/Chrome checks remain browser-based; GitHub MCP is the only GitHub network route.
