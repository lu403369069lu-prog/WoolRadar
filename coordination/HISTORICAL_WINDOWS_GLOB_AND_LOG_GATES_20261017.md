# Historical 42-family executor: native Windows gates and exact log integrity

**event_key:** `history-42/win-rg-and-raw-log-preflight/20261017`  
**Actor:** authorized interactive chat; independent code/test writes, **not** Scheduled autonomous GitHub writes.  
**Main context:** [42-task handoff](HISTORICAL_80_PERCENT_CODEX_HANDOFF_20261017.md) and [manifest](HISTORICAL_80_PERCENT_CODEX_JOBS_20261017.json); 50 family classification, 42 READY, 8 external. Frozen SHA refs remain **unchanged**: Wool PR39 `80c5ea18769c1312e5be5fd99a39e4f3d498c64f`, SAM PR15 `82bf36efa90cced8dafb56502812eb49f40515f3`, Coord PR11 `27796df5f9847c1bb5d48d2a445e418dfb3d8e96`.

## Actual new code defect fixed, NOT a 42-test success

`HISTORICAL_CODEX_42_TARGET_RUNNER_20261017.py` previously invoked child tests with `text=True, errors='replace'` and then `stdout.encode('utf-8')`. A subprocess that emits invalid UTF-8 bytes was silently reencoded with replacement bytes `EF BF BD`. Its purported raw log and SHA256 would **not** match original process output. This was reproduced in real Python3.13 child subprocesses using bytes `FF FE` followed by a valid unittest summary: old text capture hashes different bytes, new binary capture hashes exact bytes; **3/3 independent focused real subprocess tests PASS** (local source scope, not the new repo's full test module).

Actual commits on this checkpoint branch:
- `96f9376e4cdc6143f6d8a04f9fdabe8cb2a9d96e` changed child capture to raw `stdout=PIPE` bytes; exact file logs and SHA256 now preserve original bytes; malformed UTF8 logs fail closed.
- `7d34117f74aef33b294e1d90779e2a18b1a7aa98` extracted `audit_raw_log(raw, exit_code)` for independently testable verdict.
- `299767d59c84648268039eeed1ae0d29b7856266` added 3 formal `ExactChildBytesTests` to existing `test_historical_codex_42_target_runner_20261017.py`, blob `af52eaabdfc23450f90e35f6accc9118fb51b5b4`. **These actual GitHub test methods have not been run as a whole 42-runner formal suite.** The 3/3 above are an independent exact-behavior reproducer, not falsely attributed to that full suite.
- `58a125b028c2b739d1c883729e27041e7b02de5d` sets `PYTHONIOENCODING=utf-8` in child env to avoid Windows cp936/cp1252 stderr producing malformed bytes. Current 42 runner Git blob `525d4bba4c422e21fe3295dc03c24daf6fe7df32` (unless subsequently changed; always re-read before claiming).

## Broader historical executable-file audit

Every one of **39 distinct test paths** in the frozen 42 READY jobs was refetched directly at its per-project immutable Git commit and compared with the corresponding `verified_test_blob`: **39/39 exact matches**. This is actual independent remote Git source integrity inspection, not running those tests. Their executable shape and immutable manifest gate were previously checked: 50 jobs (42 READY/8 external), 39 distinct commands, zero SHA or target path mismatch after fixing old WR-H15 command.

Four test files explicitly contain a skip gate:
1. **SAM-H06** `SAM/independent-review/20261016/glob-ripgrep-572-matrix.test.ts` line 10 **always skips on Windows** (`process.platform === 'win32'`); line 12 additionally skips if `rg` unavailable.
2. **SAM-H18** `SAM/independent-review/20261016/glob-case-parity.test.ts` line 10 **always skips on Windows**; line 13 also skips if `rg` unavailable.
3. **SAM-H10** `SAM/snapshot/test/canonical-fail-closed.test.ts` line 43 may skip on Windows when junction/symlink creation is blocked.
4. **SAM-H20** `SAM/snapshot/test/source-qualified.test.ts` line 184 may skip when symlink permission is missing.

The 42-runner/receipt guard correctly rejects skip outcomes, but **SAM-H06 and H18 cannot both PASS using only the existing POSIX tests on native Windows**. Do not claim 42/42 green just because 42 paths exist.

## Actual new no-skip native Windows acceptance program

A separate, **SHA-locked**, read-only [native ripgrep test](HISTORICAL_WINDOWS_NATIVE_RIPGREP_PARITY_20261017.mjs) was committed as `0fec57aa91dab0ab5d2fb3719dd2016a1dad1e43`, exact remote/local Git blob **`90db7fbb00d4037b793a48aa355b1343f791e205`**. This separate coordination-branch test **does not change** the frozen SAM PR15 checkout SHA or 42-task manifest.

It checks the SAM checkout's real `git rev-parse HEAD = 82bf...`, clean tree, canonical top-level and **real `source-policy.ts` Git blob `0cb6ead...`** before importing the actual TS `isExcluded` from that immutable source and comparing **26 globs × 22 synthetic filesystem paths = 572 actual native ripgrep 14.1 assertions**, no platform skips or silent `rg` fallback. It never reads actual private PLC cards or writes into the checkout. Test only uses temp directory synthetic files. Run **once on Windows Node24 and once Node26** (no auto runtime installation). On absent native `rg` or policy mismatch, deliberately fail.

```powershell
$env:SAM_CHECKOUT_ROOT = "C:\temp\sam-history-qa"
git -C $env:SAM_CHECKOUT_ROOT rev-parse HEAD   # must be 82bf36efa90cced8dafb56502812eb49f40515f3
node --version                               # record v24, then separately v26
rg --version
node --experimental-strip-types --test C:\temp\historical-handoff\HISTORICAL_WINDOWS_NATIVE_RIPGREP_PARITY_20261017.mjs
```

**Independent local harness validation actually run** in isolated Linux Node22.16.0 / ripgrep14.1.1 against a disposable stand-in Git repository implementing the relevant exclusion semantics (pinned SHA/blob substituted **only in this isolated fixture harness**, never in the committed frozen program):
- 572 comparisons, **1/1 TAP formal method PASS, exit0**, log SHA256 `07a67954cc75e9e5be88b495e5367c06f4cae0dacb36a84ed7a84e236481aba1`.
- Replaced case flags in stand-in TS with an unconditional `'i'` and recomputed stand-in test pins, then **1/1 TAP FAIL, exit1**, identifies `secret.txt` erroneously excluding uppercase `Secret.txt`; raw log SHA256 `c13173872191450db53980336b11787ee0163c7a31561425e66cf54efa13a74d`.
- **NOT** an execution against real exact SAM source on Windows; that is the next authorized Codex gate. Existing separately documented POSIX SAM actual-source 572 parity tests do not prove Windows behavior.

## True remaining engineering scope

Need full 42 task source module tests on frozen code: formal 23+3 42-runner tests and 18 receipt-guard tests remain `SOURCE_COMMITTED_NOT_FULLY_RUN`; SAM Node24/26 all package, zod cards.ts, true direct/stdio MCP, 61+522 human source gold, Wool unseen 47 new public blind recall, genuine 09:30 same-SHA report and coordination unattended Scheduled-GitHub permission all remain unresolved. This is **one security/test-harness repair and a native Windows path**, not 80% feature or release completion. No auto-merge, paid Actions, Codex/Work quota, production Windows/PLC/SQLite or user secrets used.
