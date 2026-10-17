# Codex local verification handoff — fixed pre-October-17 historical batch

**Owner:** user-selected local Codex, run manually in the user's real Windows environment. ChatGPT interactive coordinator only authors isolated Draft PRs/Issue handoffs. **Do not auto-merge**. Historical scope is precisely the **50 immutable family IDs** in [HISTORICAL_FREEZE_50_20261017.json](HISTORICAL_FREEZE_50_20261017.json); new hourly outputs go to [NEW_SCHEDULED_RESULTS_INBOX_20261017.md](NEW_SCHEDULED_RESULTS_INBOX_20261017.md) and do NOT keep expanding this work batch.

**Read-only preflight:** before doing any work, get fresh PR HEADs; the immutable SHA values below are starting identities, not permission to force-reset newer changes. The V3 current Codex owner/fence is held on Wool main PR23 and SAM main PR5; do not change the other owner's locked branch. Execute on a clean **separate detached local worktree** or other isolated directory, not production. Preserve or sanitize the current source corpus, Windows usernames, tokens, email, card numbers, PLC secrets and 522 user-private gold. **Only sanitized result counters and test file SHAs may be committed**.

## Batch A — YinQieJi/SAM original full runtime compatibility (priority P0)

**Source:** [SAM independent Draft PR15](https://github.com/lu403369069lu-prog/YinQieJi/pull/15) originally HEAD `e0247b42e9878c3363269c5a322090b8720cabab`, plus main [SAM PR5](https://github.com/lu403369069lu-prog/YinQieJi/pull/5) HEAD `5aeb852577cc53da76f9a0b5e78dfef63a83a35b` (compare; no automatic merge). PR15 includes PR12 source-root/ripgrep fix, PR13 enum, PR14 WorkBuddy, PR15 typed claim and actual reviewed-cards-SHA gate. These are **Draft**, not released.

In a separate *YinQieJi* git checkout, review PR15 changed files and clone/fetch its branch without changing main:
```powershell
git fetch origin pull/15/head
git worktree add --detach ..\sam-history-validation FETCH_HEAD
cd ..\sam-history-validation\SAM\snapshot
node --version
npm --version
npm ci
npm run build
npm test
```

Record actual `$LASTEXITCODE` for each, exact `git rev-parse HEAD`, package lock SHA and the full formal test denominator. Repeat on **Node24 and Node26** in isolated terminal environments; do not claim Windows parity from Linux Node22. Running `npm ci` installs repository-declared dependencies in the **test worktree only**; it must not touch installed user/global Skills.

**Focused, mandatory four historical fixtures:** `test/cards.test.ts`, `test/card-index.test.ts`, `test/quality-gates.test.ts`, `test/inheritance-source-gate.test.ts`, `test/iteration-fixes.test.ts` and new `test/reviewed-artifact-byte-binding.test.ts`. Under `npm test` assert a review's `reviewedArtifactSha256` matches **the raw full JSONL cards file bytes**, not backing TwinCAT/Axis source SHA. The three most recently corrected old fixtures were uploaded to PR15 (commits `00a5897`, `066cf3f`, `a671c0a`); old fixed 64hex placeholders still deliberately remain in *negative* tests and should fail. **Do not loosen real production gates to make fixtures green.**

Run the source-policy matrix on Node24/Node26 in Windows for actual local `rg --version` and `rg --files` case/glob behavior. On Linux Node22 the exact formal source suite is now 39/39 with one formal glob test containing 572 actual assertions; **that is not Windows verification**. If real ripgrep and JS matcher disagree, attach *synthetic pattern + path only* and fail the permission gate, never broaden reads. Record V3 owner/fence and exact failure.

**MCP direct+stdio (offline synthetic only):** run project-declared `npm run smoke:interfaces` after build and the repo's `test/workbuddy-rank-order.test.ts`, `test/workbuddy-filter-fallback.test.ts`, `test/workbuddy-nonempty-lines.test.ts`, `test/workbuddy-response-contract.test.ts` under the supported `node --import tsx --test ...`. Use explicit *synthetic local registry and safe offline files*, run direct API and StdioClientTransport protocols separately, record tool names, status, exit and redacted test logs. **No TwinCAT/XAE activation, download, ADS/PLC connection, real WorkBuddy script/database/index changes.**

For [SAM-H17 release-state](https://github.com/lu403369069lu-prog/YinQieJi/pull/15), inspect `tools/build-release-manifest.mjs`, `tools/migrate-release-041.mjs`, `test/release-040.test.ts`, `src/manifest.ts`. **Do not execute migration on real 0.4.0/0.4.1 knowledge release or update current.json**. Copy only synthetic test fixtures to disposable worktree and check manifest/current pointer atomicity, checksum binding and rollback. Dist installation/reinstall/upgrade rollback must be dry-run in a disposable `HOME`/profile, never user global ~/.codex.

For SAM-H08/H11/H24, inspect the current real 61-question and 522 approved-source records **locally only**. Known prior status 10/61 source-bound answered and 51 refused, with T031 Axis/FSM evidence mismatch. Do not upload raw questions, full records, source code or identifiers to GitHub. Publish only sanitized aggregate counts, exact source-file hash labels when approved, and an explicit refusal/mismatch verdict with human-review gate. Need **three truly independent final acceptance rounds after code freeze**, not a postlabel refit or previous test rerun.

**Acceptance for this batch:** each fully executed command and exit status, version OS/Node24/26/rg, test denominator, true source/current SHA, regressions and corrections (when in owner's allowed branch), Windows real source authorization and MCP direct+stdio contract. Any failing command = RED/BLOCKED, not "done".

## Batch B — WoolRadar full Windows + truly new source holdout (priority P0)

**Source:** current independent [unified Draft PR39](https://github.com/lu403369069lu-prog/WoolRadar/pull/39) initially HEAD `e31eea548ab0b05d26e6fd639907bd81cbabcdfc` based on **Codex-owned main PR23** `6babbe12727652e8626e0fe6f554eb01fecd4a30`. PR39 includes original PR37 sampler private-host/strict identity, PR38 separated-project grants and H10 explicit timezone UTC normalization. **Do not merge PR37 and PR38 additionally if owner picks PR39.**

```powershell
git fetch origin pull/39/head
git worktree add --detach ..\wool-history-validation FETCH_HEAD
cd ..\wool-history-validation
python --version
python -B -m unittest discover -s tests -v
python -B -m unittest discover -s independent-quality/public-corpus-blind-dedup-20261016 -p "test_*.py" -v
```

Record exact counts/exits and a clean isolated SQLite database if needed. Original main PR23 had Windows **412 tests** at an earlier SHA; **do not copy that result onto PR39**. Linux focused current PR39 before handoff had **34/34 producer+grant and 24/24 independent sampler/real-schema tests = 58 distinct tests**, no Windows all-suite claim.

Next generate **a genuinely new unlabelled public-source time-window** safely from **approved public-only** X/Reddit/Linux.do/official sources within allowed network and host rules. Do not access login-only pages, private browser state, user Gmail, any private production local reports or blocked sites; do not rotate proxies/bypass CAPTCHA/geo rules. Have an independent reviewer label fresh campaign positives/negatives *before* scoring. Historic 47 first-run holdout TP1 FP0 FN3 TN40 unknown3, recall25%, cross-URL same-campaign false split1. Document new blind initial TP/FP/FN/TN/unknown/denominator and matched-identity counts; postlabel refit **must not be described as fresh independent success**. Review official eligibility/regions/card/expiry before treating an opportunity as claimable; no registrations, applications or payments.

For signed 09:30 local daily report bridge, do **not** connect by copying Windows SQLite, user reports, account tokens or production files into ChatGPT/cloud/GitHub. Design local-only opt-in sanitized report contract, explicit user approval, same-SHA producer/consumer verification, signature and replay rejection, then report `OUTPUT_CONNECTED` **only after an actual consumer round-trip**. Until then `OUTPUT_NOT_CONNECTED` remains honest.

## Batch C — WoolRadar coordination PR11 historical offline engine (priority P1)

**Source:** [Wool Draft PR11](https://github.com/lu403369069lu-prog/WoolRadar/pull/11) HEAD `27796df5f9847c1bb5d48d2a445e418dfb3d8e96` independent of main PR23. Existing original verified evidence `coordination/evidence/return-20261015/fixed-tests.json` says Windows Python3.12.14 **57 tests/exit0** at earlier SHA `a2a677...`. Git comparison says its latest code/test blobs unchanged, but **today's independent retest and true scheduled agent GitHub writes are unverified**.

```powershell
git fetch origin pull/11/head
git worktree add --detach ..\relay-history-validation FETCH_HEAD
cd ..\relay-history-validation
python --version
python -B -m unittest discover -s tests -v
```

Execute only offline synthetic `coordination/relay.py`, `relay_git.py`, `dispatcher.py` unit tests and safe no-credential dry-run state, plus replay/idempotency/SQLite-in-temp simulation, no real GitHub webhook secret, scheduling, auto PR merge or production files. Verify separation from main PR23 before any migration. Windows57 original receipt cannot be reclassified as current unattended Scheduled executor capability; that requires an authorized real sandbox event and direct writer success receipt, which should **not** be simulated by an interactive GitHub comment.

## Evidence & handoff output — strict format to existing issues

Respond into [SAM Issue #1](https://github.com/lu403369069lu-prog/YinQieJi/issues/1), [Wool Issue #2](https://github.com/lu403369069lu-prog/WoolRadar/issues/2), and [Coord Issue #3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3) only after **actual local execution**:
```text
event_key=local-history/frozen50/<family-id>/<test-type>/<immutable-sha>
repo / PR / immutable HEAD / V3 owner / platform / Node-or-Python-and-rg version
exact safe commands + exit codes + passed/failed/skipped/expected-denominator
source and formal test Git blob SHA; synthesized-only artifact locations
PASS / FAIL / BLOCKED_EXTERNAL / NOT_RUN for each stated gate
regression cause + minimal patch commit (if a real fix) + rollback
sanitized counts only, no personal URLs, Windows home paths, passwords or source documents
```

**Close individual historical families by actual evidence**, not by repeatedly re-summarizing green tests. True 80% engineering task completion is **at least 40/50 independently accepted dispositions**; a source path present or a prior Draft test is not acceptance. The historical inventory never gets a 51st member. New hourly findings go to [NEW_SCHEDULED_RESULTS_INBOX_20261017.md](NEW_SCHEDULED_RESULTS_INBOX_20261017.md). No dependency on activating new Work/Codex/cloud paid quota by ChatGPT. No proactive reminder or extra notifications.



## H17-a exact current manifest helper branch — concrete new local Codex job

**Historical SAM-H17, not a new family.** [SAM PR15](https://github.com/lu403369069lu-prog/YinQieJi/pull/15) now contains a real interactive new atomic metadata helper `SAM/snapshot/tools/atomic-write.mjs` blob `de5a34c509740e4eac44656379c7b6ed52ca5329`, builder `build-release-manifest.mjs` blob `0ed0bfb55851a092b73c0e30856f3926ce2f2b20`, and `atomic-write.test.mjs` blob `7acb5d3fa6b645487cf1d2e4d5d9092c64bb8e89`. Rebuilt independently from a Scheduled H17-a BLOCKED_WRITE report; original old patch ZIP remains inaccessible.

In the *independent SAM test worktree* specified above, **do not run the real build-release-manifest.mjs until a fully synthetic registry and immutable release source snapshot are prepared**. First run only:
```powershell
cd ..\sam-history-validation\SAM\snapshot
node --version
node --test tools/atomic-write.test.mjs
```
Run on Node 24 and Node 26 Windows; return exit/denominator and filenames + sanitized Git SHA. Expect 6 total controls. The earlier isolated Linux Node22 had 5 genuine filesystem checks plus a reconstructed minimal static callsite test **6/6 exit0**, but the entire real build script was **not** dynamically run. A Windows test can expose rename-over-existing/AV-lock/failure differences and post-replace partial-failure behavior. Add crash/restart, target absent, concurrent processes and directory handles on a **disposable synthetic folder**. Keep `current.json`, release pointer, tags and global skill/cache untouched. Separate later full **pointer + release-manifest ordering** transaction after reviewing current full `tools/migrate-release-041.mjs`; test rollback using synthetic files, never actual release data or user home.

Report only immutable helper/builder/test blobs, command exits and synthetic fixture results to [SAM Issue1](https://github.com/lu403369069lu-prog/YinQieJi/issues/1), with `event_key=local-history/SAM-H17/atomic-release-windows/<head-sha>`. A passing helper alone does not approve a production release.
