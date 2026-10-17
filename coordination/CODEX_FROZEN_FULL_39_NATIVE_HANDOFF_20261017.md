# Codex: complete the 39 frozen historical test commands in disposable native checkouts

This handoff is for **the still-blocked native part**, not a new implementation project. Source of truth: [immutable manifest](HISTORICAL_80_PERCENT_CODEX_JOBS_20261017.json), Git blob `96c71aad1e26e5bf7b0aa12ac1e4b62ddcb98744`. Latest candidate source verification: [257 selected passing Linux tests, 127 overlapping Wool co-staged tests and pinned-log guard red-green evidence](SELECTED_257_GUARD_PINNED_LOGS_JOINT127_20261017.json). The 257 are 87 coordinator/external-gate/formal-guard methods + 82 Wool public corpus + 43 SAM synthetic migration + 45 Wool grant diagnostics. The Wool 127 joint cases overlap those 257, and are not additive. The 87 coordinator tests include the earlier 53 methods, 30 newly uploaded external gate/CLI methods and four pinned-raw-log red-green regression cases. Frozen jobs are enumerated by [29-command exact blocker matrix](FIRST_CATEGORY_29_FROZEN_COMMANDS_NATIVE_GATE_MATRIX_20261017.json).

## Safety and preparation

Use only separate **disposable, clean** local checkouts, never `C:\WoolRadar`, any user production app profile, PLC paths, or scheduled job state. Preserve the actual user machine and accounts. Do not use the moving PR41/42/43/17 candidate heads instead of the **old frozen commits**. Verify every head and clean worktree. Do not force-reset a user's existing repository; make new disposable clones only. Do not install network/npm dependencies without checking local pinned lockfile, provenance and policy, or pay for CI; if unavailable report BLOCKED. Keep private test inputs/logs on the local machine, only send sanitized aggregate/hash receipts. No auto-merge or production migration.

The three exact frozen source references are:

| Project | Repository | Frozen full HEAD |
|---|---|---|
| wool | `lu403369069lu-prog/WoolRadar` | `80c5ea18769c1312e5be5fd99a39e4f3d498c64f` |
| sam | `lu403369069lu-prog/YinQieJi` | `82bf36efa90cced8dafb56502812eb49f40515f3` |
| coord | `lu403369069lu-prog/WoolRadar` | `27796df5f9847c1bb5d48d2a445e418dfb3d8e96` |

The reviewed executor lives in **Draft PR42**, path `coordination/HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py`. It needs the adjacent formal receipt guard, batch contract and immutable manifest from the same reviewed PR branch. Do not copy only one runner and accidentally omit its contract. Git object identity for the new untracked-file hardening: runner `08af6d6304758399282d7b1799604089570c7b09` and regression test `458db80b575369a1a4614fe4de0225a7745ab3db`. Later coordination evidence-only commits do not alter this tested code.

## Exact runner invocation contract

First verify each snapshot by `git rev-parse HEAD`, verify `git status --porcelain`, validate the manifest exact Git blob, then for each of the three cases use the reviewed Python script:

```powershell
# In an isolated shell, set these to your NEW disposable clone paths.
$runner = '<reviewed-PR42-disposable-checkout>\coordination\HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py'
$wool = '<frozen-WoolRadar-checkout>'
$sam = '<frozen-YinQieJi-checkout>'
$coord = '<separate-frozen-WoolRadar-coordination-checkout>'

python -B $runner --project wool --repo $wool --expected-head 80c5ea18769c1312e5be5fd99a39e4f3d498c64f
python -B $runner --project sam --repo $sam --expected-head 82bf36efa90cced8dafb56502812eb49f40515f3
python -B $runner --project coord --repo $coord --expected-head 27796df5f9847c1bb5d48d2a445e418dfb3d8e96

# Run only after preflight/fixtures and dependencies are safely available.
python -B $runner --project wool --repo $wool --expected-head 80c5ea18769c1312e5be5fd99a39e4f3d498c64f --run
python -B $runner --project sam --repo $sam --expected-head 82bf36efa90cced8dafb56502812eb49f40515f3 --run
python -B $runner --project coord --repo $coord --expected-head 27796df5f9847c1bb5d48d2a445e418dfb3d8e96 --run
```

