# Current-head Codex acceptance delta — source patch after frozen 50-family manifest

**Purpose:** keep the [50-family immutable original manifest](./HISTORICAL_80_PERCENT_CODEX_JOBS_20261017.json) and its [current runner](./HISTORICAL_CODEX_BATCH_RUNNER_20261017.py) honest, while giving local Codex explicit **new** source-head acceptance steps for the interactive code changes made after the snapshot. This is a one-time interactive coordination handoff, NOT a Scheduled writer or a claim of Windows test success.

## Immutable heads and why the existing batch runner must not be used against a new head

| Unit | Frozen 50-family manifest SHA | Latest Draft candidate SHA, cold-read 2026-10-17 | Evidence state |
|---|---|---|---|
| WoolRadar PR39 | `80c5ea18769c1312e5be5fd99a39e4f3d498c64f` | `1aad1c98584dd2c7291ada30ef71e813dbfedd50` | producer host-scope + malformed UTF-8 code, current true focused **21/21 pass** Linux3.13 |
| SAM PR15 | `82bf36efa90cced8dafb56502812eb49f40515f3` | `73a3ff3c6f8fd33fdeec05ea8b9511c73c91fa58` | isolated original release atomic6 + synthetic manifest builder5 + prevalidated 0.4.1 migration7 = **18/18 pass** Node22 |
| historical Coord PR11 | `27796df5f9847c1bb5d48d2a445e418dfb3d8e96` | unchanged in this check | historical Windows57 provenance, new clean exec still needed |

**Do not simply overwrite one of the three SHA constants.** Current original runner/JSON manifest both intentionally refuse any other SHA. Changing only the JSON leaves runner preflight failing; changing only the runner leaves JSON provenance stale. Prior direct GitHub runner source write was safety-blocked. The two historical snapshots are still valid as **old** frozen evidence; to run new code against the latest HEAD, either run the explicit manual commands below in new isolated worktrees, or after owner review update *both* runner and manifest together, with missing/mismatching-manifest negative tests before execution. Do not silently claim `80c5` tests cover `1aad`, nor `82bf` tests cover `efe9`.

## Batch A: WoolRadar — current true source 1aad1c...

In a new, clean, disposable worktree **outside the production Windows installation**, check `git rev-parse HEAD` exactly `1aad1c98584dd2c7291ada30ef71e813dbfedd50`. Then:

```powershell
python -B -m unittest discover -s tests -p "test_public_corpus_*.py" -v
python -B -m unittest discover -s tests -p "test_developer_grant_*.py" -v
python -B -m unittest discover -s tests -p "test_*.py" -v
python -B -m unittest discover -s independent-quality/public-corpus-blind-dedup-20261016 -p "test_*.py" -v
python -B -m unittest discover -s independent-quality/delivery-bridge-20261016 -p "test_*.py" -v
```

Run each command once; overlapping formal tests are not distinct additional tests. **Never count full suite and subset twice.** Keep full stdout/stderr and exit code, compute SHA256 for each log, and report new total/failures/skip counts. If repo lacks a dependency, `BLOCKED_DEPENDENCY` with exact missing package, not green. If a test touches actual accounts/report source/PLC/SQLite, stop and use isolated synthetic inputs only.

