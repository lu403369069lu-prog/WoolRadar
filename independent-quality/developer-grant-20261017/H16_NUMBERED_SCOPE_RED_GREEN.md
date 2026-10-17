# WR-H16: numbered-list developer grant scope — exact Git blob red/green

Date: 2026-10-17. Status: PARTIAL_DRAFT_CODE_TESTED; FULL_BUSINESS_ACCEPTANCE_NOT_RUN.
Source is synthetic-only. No official activity claimability, account/region/card terms, real feed capture or production deployment was touched.

## Exact byte provenance

- Old actual core/developer_grants.py Git blob: ce53bfdcfb75d1f9b4927f0dad762a20b9bd5bc2.
- New actual core/developer_grants.py Git blob: 8543c9c63543645e36fcd0ed3fea396081c258f7.
- Existing committed tests/test_developer_grant_project_scope.py blob: 26193c5b92c69c41b53a22ccc1cbb6c008ec2545.
- New committed tests/test_developer_grant_numbered_scope.py blob: 9263786f4165696a4647fbbd1f62b6a96ea33110.
- All four standalone local source/test files were reconstructed from GitHub and each verified by git hash-object to match the exact blob above before running. No test logic altered between red and green.

## Actual local execution (Linux/Python, no external services)

Command with each exact producer source:
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest discover -s tests -p 'test_developer_grant_*.py' -v

| Input source | Result | Exit | Log SHA-256 |
|---|---|---:|---|
| Old detector blob ce53bfd... with existing 11 plus new 6 tests | 17 methods, 3 failures: numbered 1., numbered 1), Unicode bullet false-positive | 1 | df8ea02675e591fd3f1e1ace361063eb5e14ee91c7248e7f498afe3f6d4644f1 |
| New detector blob 8543c9c... with identical tests | 17/17 pass | 0 | edce19c7209a0f31f246cef87165b04fbbaa6149eb6fa5676a8f6d1c10f52936 |

Six new formal contracts: numbered 1., parenthesized 1), Unicode bullet cross-project separation; positive complete numbered project; global closure/denial priority; fee-required negative. Previous 11 source-scope tests remain green. No private real-world source was read or saved. Raw local logs are not uploaded.

## Limitations / Codex next tasks

1. This tests only actual full developer_grants module plus 17 focused formal methods. It does NOT assert whole collector, Windows, PR39 full suites, new independent 47+ public-source recall, dedup, or notification/delivery is green on new HEAD. Previous Linux 58/58 was on older PR39 SHA, not this patch.
2. Need Windows clean worktree exact new PR39 HEAD, whole tests plus held-out sampler and delivery-boundary suites; no auto-merge or production writes.
3. True business gates remain TP1/FN3 recall25%, one crossURL false split, and 09:30 OUTPUT_NOT_CONNECTED. No synthetic green waives these.

All changes stay on Draft PR39; do not separately stack old PR37/PR38.
