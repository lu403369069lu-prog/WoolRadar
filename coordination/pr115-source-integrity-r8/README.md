# R8: reject Git index flags that conceal modified source

This review-only follow-up addresses PR115 review comment 6335535293. It adds a
separate candidate; the historical R7 files and production gate remain intact.
No shared V3 ownership was claimed. Current source pin remains WoolRadar PR113
`396ce94e3510d4f09f951b0a973716c3c343bc93`.

## Demonstrated defect and change

R7's `rev-parse HEAD` plus `status --porcelain` accepted modified tracked tests
marked `assume-unchanged` or `skip-worktree`. Ten disposable-Git regression cases
against the original R7 produced **5 PASS, 5 FAIL, exit 1**. The five failures
are two hidden modifications, two unchanged abnormal index flags, and a hidden
modification introduced by a running test. The earlier seven-case RED run is
also retained locally (5 PASS, 2 FAIL, exit 1).

The R8 candidate rejects any nonordinary entry from both NUL-delimited
`git ls-files -v -z` and `git ls-files -f -z`. This fails closed on
assume-unchanged, skip-worktree and fsmonitor-valid entries. It checks before
execution, before each suite, and after all suites. A flagged checkout is
rejected even if its current bytes happen to match HEAD. No flags are cleared
or source files changed by the guard.

## Actually executed

Windows Python 3.14.5, `-I -B -X utf8`:

```text
python -I -B -X utf8 test_index_guard.py --module ../pr113-real-test-gate-r7/r7_verified_roots.py --report baseline-full-red.json
# 10 tests, 5 failures, 0 errors, exit 1 (expected RED)
python -I -B -X utf8 test_index_guard.py --module r8_verified_roots.py --report candidate-green.json
# 10 tests, 0 failures, 0 errors, exit 0
python -I -B -X utf8 r8_verified_roots.py --source EXACT_PR113_CHECKOUT --expected-sha 396ce94e3510d4f09f951b0a973716c3c343bc93 --output exact-pr113-results.json
# relay 72/72 + coordination integrity 4/4 + original coordination 48/48
# 124/124 PASS, exit 0; source status empty before/after, head unchanged
```

For the actual source suite, TEMP/TMP/TMPDIR were redirected to a writable
isolated scratch directory. As in R7, local synthetic Git push fixtures needed
the already scoped Windows Git process permission; no remote network push or
production resource was used by those fixtures. The 10 guard cases use tiny
synthetic three-test suites and are **not** an independent 124-test run.
`candidate-green.json` records nine gate observations because the wrong-SHA
case calls the gate directly; the unittest runner still executed ten cases.

## Limits

This fixes the reported index-flag bypass. It does not make a same-user mutable
checkout immutable or prove absence of ignored-file/import shadowing, malicious
Git config/hooks/filters, transient modifications reverted between checks, or
external binary substitution. Rejecting abnormal flags is not byte-for-byte
comparison against every committed blob. Use a reviewed isolated checkout.

Hosted Actions run 39738068112 at PR115's preceding head still reports failure;
its single returned formal job has `steps=null`. Commit check-runs reports
`annotations_count=2` but null title/summary/text. Annotation access is not
available through the current approved connector route, so the startup cause
remains unknown. No hosted CI pass is inferred from local 124/124.

Business acceptance, real same-SHA 09:30 consumer ACK, C1–C5, and the final V5
rounds remain unverified. No PR merge, live hook installation, or deployment.
