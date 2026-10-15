# Independent Windows integration review — 2026-10-16

Status: NOT ACCEPTED / IN PROGRESS. This review is not a merge or deployment.

Repository identity: coordinator root has unborn master, no remote, untracked existing assets.
It is not a third business repository. Existing WoolRadar bare store reused; SAM existing
GitHub repository fetched into an isolated bare store/linked worktree. Both default branches
are main; neither changed. Primary developer branches remain untouched.

## Exact evidence and counterexamples

WoolRadar PR22 e03674ec3a4ee5df27047e91af5d972495574bde:
- python -X utf8 -m unittest tests.test_apply_evidence_transaction tests.test_official_trace_stale_event tests.test_notify_reindex_transaction tests.test_reindex_review_race -v: 18/19 pass, 1 error, exit1.
- python -X utf8 -m unittest discover -s tests -v: 232/233 pass, 1 error, zero skipped, exit1.
- Test defect: ReusedEventIdentityTests calls self.report at line163; helper belongs to a different class. Assertions were not removed or changed.
- New P1: test_report_identity.py, 0/1 pass exit1. Real review_campaign merges/deletes an ID between report list_events and get_evidence; a new unrelated event reuses that ID. Report JSON attaches unrelated official proof to old primary_url. No HTTP/model/production access. A successful unit suite would not cover this independent counterexample.
- Explicit temporary source composition: PR22 above + PR23 collector 68b018965491911f2ab4943bc760eaeaa6eea710 (contains PR13 collector work) + PR14 cli/report/noise f4cf71ef5df5c3ee6b2c70b46c29cb6bd4bb650d. 262/263 pass, same helper error, exit1; report identity repro also 0/1 exit1. This is a provenance-recorded filesystem overlay, not a Git merge. Tests are not summed across variants.

