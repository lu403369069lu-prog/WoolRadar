# Historical 42-family executor security follow-up — 2026-10-17

## Scope and authoritative state

This is an **interactive ChatGPT/GitHub handoff**, not a Scheduled task and not a production deployment.
The candidate is [Draft PR #42](https://github.com/lu403369069lu-prog/WoolRadar/pull/42), based on
`chatgpt/scheduled-checkpoint-contract-20261016`. Do not auto-merge or silently re-pin the frozen
historical manifest. `HISTORICAL_RECOVERY_CLOSED=false`; a verified runnable target is not a passed historical family.

The exact project test sources remain frozen:

| Key | Repository | Immutable SHA | READY families | Distinct commands |
|---|---|---|---:|---:|
| W | WoolRadar | `80c5ea18769c1312e5be5fd99a39e4f3d498c64f` | 15 | 14 |
| S | YinQieJi | `82bf36efa90cced8dafb56502812eb49f40515f3` | 21 | 19 |
| C | WoolRadar coordination | `27796df5f9847c1bb5d48d2a445e418dfb3d8e96` | 6 | 6 |

**42 READY / 39 distinct commands, 8 externally gated**. Latest business draft PRs are *not* interchangeable
with the frozen execution heads. Two new engineering branches, Wool PR41 and SAM PR17, have their own follow-up tests.

## New actual changes (candidate source)

- `HISTORICAL_CODEX_42_JOB_EXECUTOR_20261017.py`: full Git blob
  `5147d11067393b41db948eadea0ea2137c1cfed8`
  (previous `3e66a272f709e2af186c821313c1e11ff2f0f51b`).
- `test_historical_42_executor_raw_integrity.py`: full Git blob
  `04676c82f365e14ef9dcf24f07b30c201b8980ae` (5 tests).
- `test_historical_42_executor_path_and_log_collision.py`: full Git blob
  `67c03fd0a9b616b8fec11779d3fe250fb1901977` (11 tests).
- `test_historical_42_executor_env_isolation.py`: full Git blob
  `35885ee621defbd6332ebe2f931b1b3e0c6bf60c` (3 tests).

Key gates: original raw stdout byte hashing; do not follow symlink *ancestors*, working directory
or command-relative symlinks; permit legitimate `SAM/snapshot/../independent-review` paths only when they
stay inside the checkout and contain no symlink; full 64-hex command-digest filenames so 16-hex-prefix
collisions do not overwrite another command's log; reject zero-job, malformed, duplicate, and unmapped
family receipts; subprocess receives allowlisted OS execution variables and a fresh disposable HOME/TEMP
instead of inheriting credentials, SSH/Git keys, preload variables, and user configuration.

This is **not OS-level network/filesystem isolation**. Use a disposable low-privilege offline environment
to run third-party tests. The output directory and test log still require private-data inspection before sharing.

## Actual independent red/green results

Reconstructed the *exact* old full Git blob `3e66a272f709e2af186c821313c1e11ff2f0f51b`
by reversing the candidate code changes and compared using `git hash-object`. On Linux Python3.13.5:

- **Old source + 9 new adversarial cases**: 1 pass, 6 failures, 2 errors; exit 1;
  raw test log SHA256 `ab6c4d21b4f1fe4d22dd3ca34f5d82faa959062558f1dfd55d7a43fcc23cb2cb`.
- **Final new source + 5 prior tests + 11 path/collision tests + 3 environment tests**:
  19 pass / 0 failures / 0 errors / 0 skips; exit 0. Reproduced with the
  source-compatible `summarize/evaluate_run` functions extracted from the actual adjacent runner
  (other contract functions isolated); final raw log SHA256
  `1b27e086d176db270911486dd1958630fdd9c605ad209e36de18cccc97295686`.
- All four Git source/test blobs above were independently compared to the locally executed files.

The synthetic subprocesses use private ephemeral Python scripts and harmless fabricated output.
**The real 39 commands/42 historical families have not run in this turn; zero new Windows receipts.**
The Linux results do not prove a Windows security sandbox or the user's real account setup.

## Local Codex acceptance contract

In an independently isolated, clean Windows clone of this PR #42, using its **current exact
head SHA** (read GitHub immediately before run), first:

```powershell
python -B -m unittest discover -s coordination -p "test_historical_42_executor_*.py" -v
```

Reject failures and skips; rerun original neighboring executor/contract/receipt-guard tests
with their exact existing test locations. Verify the 50-family manifest is present byte-identically
and can be rejected when mutated. Do not use `main` or a moving PR name as the code SHA.

Then in *three separate clean and disposable checkouts* of W/S/C frozen commits, call the runner
from the review checkout using `--project wool|sam|coord --repo <frozen-repo-dir>
--expected-head <exact-40-hex-sha>`. First omit `--run` for dry-run,
then use `--run` once dependencies and network/OS boundary are explicitly checked.
The code will reject a new business PR head instead of silently re-pinning the old contract.

Inspect and redact raw logs locally before posting receipts; include real OS/Node/Python version,
exit codes, counts, skip count, exact HEAD SHA, log SHA256, and a mapping to individual families.
Pass the generated receipt through the matching family-level guard; do not interchange protocols
with the older eight-batch guard. Keep unresolved skips, official/source qualification, current
real gold, ChatGPT 09:30 delivery receipts and external-policy gates OPEN. No Work, paid cloud CI,
production SQLite, Windows Task Scheduler, PLC or secrets are authorized by this handoff.

## Upstream business follow-ups (not part of frozen historical 42)

- [Wool Draft PR #41](https://github.com/lu403369069lu-prog/WoolRadar/pull/41):
  encoded query selectors and independent live business-gold/recall remains open.
- [SAM Draft PR #17](https://github.com/lu403369069lu-prog/YinQieJi/pull/17):
  missing review status / bad UTF8 migration safeguards, true Windows Node24/26 and rollback tests open.
- Coordinator real ChatGPT takeover and real delivery/publication also remain open.


## 2026-10-17 LARGE INTERACTIVE CONTINUATION — formal guard, read-only migration, public source safety

GitHub source heads at this handoff: coordination PR42 = 7aefb93f865a822a6cd775fd1a76addcb8328f42; Wool PR41 = d6988e825f6adde55bba21483feb613b4a97b2bd; SAM PR17 = d8f3344a4a680a6e262ccb571a35755263ec9c7d. All three Draft and unmerged. Re-read heads and STOP on any drift.

### A. Real interface mismatch fixed in coordination PR42

The previous 42-job executor emitted only a per-family legacy receipt.json containing schema, repo_head, source=local-disposable-codex and full-hex log filenames. The existing OFFICIAL HISTORICAL_CODEX_42_RECEIPT_GUARD_20261017.py expects a DIFFERENT grouped-command protocol: schema_version, repo_sha, source=disposable-local-codex, runtime Python/platform/Node, test-NNN.log raw bytes, family_ids, counted tests, and immutable manifest/head/argv. Prior output was NOT directly verifiable.

Updated executor now ALSO emits receipt-guard-v1.json and test-NNN.log (same original process bytes) while retaining receipt.json for history. Invalid UTF-8 raw output cannot produce a green official receipt. The CLI loads the unchanged actual frozen guard and manifest, writes guard-verdict.json, and rejects a positive subprocess batch when the guard rejects it. Formal integration source test_historical_42_executor_guard_bridge.py contains 5 Python/Node/tamper cases; prior raw-log test expectation adjusted to fail closed on binary garbage.

THIS TURN SOURCE/TESTS ARE COMMITTED, BUT UPDATED END-TO-END GUARD TESTS HAVE NOT BEEN EXECUTED IN THIS CHAT. No 42-family Windows PASS is claimed.

### B. Wool public source producer, Draft PR41

Python urllib.urlsplit was directly verified to silently strip CR/LF/TAB and leading spaces. The source now denies normalized input identity before recording sample. Credential-bearing URL paths such as /api-key/value and /session/value get redacted before public sample storage. Node/platform metadata now receives the same URL redaction. Formal new test files: tests/test_public_corpus_control_url_identity.py, tests/test_public_corpus_sensitive_paths.py, tests/test_public_corpus_source_metadata_redaction.py. Older encoded selector, numeric IP and DNS lexical tests remain. These new tests have been committed, NOT executed against full latest PR41 source in this turn.

### C. SAM H17 release migration, Draft PR17

Derived audit claims now preserve their individual source record's reviewer/reviewedAt; migration does not falsely attribute an old review to a synthetic migration reviewer/date. An explicit --dry-run validates old 0.4.0 sources but never creates/overwrites 0.4.1, enabling read-only legacy source preflight in an isolated local checkout. Added two provenance tests plus five dry-run regression tests. New source/test code committed; NOT executed against entire latest PR17 source in this turn.

### D. Exact local Codex execution, all in three distinct disposable clean worktrees

1. Re-read current PR HEADs; compare the SHAs above. Reject drifting sources and never silently repin. Do not modify real Windows production paths.
2. PR42 repo root: run:
   python -B -m unittest discover -s coordination -p "test_historical_42_executor_*.py" -v
   python -B -m unittest discover -s coordination -p "test_historical_42_executor_guard_bridge.py" -v
   Also run existing runner/manifest/receipt guard tests. Require 0 failure, 0 error, 0 skip; capture original logs and SHA256.
3. PR41 repo root: run:
   python -B -m unittest discover -s tests -p "test_public_corpus_*.py" -v
   python -B -m unittest discover -s tests -v
   A green suite alone does not establish 95% recall/new held-out user eligibility.
4. PR17 under SAM/snapshot: run:
   node --test tools/atomic-write.test.mjs tools/migrate-release-041.synthetic.test.mjs tools/migrate-release-041.trust-boundary.test.mjs tools/migrate-release-041.provenance.test.mjs tools/migrate-release-041.dry-run.test.mjs tools/build-release-manifest.synthetic.test.mjs
   Then npm run build and npm test, only with already-installed isolated dependencies; no automatic install. Repeat native Windows Node24 and Node26 where available, report separately.
5. Separately test old FROZEN 42-family contract using W/S/C SHAs from prior section; run old 39 unique commands after dry-run, never substitute latest PR41/PR17 heads for frozen heads. A formal batch passes only if local_full_family_receipt_accepted=true in guard-verdict.json and raw-log SHA/tallies match the actual immutable guard.
6. Do not upload raw customer corpus, tokens, production SQLite or locally identifying details. Keep all eight external/policy gates, unseen independent business gold, Wool delivery consumer, SAM source gold 61/522, MCP, release rollback and final 3 rounds OPEN.

All code and tests herein are isolated candidate artifacts: no auto merge, Scheduled GitHub writer, paid CI, Windows Task Scheduler/production changes, PLC or deployment.


## E. New separate Wool developer-grant diagnostic PR43 (same interactive batch)

Independent [Draft PR43](https://github.com/lu403369069lu-prog/WoolRadar/pull/43),
candidate HEAD a4b969919603291849e0fddc535b0309628eb3c6. This branch is rooted
in Wool PR39; it does NOT modify the real Boolean lead classifier or its
thresholds. It adds human-auditable reason/signal analysis and a local-only,
aggregate-by-reason CLI over explicitly sanitized public JSONL, with no
source contents/URL/identifiers printed.

Additional Codex worktree required to validate PR43 independently:

    python -B -m unittest discover -s tests -p "test_grant_lead_diagnostic*.py" -v
    python -B -m unittest discover -s tests -p "test_developer_grant_*.py" -v
    python -B -m unittest discover -s tests -v
    python -m core.grant_lead_diagnostics < local_public_sanitized.jsonl

Expect the last command to print aggregate-only reason frequencies and
missing application/award/scope/program signals. Do not send sanitized
source text to Github by default, and never call diagnostic counts a measured
new held-out source recall. The earlier 56-row FN2 freeze was used for
development and must remain development data. True unseen source evaluation,
official evidence and user eligibility stay open. Formal diagnostic tests
are committed but NOT EXECUTED in this chat.

## LATEST 2026-10-17 QA — supersedes previous unexecuted-test statements

Verified selected Linux QA is now **138/138 pass, 0 skipped**, not merely authored: coordinator 27, SAM migration 27, Wool public corpus 53, Wool grant diagnostics 31. [Exact blob and log-hash receipt](INTERACTIVE_LINUX_QA_EXPANDED_138_20261017.json). These are selected tests reconstructed from exact GitHub source blobs, not the full Windows suites or the frozen 39-command job run.

[Frozen 42-source audit](FROZEN_42_GIT_TREE_SOURCE_AUDIT_20261017.json): all 42 READY test files exist with exact matching Git blobs, across three complete (nontruncated) immutable Git trees. All 42 command argv shapes and derived paths statically match the real runner allowlist (21 Python, 19 Node+tsx, 2 Node --test). **This does not certify successful execution.**

Current PR draft HEADs at this update (always re-read prior to local run):
- Coord PR42: 1cedcbc2ea036b723637aa94ce52fd06ac2b929c
- Wool public corpus PR41: fb091da93c0489ce88e4c1a6db0dae8f4d41be51
- SAM migration PR17: ee76958c7cbd6ed50fc3fe3fd306f47eb32ce780
- Wool grants PR43: a4b969919603291849e0fddc535b0309628eb3c6

Actual new fixes this turn: SAM 0.4.0 source file and 0.4.1 target symlink path redirects blocked before read/write (old 3 real subprocess cases, 2 failed; new migration suite 27/27 green). Wool public samples now redact percent-/multiply encoded credential-like URL paths, reject invalid non-Boolean accepted labels including string false/0, and reject in-root symlinked data/public-corpus storage that could overwrite unrelated JSON (public corpus 53/53 green). Source/test blobs are verified in the QA receipt.

Run in separate disposable worktrees pinned to those exact heads:

    # PR42 from repository root
    python -B -m unittest discover -s coordination -p 'test_historical_42_executor_*.py' -v
    # PR41 from repository root
    python -B -m unittest discover -s tests -p 'test_public_corpus_*.py' -v
    # PR17 from SAM/snapshot
    node --test tools/migrate-release-041.*.test.mjs
    # PR43 from repository root
    python -B -m unittest discover -s tests -p 'test_developer_grant_*.py' -v
    python -B -m unittest discover -s tests -p 'test_grant_lead_diagnostic*.py' -v

Then run each FULL official repo suite with the existing local offline dependencies and report environment/skip/log SHA evidence. The original distinct 39 historical commands require separate clean checkouts at their OLD frozen commits; the new PR heads cannot replace them. Run the official receipt guard: command PASS alone is insufficient unless its guard-verdict indicates accepted family coverage. Do not auto re-pin.

Windows symlink creation may be permission-gated; classify such native verification as BLOCKED rather than changing production ACLs or claiming PASS. True held-out source gold, Wool morning delivery consumer, SAM 61/522, real MCP, Node24/26, upgrade transaction and rollback remain OPEN. No scheduled task GitHub writer, PR auto merge, production PLC/SQLite access, live credentials or paid CI permitted.

## 2026-10-17 first-category source work completion checkpoint (latest; overrides older SHA/count claims)

**Actual executable selected-module tests have been run** on Linux Python3.13.5/Node22.16.0: coord33 + SAM30 + Wool corpus56 + Wool grant31 = **150/150 pass, 0 skip**. The exact current production source/test Git object blobs matched the temporary executed files. Additionally, PR41 and PR43 modules were combined without merging and **87/87 tests passed** against the same Python import graph. Full raw stdout SHA256, old-source negative results and precise limitations are stored in [first-category 150/87 QA receipt](FIRST_CLASS_SOURCE_QA_150_AND_SHARED_87_20261017.json).

New effective corrections: the frozen receipt guard and executor both reject duplicated/mixed TAP/Python aggregate summaries; SAM 0.4.1 migration rejects pre-existing (cardId, claimId) collisions before any write including --dry-run; Wool samples redact credential-bearing #/token and #!/api-key SPA hash routes, including when embedded in title/summary. The old sources failed respectively 5/6, 2/3, and 4 assertions, while current selected suites are green.

Two Wool branches PR41 and PR43 share exact historical base `1aad1c98584dd2c7291ada30ef71e813dbfedd50` and have zero overlapping changed filenames. Cross-branch 87 selected Python regressions have run in one combined throwaway source tree; this is not a Git merge, complete repo test, or official CI (no remote status contexts returned for any of four current Draft heads).

**Current checkout limitation:** this execution container cannot resolve github.com for git clone. Connector-backed immutable Git trees showed 42/42 frozen READY source blob and file path matches, 42/42 allowlisted test command paths. There was no full-repository worktree or the Node `tsx` dependency in the current container. Thus actual frozen 39 commands/full private repo suites, Windows Node24/26, authentic release upgrades, application/claimability business gold, actual alert consumer and MCP remain **NOT_EXECUTED/EXTERNAL**. Those cannot be replaced with 150 module tests.

On Windows local Codex: use fresh nonproduction disposable clean worktrees at the current four PR heads; first verify remote immutable commit/ref and test commands from this handoff. For SAM, run `node --test tools/migrate-release-041.*.test.mjs` with actual paths enumerated rather than relying on shell wildcard expansion when shell is Windows. For official old frozen history, run 39 distinct commands strictly at the immutable W/S/C heads, then formal guard on raw receipts. Never silently substitute current draft heads for the fixed historical test heads.

Prohibited: auto-merge/publish, scheduled GitHub writer, paid CI, reading real production SQLite/PLC or private tokens, changing Windows symlink permissions, or reporting 95% held-out recall without a new independent gold window.

## FINAL FIRST-CATEGORY CURRENT KNOWN CODE GATE — 2026-10-17

New authoritative [151 selected executed / 87 joint source QA](FIRST_CLASS_LINUX_VERIFIED_151_20261017.json) replaces earlier count statements. Both current real source modules and new formal test source blob hashes were matched to executed temporary files. Coord 33, SAM 31, Wool sample 56, grant 31 = 151 PASS with 0 skip/0 fail; joint Wool PR41+PR43 Python graph 87 PASS.

Additional independent fixes after earlier handoff: official guard+executor refuse mixed or duplicate TAP/Python aggregate summaries; SAM rejects BOTH collision of a new claim with existing (cardId, claimId) AND duplicate identical claim identities in old unrelated cards before a version write, including on --dry-run; Wool public sample now redacts sensitive SPA hash-router paths #/token and #!/api-key rather than preserving them. New adversarial tests were red on old source, green on updated real source.

Current unmerged candidate PR SHA must always be re-read from GitHub, not assumed from historical text above. Remote CI combined-status queries for four candidate HEADs returned 0 status entries; do not call this CI-green. True Windows frozen 39 commands/42 families were not run in chat; no Git clone possible from the current container due GitHub DNS, but exact frozen test blob and argv checks passed in the GitHub connector. Node tsx was unavailable locally. Authenticated business gold, notification consumer, full SAM lifecycle are external gates.

No auto merge, production changes, PLC access, task-scheduler GitHub writes, private data export, paid CI or synthetic tests counted as real holdout acceptance.

## 2026-10-17 CONTINUED REAL QA — 193 selected + 104 joint (supersedes earlier 151/87 and 138/96)

Machine proof: [FIRST_CLASS_LINUX_EXECUTED_193_AND_JOINT_104_20261017.json](FIRST_CLASS_LINUX_EXECUTED_193_AND_JOINT_104_20261017.json). The following are actual Linux subprocess test results on candidate Git-blob-matched source, not authored-only tests:

| Draft PR | Selected real tests | Code source blob at test |
|---|---:|---|
| Coord42 | 50/50 | 29566bd772b4564aa96d0c1ae30b6b1af99af4a8 |
| Wool41 public corpus | 59/59 | 3038f16f129e675381f5fb9a87bbf5a7c53dfaf4 |
| SAM17 migration | 39/39 | b80c4e693d11d5a7b4f7ac174e32e40fdf5f95e2 |
| Wool43 grant diagnostics | 45/45 | 6fe02aa7a83479c4eeea6a448b80f75988a13ffd |

Total 193 selected executed PASS / 0 fail / 0 skip. Manually assembled Wool41+Wool43 selected module graph: **104/104** PASS / 0 skip; it overlaps the separate suites and is NOT a Git merge nor independent business families.

Actual new fail-before/pass-after fixes:
- Wool41: URL path user emails (literal, percent, double-percent) and plain-feed title email addresses could enter a supposedly public blind corpus. New 3-method test old 4 failing assertions; now redacts mail identities without erasing benign public offer paths.
- SAM17: source 0.4.0 JSON review rows with duplicate answer_status or cardId keys, escaped aliases and nested duplicate keys were silently last-write-wins; migration now refuses source ambiguity. Source review number 1e999 became Infinity and later null, and unsafe integer IDs silently rounded; those are now rejected.
- Wool43: local diagnostic JSONL now rejects Python JSON NaN/Infinity, invalid non-string authoritative `text` override and pathological deeply nested payloads, but preserves nullable optional `text` and `summary` fallback compatibility.
- Coord42: immutable source check extended from `HEAD:path` to actual tracked on-disk bytes before and after each frozen subprocess, including Git assume-unchanged index masking. The selected test suite is 50 PASS with real local Git temporary fixtures.

**Separate historical progress:** 10 exact frozen command spellings were actually run against source-reconstructed disposable Linux partial trees, covering 11 of 42 READY historical families and 105 methods, all PASS and official per-log grammar/counts parse 10/10. See [the separate historic partial evidence](FROZEN_10_COMMANDS_11_FAMILIES_LINUX_PARTIAL_20261017.json). The remaining 29 frozen commands HAVE NO accepted execution receipt; the existing 10 also do NOT satisfy the frozen full-repository worktree preflight. No full-family official guard acceptance was claimed. All 39 test entrypoint literal imports were checked statically [here](FROZEN_39_DIRECT_IMPORT_READINESS_20261017.json).

Next actions for authorized native Codex Windows (separate disposable copies, no production): run all 39 frozen commands on the exact three OLD pinned heads using the official runner/guard, preserve every raw log SHA and test count, and report missing or skipped tests as BLOCKED. SAM old TypeScript tests require the pinned local `tsx` and lockfile dependency; installing that dependency here was impossible because the isolated container had no installed `tsx` or GitHub/npm network access. Native Node24/26, real MCP, real legacy releases, true held-out source business gold and the actual Wool 09:30 notification consumer remain unverified external gates. Do not silently update frozen manifest refs, merge draft PRs, or claim the 80% historical business acceptance is closed.
