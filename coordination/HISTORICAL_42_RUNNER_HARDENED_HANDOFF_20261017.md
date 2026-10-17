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
