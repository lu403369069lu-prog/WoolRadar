# Historical Codex handoff source drift, no silent repinning — 2026-10-17

**event_key** `interactive/history-50/head-drift-safe-reconciliation/20261017`. This is a **read-only multi-repository comparison** followed by an authorized separate checkpoint documentation update. Nothing was merged, rebased or force-pushed; no production user files, accounts, Windows/PLC, runner deployment or paid CI.

## Why a fresh freeze is necessary

The SHA-guarded 42-family / 39-unique-command offline Codex handoff is intentionally pinned to source snapshots **Wool Draft PR39 `80c5ea18769c1312e5be5fd99a39e4f3d498c64f`**, **SAM Draft PR15 `82bf36efa90cced8dafb56502812eb49f40515f3`**, and **Coord Draft PR11 `27796df5f9847c1bb5d48d2a445e418dfb3d8e96`**. It refuses unknown refs rather than silently adjusting.

New cold GitHub read during the **same interactive engineering session** showed **both owner branches advanced independently while the checkpoint execution harness was being completed**:
- Wool PR39 now **`1aad1c98584dd2c7291ada30ef71e813dbfedd50`**, `compare_commits(old...new)` **ahead7 / behind0**, changed `core/public_corpus.py`, and added exact new formal public host tests `tests/test_public_corpus_nonpublic_urls.py` blob `5dc8307b2666c3ba670f7d04ee260c7ce7f02326` (six unittest methods) plus `tests/test_public_corpus_invalid_unicode.py` blob `e26a0ba16033de49c8544c2b03093ad103787e83` (five methods), with corresponding producer/quality evidence Markdown. New actual producer code blob `383f3ad38930863fe5311260f8869b1ca65564ef`. An independent fresh new blind provider-window remains **NOT PASSED**.
- SAM PR15 now **`efe9a93f4bea4b6f3bf33f7fc9772e9008c8b3c0`**, `compare_commits(old...new)` **ahead2 / behind0**, added formal standalone `SAM/snapshot/tools/build-release-manifest.synthetic.test.mjs` blob `5b8e99131748269ed7046ffd0d2396da3d30bc79` (five actual Node TAP cases) and its historical report blob `be4f6120a96ac46e50e93fb43f0835612aa2909a`. The report says the true original `atomic-write.test.mjs` 6 + new 5 = **11/11 Linux Node22 isolated official tests pass exit0** with temp synthetic Git and registry, but THIS latest-head audit did **not** re-run those 11. That is an original GitHub-authored test receipt, not current Windows Node24/26 and not a multi-file transaction or release approval.
- Coord PR11 remains exact same SHA and historical Windows57 original receipt source-matched; current execution has not retested the 57.

## Revalidation of the existing 42 historical job identities

Fetched full actual new Git trees: Wool **302** items, SAM **228** items, Coord **58** items; no truncation. For **all 42 original ready jobs** (Wool15, SAM21, Coord6), rechecked `verified_test_path` → Git blob: **42/42 unchanged** from original frozen manifest, **0 changed/missing tested file SHA**. The three *new* official test files above were never in that 42-job historical list; don't claim the old manifest covers these additional regressions.

**Do not silently overwrite the reviewed manifest SHA with the newer HEAD.** Those heads may continue moving concurrently, and Wool source code really changed. Safe options for Codex:
1. **First frozen regression**: run the existing reviewer-pinned `--expected-head` commits in clean detached, disposable checkout with checkpoint executor and manifest. This yields real old-head 42-family evidence, and the executor correctly rejects branch HEAD drift.
2. **Current-head delta**: in **separate** clean disposable checkouts at newly observed full SHA, run the three additional *real* new formal tests, whole native official suite and new external source gold. Exact syntactically scoped commands:
   ```powershell
   # cd into PR39 HEAD 1aad1c... disposable clone
   python -B -m unittest discover -s tests -p test_public_corpus_nonpublic_urls.py -v
   python -B -m unittest discover -s tests -p test_public_corpus_invalid_unicode.py -v
   python -B -m unittest discover -s tests -p 'test_*.py' -v
   # cd into SAM PR15 HEAD efe9a... disposable clone/SAM/snapshot
   node --test tools/atomic-write.test.mjs tools/build-release-manifest.synthetic.test.mjs
   npm run build
   npm test
   ```
   Dependencies must already be installed offline or require explicit safe permission first; no paid Actions/auto install.
3. **Promotion/re-pin only after review**: if current heads remain stable and all 42 original file SHA agree with reviewed manifest, explicitly issue a new immutable manifest+runner contract pair and its fresh formal tests. Do not mutate the original frozen historical evidence or auto-merge PRs. If heads move again, repeat comparison.

## Gate status

- This interactive session actually committed 50-family full manifest guard, new 42-family one-shot executor, 42 synthetic guard/verdict/executor tests (not 42 historic real projects), and source/command/blobs 42/42 static verification.
- The **current moving** Wool/SAM heads are not authorized by old runner `EXPECTED`: an attempted `--run` with those SHA returns nonzero before real tests, **as designed**.
- Wool fresh independent 47-piece time-window first run TP1/FN3/25% recall and one cross-URL false-split are still red; true 09:30 signed local report `OUTPUT_NOT_CONNECTED`. SAM original61/522/T031 actual source gold, true direct/stdio MCP, Windows Node24/26 and full release install/rollback remain unaccepted. Historic `historical_recovery_closed=false` and `all_scheduled_run_logs_complete=UNKNOWN_SOURCE_UNAVAILABLE`.