New precise real source identities: `core/public_corpus.py` blob `383f3ad38930863fe5311260f8869b1ca65564ef`; host test `5dc8307b2666c3ba670f7d04ee260c7ce7f02326`; malformed Unicode test `e26a0ba16033de49c8544c2b03093ad103787e83`; prior original timestamp test `c90cb9eab13230d4c4086e51c9c1b3f6f034dd62`. Current isolated real exact producer Python3.13 did **21/21 pass**; baseline old production exact blob `6768c5d1a2229c6b5410c70de270ef49dc65bc26` actually failed host formal test 23 *subtest assertions* (6 unittest methods); intermediate producer also failed all 5 Unicode tests. [Full red/green source receipt](https://github.com/lu403369069lu-prog/WoolRadar/blob/chatgpt/wool-historical-integration-20261017/independent-quality/public-corpus-blind-dedup-20261016/PRODUCER_HOST_UNICODE_REAL_RED_GREEN_20261017.md).

After formal suite, owner still needs a **truly new** independent public time-window gold corpus, direct source eligibility check and 09:30 approved signed report bridge. Historic first holdout TP1/FN3 recall25% and cross-URL true campaign false split1 remain red and may not be relabeled as green.

## Batch B: SAM — current true source efe9a...

In a new clean, separate copy of [PR15](https://github.com/lu403369069lu-prog/YinQieJi/pull/15) exact `73a3ff3c6f8fd33fdeec05ea8b9511c73c91fa58`, use `SAM/snapshot` as CWD. **Do not run `build-release-manifest.mjs` against its default real Windows registry paths.** The added safe test `tools/build-release-manifest.synthetic.test.mjs` creates its own temp synthetic Git/registry/card/artifacts/automations and uses `SAM_ENGINEERING_REGISTRY` pointing to its own fixture.

```powershell
node --test tools/atomic-write.test.mjs tools/build-release-manifest.synthetic.test.mjs tools/migrate-release-041.synthetic.test.mjs
node --test ../independent-review/20261016-0904-audit-coverage/*.test.mjs
node --import tsx --test ../independent-review/20261016/rooted-source-authorization.test.ts ../independent-review/20261016/glob-case-parity.test.ts ../independent-review/20261016/glob-ripgrep-572-matrix.test.ts
npm run build
npm test
```

For Windows Node24 and Node26 execute both runtime matrices **only if already installed and needed dependencies are available safely**. Do not auto-install paid network dependencies or touch TwinCAT. Record the exact new head for each test, and distinguish native MCP direct tool entry from stdio MCP transport; both are unverified despite isolated module tests. Avoid wildcard scripts that resolve to unrelated source if working directory changed: verify `test` and `tools` files are those from the exact head before running.

Original precise release sources for 11 Linux tests: `tools/atomic-write.mjs` blob `de5a34c509740e4eac44656379c7b6ed52ca5329`, `tools/atomic-write.test.mjs` blob `7acb5d3fa6b645487cf1d2e4d5d9092c64bb8e89`, `tools/build-release-manifest.mjs` blob `0ed0bfb55851a092b73c0e30856f3926ce2f2b20`; new exact synthetic builder test `5b8e99131748269ed7046ffd0d2396da3d30bc79`. Original 6 + new5 test locally exact **11/11 pass exit0**; [formal detailed evidence](https://github.com/lu403369069lu-prog/YinQieJi/blob/chatgpt/sam-recover-claim-audit-types-20261017/SAM/independent-review/20261016/H17_REAL_RELEASE_BUILDER_11_EXACT_20261017.md).

This H17 test is a **single manifest atomic file**, not transaction for pointer `current.json`, dist, skill install or rollback. Real 61-question source gold only 10 supported, 522 independent gold and T031 question/source mapping remain unsolved.

## Receipt schema and disposition gates

For each unique invocation report `repo | exact_head | batch | command | OS+runtime | exit_code | tests | passed | failed | skipped | stdout_sha256 | disposition | linked_family_ids`. Use `PASS` only if run actually returned exit0 and nonzero tests with no failures/skips (or a successful intentional build, labeled `BUILD_PASS`). `ERROR`, `BLOCKED`, `NOT_RUN`, `GOLD_FAILED` and `NEEDS_APPROVAL` must remain distinct. Never write user-private full logs/sources/credentials; sanitized summary is enough.

Return **Wool** to Issue [#2](https://github.com/lu403369069lu-prog/WoolRadar/issues/2), **SAM** to YinQieJi [#1](https://github.com/lu403369069lu-prog/YinQieJi/issues/1) and final integrated decision to Wool [#3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3). Do not auto-merge PR37/38/39 or SAM PR9/12/13/14/15 in parallel; preserve Codex V3 main owner/lease/fence/CAS and leave all candidate PRs Draft until human review. No current source work changes Windows PLC, bank/card accounts, notifications, automations, or local production reports.

`historical_recovery_closed=false`; `42 READY_FOR_LOCAL_CODEX` was handoff availability, not 42 PASS. The H17 and producer changes in this delta are **new real code/test contributions** beyond the 50-family evidence classification.

## Subsequent source delta: actual 0.4.1 migration partial-overwrite red→green

At the latest S15 head **`73a3ff3c6f8fd33fdeec05ea8b9511c73c91fa58`**, H17 migration source `tools/migrate-release-041.mjs` full exact Git blob **`893c9970c01bd99ffdb31f18282e68261902f705`** replaced old actual blob `6bbba264b4e963ebba0e7028b23e295b472f5e95`. The old script actually failed four of five newly created formal tests (exit1) by overwriting existing 0.4.1 teacher-eval before validating missing/invalid source claim audit, C001-K05 or teacher-evidence. The new version validates *all predictable* 0.4.0 data before touching 0.4.1, rejects invalid UTF-8, and uses the original atomic metadata helper individually for four target files. Exact new migration formal test blob **`1031e5662984df8314b234492eabc39816e75ded`**, seven methods including BOM/CRLF byte preservation. Current true Linux Node22 release tools **18/18 pass, exit0**; log SHA256 `b2bafad0e2d42d5565d15b3c8b49f4b9ae810a7a63cabf6aa9a358f0851f7f8e`. [Full current original-red/current-green evidence](https://github.com/lu403369069lu-prog/YinQieJi/blob/chatgpt/sam-recover-claim-audit-types-20261017/SAM/independent-review/20261016/H17_MIGRATION_SOURCE_RED4_GREEN16_20261017.md).

**Explicit limitation:** per-file atomic rename is not a four-file/current.json transaction. No real release pointer activation/rollback, Windows24/26 or full installed source package was tested. Codex must inspect all candidate files and approved source digests before promoting `current.json`. Keep `HISTORICAL_RECOVERY_CLOSED=false`.
