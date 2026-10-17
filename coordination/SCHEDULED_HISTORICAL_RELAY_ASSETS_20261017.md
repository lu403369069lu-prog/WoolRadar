# Third track: historical coordination, dispatcher and inter-agent relay — 2026-10-17

This is a **separate historical engineering track** previously omitted from the WoolRadar 19 discovery/quality family list and SAM 24 family list. These artifacts are in the WoolRadar private repository and derive from past ordinary interactive and Codex development, sometimes informed by Scheduled QA. **Do not attribute PR creation to unattended Scheduled execution.**

## Seven distinct asset families (COORD-H01…H07)

| Key | Real remote artifact | Observed evidence and gaps | Current archival status |
|---|---|---|---|
| COORD-H01 — zero-paid-API offline event dispatcher/idempotency | [Draft PR6](https://github.com/lu403369069lu-prog/WoolRadar/pull/6) HEAD `047c579dfaed1356b21495377b2e8958f37b6dbc`. `coordination/dispatcher.py` Git blob `8812fe1a1f9a0aa93783e8943fa0b2cf6835fb00`; `tests/test_dispatcher.py` blob `006099bae5a77c91df9734aba4ca9d4e66fa960e` (8 formal test methods). | Real files submitted, read back. No complete AI agent nor autonomous trigger implied. PR still Draft/unmerged. File absent from main WoolRadar PR23 HEAD `6babbe12727652e8626e0fe6f554eb01fecd4a30`. | STAGED_OLDER_PR_NOT_MAIN |
| COORD-H02 — PR event provenance adapter | [Draft PR7](https://github.com/lu403369069lu-prog/WoolRadar/pull/7) HEAD `73214fd39840f7cb1971c25f0dce1c932f9b027b`: `coordination/github_event_adapter.py` blob `3c9ffb3d33f01691ad69772e810991d36f276f20`; `tests/test_github_event_adapter.py` blob `04bbaa1374abdaf0929a5428a1230b2c93cc8a20` (8 methods). | Decoupled GitHub event adapter, not proof of private push runtime, authentication or actual unattended tasks. PR remains Draft. | STAGED_OLDER_PR_NOT_MAIN |
| COORD-H03 — webhook HMAC verification | Same [PR7](https://github.com/lu403369069lu-prog/WoolRadar/pull/7); `coordination/github_webhook.py` blob `40eab23c5a3f7875b02a0c637c826db00a218ba3`; formal `tests/test_github_webhook.py` blob `97432b303f7a75966d805459b6380e350d345635` (6 methods). | Verified actual Git blob and test files. No inbound public webhook endpoint activated and no credential used. | STAGED_OLDER_PR_NOT_MAIN |
| COORD-H04 — dispatcher dry-run side effects | [Draft PR8](https://github.com/lu403369069lu-prog/WoolRadar/pull/8) HEAD `8aca77dbc7acd0b78a35927bcb634a9c4d55b69f`, modified actual dispatcher and formal `tests/test_dispatcher.py` blob `0ce7492f65c89b73b010ab461310da1dcc21ccd4` (10 methods). | Corrected earlier dry-run accidental filesystem writes. Historical tests reported in PR, **not rerun at latest exact SHA in this session**. | STAGED_OLDER_PR_NOT_MAIN |
| COORD-H05 — V3/V5 durable relay and fencing, five synthetic rounds | [Codex Draft PR9](https://github.com/lu403369069lu-prog/WoolRadar/pull/9) HEAD `1440553f892676a938135e24938010d50cdd351a`, `coordination/relay.py` blob `3786463420e4c5cf9012db07d032fe20f0cfe2a9`, protocol blob `1e8c73f86201d0cbf8395f83854fc07ce9ec92e0`. Exact `coordination/ACCEPTANCE_REPORT.md` blob `8b243ffd02eda23b041fc9c346929138e9410cee`. | The **historic Codex-owner Windows report** states 50/50 unittest pass and five structured challenge rounds (real local Git conflicts, injected errors). Report explicitly says **full real ChatGPT agent handoff NOT proven and not deployed**, and some GitHub CAS rejection error class remained unclear. It must not be counted as five real independent agent production executions or as new tests run this interaction. V3 relay state is in separate branch with real owner leases; this PR is Draft/unmerged. | HISTORICAL_UNIT_GREEN_REAL_AUTONOMY_UNVERIFIED |
| COORD-H06 — return synchronization and fencing guard | [Codex Draft PR11](https://github.com/lu403369069lu-prog/WoolRadar/pull/11) HEAD `27796df5f9847c1bb5d48d2a445e418dfb3d8e96`: `coordination/relay_git.py` blob `ea0333d04afc3e686999289941ebfc88b389a138`; `tests/test_return_sync.py` blob `b86b930bce40b3b7ddf7e419ca84f2c15ddce48c` (7 formal methods). | Exact source/test read back. Historic receipt addresses ChatGPT return, actual local Git sync under controlled tests; still not proof of hands-free bidirectional production agent operation or GitHub Scheduled permission. | STAGED_OLDER_PR_NOT_MAIN |
| COORD-H07 — relay independent review/advisory | [Draft PR10](https://github.com/lu403369069lu-prog/WoolRadar/pull/10), [Draft PR12](https://github.com/lu403369069lu-prog/WoolRadar/pull/12), both open/unmerged, records independently auditing PR9/PR11. | Review notes can be reused as negative regression contracts. They are advisory only; no merged runtime, no transfer of Codex owner lease, no guarantee that the Scheduled tool could write repository Issues. | REVIEW_ARTIFACT_ONLY |

## Cross-PR integration risk

At source SHA `6babbe12727652e8626e0fe6f554eb01fecd4a30`, the central WoolRadar **Draft PR23 lacks** `coordination/dispatcher.py`, `coordination/github_event_adapter.py`, `coordination/relay.py`, `coordination/relay_git.py` (all verified by direct GitHub fetch attempted at this exact ref). Thus **the coordination system is not present in that main integration snapshot**. PR9 may have incorporated PR6–8 into its own branch; cherry-picking them independently could duplicate/conflict. PR11 may depend on PR9 source and tests. Do not blindly merge a stack or label operationally deployed.

## Safe next steps and limitations

1. Read latest current PR9 and PR11 source/tests and V3 owner/fence, compare branch ancestry with PR23 and independently validate the exact-source Python suite in a disposable environment before any integration.
2. Analyze private GitHub Actions minutes/runner cost and explicit user authorization before activating scheduling. A proposed Cron Draft is not a running daemon; ChatGPT Scheduled write restriction remains unverified.
3. Preserve the historic report's caveat: 50 unit passes and five **simulated** evaluation rounds are meaningful but not proof of real ChatGPT↔Codex unattended synchronization. V3 actual owner state may evolve independently.
4. This track is **historic code with genuine engineering value**; the user's request to prioritize historical assets means it must not be lost behind a list of URL/public-sample quality issues.

No auto merge, force push, paid runner, Work/Codex API, credentials, external webhook registration, Windows PLC/SQLite production changes, or background execution asserted.

## Exact branch ancestry and file-level dedup checked in this interactive turn

Real GitHub compare results at the immutable PR HEADs above, not guessed from titles:
- PR6→PR7: **ahead6/behind0**; PR7 extends PR6. Importing both wholesale is duplicative.
- PR7→PR8: **diverged** (PR8 ahead2/behind6); PR8 was an independent dry-run fix, not directly stacked over all PR7 adapter changes.
- PR8→PR9: **diverged** (PR9 ahead9/behind2); PR9 contains a **different dispatcher source** than PR8, not byte-identical.
- PR9→PR11: **ahead2/behind0**; PR11 extends PR9.
- Current main PR23 versus PR9: **diverged**, PR9 ahead17/behind157; current main versus PR11: PR11 ahead19/behind157. Both old coordination branches differ drastically from main.

Actual Git blob comparisons:
- `coordination/github_event_adapter.py` PR7→PR9→PR11 stays byte-exact `3c9ffb3d33f01691ad69772e810991d36f276f20`.
- `coordination/github_webhook.py` PR7→PR9→PR11 byte-exact `40eab23c5a3f7875b02a0c637c826db00a218ba3`; its test blob `97432b303f7a75966d805459b6380e350d345635` also exact across the three PR snapshots.
- `coordination/dispatcher.py` PR8 blob `fc3df29d9fbd4aab4c8149606b4353e69547df07` differs from PR9/PR11 `a4c51d33f1d3be998218a46090d84a137ecd9696`; formal `tests/test_dispatcher.py` PR8 `0ce7492f65c89b73b010ab461310da1dcc21ccd4` differs from PR9/11 `0565d808e63cbf84c61b7402994de8cec3821272`. **Do not claim PR8 dry-run fix survives unchanged in PR9**: an actual code comparison and a test are required. Both PR9 and PR11 are byte-identical for those dispatcher files.
- Main PR23 at exact source SHA `6babbe12727652e8626e0fe6f554eb01fecd4a30` still lacks the four coordination source files noted above.

This isolates a real historic integration decision: **PR11 is the latest PR9 relay descendant, but its base diverges 157 commits from main and the PR8 dry-run hotfix cannot be treated as included byte-for-byte**. Proper work is a carefully reviewed current-head overlay with tests and owner authorization, never blindly merge old PRs in number order. Do not spend private Actions runner minutes without user approval.

## Functional readback of diverged PR8 dispatcher dry-run branch

Despite different blob hashes, exact full file source on PR8/PR9/PR11 was read and compared around its `dispatch(..., dry_run=True)` branch. PR8 used an in-memory SQLite connection and copied existing state via `mode=ro` source, no parent `mkdir`. PR9 and PR11 **still have that same fail-safe algorithm**, with changes: use `contextlib.closing(sqlite3.connect(..., uri=True))` to ensure the SQLite source handle closes and guard rollback on `conn.in_transaction`. So H04 dry-run **protection semantically appears retained and improved in PR9/11**, despite not being byte-identical. This is **STATIC_REVIEW_SAME_DESIGN**, NOT a newly run dry-run temp-DB test at those exact SHAs. The latest PR11 test suite remains the formal integration gate; do not revert PR11's connection-close improvement by transplanting an old PR8 file.

The distinction matters: file SHA dedup alone would call the fix absent, whereas semantic diff identifies retained behavior with further hardening. Neither PR is merged into Wool main PR23; autonomous delivery remains unproven.
