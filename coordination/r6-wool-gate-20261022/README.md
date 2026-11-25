# R6: R5 guarded discovery has no WoolRadar source test root

Date: 2026-10-22. Scope: review-only isolated negative reproduction, **no product integration**.

R5 correctly blocks an absent `tests/` directory, but the exact PR113 source
(`396ce94e3510d4f09f951b0a973716c3c343bc93`) has **16 tracked Python
test files under `.github/relay/` and `coordination/`, and no root `tests/`**.
An immutable `git archive` of that source was tested with R5's guarded candidate:
gate process exit 0, inner status `BLOCKED`, error
`INVALID_TEST_DISCOVERY_ROOT`. The original exact source worktree stayed clean.

Reproduce in a **clean local checkout of exactly PR113 HEAD**:

```powershell
python -B -X utf8 coordination/r6-wool-gate-20261022/reproduce_pr113_r5_layout.py --checkout PATH_TO_EXACT_PR113_CHECKOUT
```

The script reads the Git tree, creates an isolated temporary archive, checks
test-file presence, executes the R5 gate, and saves a redacted JSON result.
For local coordination workspace use `_outbox` equivalent paths instead of
`coordination`.

**Implication:** a real WoolRadar source test cannot receive R5 PASS under
this layout. A production-integrated gate must discover the reviewed test
roots and enforce test identity, nonzero counts, status and process exit. A
wrapper exit 0 by itself is not acceptance. R5's 5/5 synthetic assertions
remain valid, and all R5 artifacts remain review-only.

The optional local R6 dual-root experiment has **not** passed: on this same
PR113 source the relay suite discovered 72 tests but failed (17 failures and
1 error in a direct reference CLI run). Historical 72/72 green evidence under
another execution setup is retained, not promoted as current CI status.
This diagnosis does not claim the cause of the discrepancy. Hosted GitHub
Actions runner startup, final PR integration and C1–C5 remain unverified.
