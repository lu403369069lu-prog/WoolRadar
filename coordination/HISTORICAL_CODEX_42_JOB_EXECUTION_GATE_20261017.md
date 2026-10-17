# 42-family historical batch acceptance: executable gate, exact SHA source, synthetic 42-pass receipt

**Provenance:** user-authorized interactive ChatGPT/GitHub writes on 2026-10-17, no ChatGPT Scheduled write, no Codex/Work quota, no production Windows/PLC/SQLite/credentials, no GitHub Actions runner or automatic merge.

## Baseline and numerator

Original historical family count **50**, user 80% engineering target **40**. Machine list presently includes **42** `READY_FOR_LOCAL_CODEX` and **8** gated requiring new approved real sources/sensitive-owner decision/Scheduled limitation; `READY` means **executable handoff, not fixed or accepted**. The original 50 are not all closed and release-acceptance 80% has NOT been demonstrated.

Source snapshot locks:
- WoolRadar standalone unified [Draft PR39](https://github.com/lu403369069lu-prog/WoolRadar/pull/39): `80c5ea18769c1312e5be5fd99a39e4f3d498c64f` — **15** ready histories.
- YinQieJi-SAM [Draft PR15](https://github.com/lu403369069lu-prog/YinQieJi/pull/15): `82bf36efa90cced8dafb56502812eb49f40515f3` — **21** ready.
- WoolRadar historic relay [Draft PR11](https://github.com/lu403369069lu-prog/WoolRadar/pull/11): `27796df5f9847c1bb5d48d2a445e418dfb3d8e96` — **6** ready.

All 42 command targets were independently compared **against these immutable three GitHub Git Trees**: `verified_test_path` present, expected `verified_test_blob` matches actual Git blob and `run_command` resolves to exactly that test file. **42/42 path+blob+argv agreement; 0 mismatches, 39 unique literal test commands**. This is preflight *remote artifact identity verification*, **not test execution**.

## Actual code shipped (no more plan-only handoff)

The former executable `HISTORICAL_CODEX_BATCH_RUNNER_20261017.py` original Git blob `8dd067055447eb19afde71a707466d02c6526ec0` did not check the adjacent 50-family JSON before execution. This was an actual fail-closed validation omission. Its source was corrected (commit [`6e65c215`](https://github.com/lu403369069lu-prog/WoolRadar/commit/6e65c21510e774c49e0a32f43c87de056cfa18c1)) to Git blob **`d60f10c5c01d876b8ab663ad31f9c1dd703b8323`**, implementing pre-execution checks across **all 50** IDs for duplicates, project/ref/repo mismatch, wrong ready count, missing run commands, bad dispositions or missing manifest. Validation is before `preflight` or any test process.

New authentic [42-job executor](https://github.com/lu403369069lu-prog/WoolRadar/blob/chatgpt/scheduled-checkpoint-contract-20261016/coordination/HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py), commit [`47008ed2`](https://github.com/lu403369069lu-prog/WoolRadar/commit/47008ed26fc3bb49203af35571d5e1e83b668d86), exact source Git blob **`167d415c92dca86d1211c6fa2541c5b84c398ecf`**:
- requires adjacent protected **50/42/8 manifest** (blob `96c71aad1e26e5bf7b0aa12ac1e4b62ddcb98744`), immutable SHA of selected repo and clean disposable clone;
- validates **each local target** and `HEAD:test_path` SHA against the reviewed job blob, allows only tightly specified `python -B -m unittest discover ...`, `node --import tsx --test` and `node --test` commands via argv with `shell=False`; reject arbitrary `-c`/shell concatenation, wrong test path or escaping symlink;
- maps **42 histories → 39 distinct command executions**, one shared command yields one log digest, then maps that result into each family without counting the same run twice;
- default **DRY_RUN**; `--run` is a deliberate user-local Codex decision, no package installation or repository checkout/push/merge;
- emits local-only `receipt.json` with `source head | family | command | actual exit | validated exit | TAP/unittest counts | log sha256 | status`, plus local logs; logs **must be inspected and redacted before being shared with GitHub**.

The old wide-coverage runner remains available as separate option for full suites; the new one executes the specific 39 per-family reviewed tests and does not equate wide aggregate counts with family coverage.

## Actual isolated tests and precise boundary

Three official regression files committed to the checkpoint branch:
1. `tests/test_historical_codex_manifest_contract.py` blob **`f29ff052831e8437c45a70e106d3245c2c3ccb97`** — 12 synthetic pass/reject cases across all 50 family manifest contract (commit `da215c808141a3257e19d5c2f065e6d54eb12c72`).
2. `tests/test_historical_codex_runner_verdict.py` blob **`433a3d31bb0ef53294897d2beb22b57f571dbece`** — 14 synthesized Python/unittest, Node TAP and bad/missing count cases (commit `733228a81523aa1f265b67326780419d3630a804`).
3. `tests/test_historical_codex_42_executor.py` exact Git blob **`03a446ab7db3e4e20f8187c2244ed0fb6539ee14`** — 16 exact executor tests (command whitelist, Python+Node TS/MJS, real disposable Git blob source, wrong source, symlink escaping, no-shell, dedup, **three actual synthetic subprocess executions testing PASS/zero-tests/failing-exit**), commit `05bd6a47aa728043119242fd1481e6c61227ddb9`.

Local Linux **Python3.13.5**:
```bash
python -B -m unittest discover -s tests -p 'test_historical_codex_*.py' -v
```
**42/42 synthetic guard/executor methods pass, 0 failures, exit 0**; raw local log SHA256 **`50b1f3c568ad8b95e35af154a41791fcc06ef54e6ae32411dddd960608eac2e0`**. The executed new executor source byte string was **git-hash-object checked to be exactly remote blob `167d415...`**; the guard/verdict helpers were source-matched with complete corresponding original GitHub function text in an isolated minimal test module. **The entire remote 13KB legacy runner was NOT cloned/imported in the local run**, and the **actual repository-installed checkpoint tests have NOT been executed on the user's Windows machine**. The 42 TAP/unittest method count here is an unfortunate coincidence and **does not mean any of the 42 historic project jobs passed**.

An initial local-only import error in the standalone executor and two local-only mock-module omissions were repaired before final green tests and the committed exact source; neither was presented as a remote original defect. The full 42 test log includes 2 disposable real Git init/commit tests and 3 real synthetic subprocess receipts; no private data.

## Direct local Codex action and gating

Use the [handoff's literal PowerShell commands](https://github.com/lu403369069lu-prog/WoolRadar/blob/chatgpt/scheduled-checkpoint-contract-20261016/coordination/HISTORICAL_80_PERCENT_CODEX_HANDOFF_20261017.md). Script **and** manifest must be together in checkpoint clone; `--repo` points to independent clean PR39/PR15/PR11 worktree at exact SHA. First dry-run all three; only then add `--run`. Do not run a checkpoint-only script in PR39/PR15 repo where it is absent. In each `receipt.json`, map results to the original 15+21+6 histories, avoid counting shared tests twice, publish only non-sensitive summaries to [Wool Issue #2](https://github.com/lu403369069lu-prog/WoolRadar/issues/2), [SAM Issue #1](https://github.com/lu403369069lu-prog/YinQieJi/issues/1) and [coord Issue #3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3).

**Still not verified**: user-local native Windows full test suite, Node24/26 build and real MCP direct/stdio, SAM original61/522 approved source gold/T031, Wool independent fresh 47-sample recall and actual local signed daily-report bridge, coordinator genuine unattended Scheduled GitHub write. Prior 4 hourly engineering automation tasks remain disabled, daily public brief unchanged. `historical_recovery_closed=false`; no user request for automatic merge, production deployment or account redemption.