SAM PR3 f2535cc5eb1e41268fff9160fff841bb2329b564:
- node node_modules/typescript/bin/tsc -p tsconfig.json: exit0 (actual compiler, not transpileModule).
- node --import tsx --test test/path-policy.test.ts test/source-qualified.test.ts test/project-routing.test.ts test/evidence.test.ts test/canonical-fail-closed.test.ts: 31/34 pass, 2 fail, 1 permission skip, exit1.
- node --import tsx --test test/*.test.ts (shell-equivalent explicit expanded list): 167/185 pass, 17 fail, 1 skip, exit1. Node/TS versions recorded separately.
- Two routing failures: nonexistent TcCommando/SPT_Alarms authorization roots trigger ENOENT. They are not the historical EPERM failures. Root authorization remains fail closed; fixture correctness versus refusal handling needs deliberate review.
- Six missing release artifacts/manifests, three child-process dependency failures, two WorkBuddy response-shape failures, two symbol lookup failures, one server answer-status mismatch, one visual broken-reference exception, plus two routing failures =17. These categories are observations, not blanket environment attribution.
- Visual real-module regression: canonicalPath(missing.jpg) throws at visual-assets.ts:91 and aborts all enumeration; existing test expects a broken reference marker. Primary SAM developer notified, source untouched.
- One skipped file-symlink test is not pass. Existing directory-junction escape tests run successfully in this environment. Historic 24/32 cannot be presented as this fresh result; new denominator includes added cases.

## Separate acceptance gates and deduplicated dependencies

| Project / gate | Current evidence | Status / next concrete dependency |
|---|---|---|
| Wool exact runtime integration | 233 and 263 real Windows tests, both exit1 | FAIL: primary fixes helper and report snapshot identity; coordinator reruns exact new SHA |
| Wool atomic ingest/supplemental evidence/review/notification | New race cases execute except helper; independent report proof fails | PARTIAL: unify read/write identity and evaluate adversarial snapshot cases |
| Wool migration/backup/recovery | Temporary regression cases run; no real historical DB copy supplied in this checkout | PARTIAL/UNVERIFIED: anonymized historical DB copy and rollback drill, never production writes |
| Wool precision/recall/dedup >=95% | Prior fitting samples and evaluator candidates are not frozen independent truth | UNVERIFIED: fixed code/source window, independent labels, duplicate truth; primary source sampling first |
| Wool sources/account/personal eligibility | Official source is distinct from personal claimability | UNVERIFIED: evidence per source/condition; never invent eligibility |
| Wool five full upstreams, Telegram, sleep/reboot, long stability | Historical partial evidence only | UNVERIFIED/BLOCKED by absent isolated dependencies or separate live-operation authorization |
| SAM full runnable candidate | tsc pass; 167/185 tests pass | FAIL: resolve missing exported release assets/child fixtures and real runtime failures |
| SAM authorization/source qualification/refusal | Focused31 pass, two failures, one real permission skip | PARTIAL: keep strict boundary; fresh positive and negative controls before release |
| SAM R5 complete pairs and refusal>=95% | Historical4/6 and34/40=85%, not rerun here | NOT ACCEPTED: real complete paired evidence, T007 target execution/impact; no synthetic replacement |
| SAM original historical semantic/gold/context review | Prior label coverage is not semantic gold | UNVERIFIED: separate primary historical audit; no raw private export |
| SAM version/dist/plugin/release/cache compatibility | Exact compiler succeeds, release assets absent | BLOCKED release: frozen identity and required materials, no installed-cache mutation |
| Both post-acceptance three independent rounds | Both core gates currently fail | NOT STARTED: round1 code/data/full regressions; round2 real quality/adversarial; round3 integration/recovery/release only after core gates pass |

Highest-impact dependency: establish one runnable complete pinned candidate per project,
repair actual failing safety/data-identity contracts, then run all dependent quality/recovery
tests. A child PR or test helper fix alone cannot satisfy the parent project.

## Ownership and continuation

Wool primary codex-woolradar owns core/tests/HANDOFF/docs/quality/evidence. Initial overlapping
review claim was safely rejected and its queue retained; no force/replay bypass. Review
uses independent-review/20261016 (Wool) and SAM/independent-review/20261016 (SAM), separate
V3 tasks. SAM primary imports/fixes its snapshot; coordinator sends precise reproductions
instead of editing its files. Three chats have distinct observed work: sources/main integration,
SAM safety/history, independent cross-project Windows review. Thread messages are evidence
handoffs, not lock grants. All future acceptance must recheck latest SHA and ownership.

Sources: current-project/measured-state (this checkout and command logs); GitHub Issue2,
SAM Issue1 and coordination Issue3 at remote-start.json. Historical descriptions are locators,
not fresh passing evidence. Confidence high for reproduced failures, unknown for unrun live
business and release gates. No merge/force push/production tasks/databases/PLC/credential or
paid-model changes. Model use after quota exhaustion is not required to replay saved V3 events.

## Follow-up recovery probes (same source composition, before final acceptance)

+python -X utf8 test_recovery.py: 3/3 pass, exit0. Actual child process os._exit(17)
+inside a multi-table candidate transaction leaves every table unchanged on reopen.
+Real campaign-review backup restores all table rows; repeated review is idempotent.
+External-send-then-process-death preserves CLAIMED and retries after lease expiry: a
+second delivery is observed, explicitly validating at-least-once ambiguity rather than
+exactly-once. Sender is a local file stub, no Telegram/network call. Synthetic DB only;
+not an anonymized historical production-copy drill, not final review round3, and not
+evidence that the independent report P1 or SAM failures are fixed.
+
## Fresh fallback-branch counterexamples

+test_offer_branch_consistency.py against exact PR23 collector in the recorded composition:
+2/6 pass, 4 fail, exit1. Ended monetary cloud-credit award, request for a provider, withdrawn
+free-start CTA, and ended coupon all incorrectly return True. Primary negative_offer logic
+does not consistently constrain the secondary award/free_start/coupon fallback. Both live
+award and optional-paid-upgrade positive controls pass. This is new synthetic contract work,
+not real independently labeled holdout precision/recall. Primary source owner notified.
+
+The report P1 reproducer now uses an actual separate Database connection/thread. It waits
+briefly for a permitted writer, then lets an atomic snapshot finish if the writer is blocked.
+This avoids same-thread nested-transaction false negatives after a correct fix. Exact PR22
+and composed variants still each 0/1 pass, exit1; writer success and true ID reuse are asserted.
+