Expected immutable scope: **50 historical families = 42 READY + 8 gated**, deduplicated to **39 distinct runnable commands**. We have already executed **10** command strings on partial reconstructed Linux source trees (105 methods, 11 family mappings), but these **do not** replace full frozen worktree execution/strict guard acceptance. This native run must execute all 39 on exact frozen full trees; not only the remaining 29. In the chat environment **17** TSX commands failed dependency readiness because `tsx` was not installed (confirmed `ERR_MODULE_NOT_FOUND`), and **12** other Python command sets lacked complete mountable old checkout dependencies. Exact family/source blob mapping and commands are listed in the 29-command matrix.

## Required outcome and artifact

For every unique command and its mapped family IDs: record original argv/cwd, Git SHA, test source blob, interpreter/runtime versions, actual exit code, parsed tests/passed/failed/skipped, raw stdout SHA256, command and family status. Preserve raw process bytes. Run the official `HISTORICAL_CODEX_42_RECEIPT_GUARD_20261017.py` full grouped receipt review, not only per-log summary parsing. Emit the official final `guard-verdict.json` and `local_full_family_receipt_accepted` field; PASS may be declared only when that field is actually true. Failed/skipped/blocked families remain OPEN with failure explanation and retriable action. **Do not fabricate receipts for inaccessible commands**.

Separately classify the eight gated families (fresh independent Wool recall gold, 09:30 consumer/user approval, SAM human 61/522/source review and real MCP, coordination review) without inventing approvals or production tests. Link review results in [Wool Issue #2](https://github.com/lu403369069lu-prog/WoolRadar/issues/2), [SAM Issue #1](https://github.com/lu403369069lu-prog/YinQieJi/issues/1), and [coordination Issue #3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3) as **actual completed / partial / blocked**; no automatic merge.

## Tested CLI contract check (2026-10-17)

The reviewed Python executor `--help` was actually run on Linux and advertised precisely `--project {coord,sam,wool} --repo REPO --expected-head EXPECTED_HEAD [--run]`; the three PowerShell invocations above match the parser. The formal guard `--help` was actually run and requires `--receipt RECEIPT --manifest MANIFEST`. They do **not** infer approval from shell exit alone. The latest Linux integrated `python -B -m unittest discover -s . -p 'test_historical*.py' -v` against source-blob-matched executor, hardened formal guard, gate auditor and all selected tests completed **87/87**, zero skips, exit 0, raw log SHA256 `8f17cc9a40cb7afbc38d0f5fe46db921d6d9487375cb9591e88ef30b75d31d83`. That is not a full 39-command pinned snapshot receipt. Do not modify original frozen source hashes or execute in production.

## New formal raw-log guard safety contract (2026-10-17)

Original formal guard blob `072ba64688fcd479795620b870a803ddb29dc78b` allowed a raw log to be read after a prior path/symlink precheck and had no bounded file read. Three synthetic adversarial regression cases failed on the original blob (old 4-case suite 3 failures, exit 1, raw log SHA256 `998f077130fe60d636164c8ba2cd9e69e1536b6b5a903870a92faaa14f103442`); exact new formal guard blob `e51ec61d5fab3b82e763f8c147f73b3486123110`, tests `76acb4ca9a48a709af611a92ed9554c89165f77d`, green with all **87/87**.

The guard now rejects oversized raw stdout logs (8 MiB cap), FIFOs/nonregular files and path precheck/symlink replacement. POSIX uses descriptor-relative `O_NOFOLLOW`; Windows performs pre-lstat/opened-fstat/post-lstat file-identity comparison **as a narrower fallback that still requires a native Windows acceptance test**. When using the actual frozen 39-command Windows runner, capture blocked oversized or untrusted files as **BLOCKED/FAIL**, not as green. A candidate-source Linux unit suite still does **not** satisfy the whole-batch 39-command receipt, actual Windows requirements or business gold. No existing raw receipts were retroactively recertified.
