# Independent follow-up after user explicitly resumed — 2026-10-16

## Branch and scope
- This is an isolated review candidate based on main integration Draft PR #23 exact parent commit `2a0fea314f3728e22a334cbf6fe4202d2b5da422`.
- Earlier user-stop note is preserved at `evidence/pipeline-integration-20261016/user-stop/HANDOFF.md`; the new user message explicitly said **继续**. No stopped automation was reactivated, no Codex quota used and no existing owner lease, task/fence or Windows production data was touched.
- Only two conservative business source guards and their targeted tests are changed. No automatic integration into PR23, no merge, force push or deployment.

## Verified concrete corrections
1. `core/developer_grants.py`: refuse negated base-verb applications (do/does/did/will/would/can/could/should/may not accept applications) and passive `applications are not being accepted`. Keep legitimate open/fee-waiver positives.
2. `core/public_corpus.py`: a truncated sanitized URL is **not** an identity-preserved resource. Record `url_identity_preserved=False` whenever its eventual stored URL was truncated after 2048 characters; recompute `url_sanitized` against the actually stored URL. Long tracking-only selectors that safely disappear may still retain true identity status if the retained URL fits.

## Actual isolated execution evidence
- Linux sandbox `python -m py_compile` on the full reconstructed new developer-grant module passed.
- Exact `git hash-object` of the reconstructed **full** developer-grant module matched live GitHub blob `8640451fc8e038f9eba125ab684e93dec4be95a6`; exact existing formal test blob `243f8ad7675a4a550bf2eea73164590b6d5600ef` also matched GitHub.
- `PYTHONPATH=. python -B -m unittest discover -s independent-quality/developer-grant-20261016 -p test_developer_grants.py -v`: **17 run / 17 pass / 0 fail / 0 error / exit0** against that exact module in an isolated package.
- 5 additional synthetic grammar negations plus one fee-waiver positive independently passed 6/6 against the exact full module. Initial scratch reproducer malformed the passive phrase by dropping `Applications`; harness corrected, then succeeded. No production code change was driven by that harness mistake.
- Exact reconstructed **full** producer module `core/public_corpus.py` matched live GitHub blob `4d13aed06b15542febe0388f0a03770bddd01168`; stubbed only `core.models.utc_now` for isolated import. Running its **real** `record_public_sample` into synthetic temporary directories and reading its JSON back checked four controls: two distinct overlong source URLs collapse to same stored prefix but both lose identity; harmless 3000-character `utm_source` safely drops yet preserves `batch=1` identity; duplicated conflicting batch values fail closed; token query value is absent and identity lost. **4/4 passed / exit0**.
- Current PR branch's new existing-repository formal tests add 2 producer/sampler cases plus expand the grant formal negative cases; **those exact new integrated tests have not been executed with the entire collector/sampler or Windows checkout here**. GitHub blob readback alone is not a test result.

## Required owner integration after independent review
1. Compare this Draft against latest PR23 HEAD, check V3 owner/lease/fence and prevent write contention; migrate only four targeted source/test paths if safe.
2. Run real `python -B -X utf8 independent-quality/delivery-bridge-20261016/run_combined_tests.py` on a full Windows checkout at **the integrated new exact SHA**, including the previously failing `tests/test_developer_grant_negations.py` and new producer/sampler tests. Record run/exit/pass/fail/skip without reusing prior 396 green count.
3. Freeze corrected code; draw **new and unseen** real public sources with independent URL+campaign adjudication and human labels before predictions. Old 56/53 corpus is development evidence, not fresh recall gold.
4. Keep `DELIVERY_BRIDGE=OUTPUT_NOT_CONNECTED` until user-approved sanitized real report publication and same-SHA consumer receipt actually exist; continue P06/region/card/account/deadline/actual notification recovery/three final independent rounds.

Never upload private Windows reports/SQLite, credentials, account details, raw conversations or production logs. No Work, paid model API or automated claims.


## Additional independent negation verification, 2026-10-16 (current Draft revision)
- An independent reviewer found that ordinary English contractions and passive future application denial were not recognized by the previous narrow negative-application pattern: `doesn't accept`, `isn’t accepting`, `aren't being accepted`, `applications will not be accepted`. Prior pattern checked these four exact synthetic phrases and returned **False** for being a denial (a security/quality gap), while affirmative-looking `Apply today` nearby could satisfy the positive opening detector.
- Current candidate updates `core/developer_grants.py` and appends **seven** exact text cases to the existing formal `tests/test_developer_grant_negations.py` without changing the positive original. It does **not** broaden the free-benefit predicate or claim personal eligibility.
- Reconstructed full exact GitHub production-module bytes and 17 pre-existing formal unittest bytes in an isolated Python environment. Their actual Git object SHA1 values matched the GitHub connector readbacks **`0201c0327c9d6039ccc3054dc1449e9cc15b831c`** (module) and **`243f8ad7675a4a550bf2eea73164590b6d5600ef`** (original formal tests). Python AST parser accepted the full source.
- Actual subprocess `python -B -m unittest discover -s independent-quality/developer-grant-20261016 -p test_developer_grants.py -v` ran **17 / 17 pass, 0 failure/error, exit0** against that exact hash-matched full module.
- Direct actual function regression against that exact module: **12 / 12** synthetically negated application variants returned False, with the existing positive `open application + no application fee` returning True (**1 / 1**). This is **not** full `core.collector.contains_keyword` execution, GitHub Actions, Windows integration or real official-program eligibility.
- Follow-up production-module tests and source blobs are uploaded on PR36. Current formal new collector integration test imports live `core.collector` and remains unexecuted by this narrow reviewer; exact new full combined Windows suite is still required at the final selected integration SHA.


## Follow-through: branded "free" fallback must not revive denied grants (2026-10-16)

**Real repro at frozen parent PR23:** The full `contains_keyword` function was extracted from the actual GitHub `core/collector.py` blob `e8183456ae5d25423c7dca76c7ae712a4e2a84e2` and executed in isolated Python with the exact helper. Three synthetic strings with `GitHub free open source developer grant` plus (a) `doesn't accept`, (b) `isn’t accepting`, (c) `applications will not be accepted` returned **True** for both `['developer perks']` and `['GitHub']` despite `is_developer_grant_lead` returning False. Thus a fixed helper alone was not end-to-end protection: the collector's brand/free fallback revived the rejected closed lead.

**Minimal business fix:** `core/developer_grants.py` now exposes `has_grant_application_denial`, requiring developer/maintainer/open-source scope + funding-program terms + a documented explicit application denial. Actual production `core.collector.contains_keyword` now fails closed for such a combined item before direct keywords, credits or brand fallback. Items with independent newly-opened campaigns require separate source review instead of treating one mixed post as automatically open. Formal regression `tests/test_developer_grant_negations.py` checks all three branded denials with two keyword configurations and positive controls for an actually open fee-waived grant and unrelated GitHub free VPS.

**Isolated execution (no Windows/full checkout):** The exact current full grant module was reconstructed byte-for-byte and hashed with Git's `blob <size>\0<bytes>` rule; SHA1 **`15af863bfa95073af6628c7ea97d5b7dc6912707`** matches GitHub readback. Pre-existing formal 17 unittest module hash remained `243f8ad7675a4a550bf2eea73164590b6d5600ef`; subprocess `python -B -m unittest discover -s tests -p test_developer_grants.py -v` ran **17/17 pass, exit0** on the exact module. Three isolated full-function `contains_keyword` source-extracted adversarial inputs were **3/3 incorrectly accepted** before collector guard and **3/3 correctly denied** after, under both `['GitHub']` and `['developer perks']`; free actual-grant and unrelated Github free VPS positives remained allowed. These are executable exact-function excerpts from GitHub, NOT an import/test of the entire `core.collector` module or a full Windows run.

Current focused changed files also include `core/collector.py` and one expanded formal collector test method; the PR is still Draft and unmerged. All real accounts, source availability, regional restrictions, current eligibility, campaign truth, fresh blind holdout, notification/recovery and 09:30 ChatGPT same-SHA receipt remain unverified. Full `run_combined_tests.py` at an integrated exact final SHA is mandatory.


## Final isolated guard consolidation — closed/expired/cancelled cases (2026-10-16)

Previously `applications have closed` was covered by grant helper's generic deny regex, but **not** the new collector gate `has_grant_application_denial`; `grant program cancelled` was also missing the conservative deny ordering. The precise extracted parent collector accepted these as a GitHub/free candidate. Current candidate adds explicit closed/expired application status and `fund|grant|program` closed/cancelled/expired program state to the same reviewed application-denial regex, while preserving the prior contracted and passive wording.

Independent exact-source execution after this update:
- Full current grant-module UTF-8 reconstructed from GitHub source patch, Git blob SHA1 computed: **`76994c181da6503fd52123e69a7d0580749b0ee9`**, identical to remote.
- Python AST parse succeeded. Original untouched formal `test_developer_grants.py` blob `243f8ad7675a4a550bf2eea73164590b6d5600ef`: subprocess `python -B -m unittest discover -s tests -p test_developer_grants.py -v`, **17 run/17 pass/0 fail/error/exit0**.
- Full source-extracted `contains_keyword` with current precise import/early-guard logic: **six** synthetic closed-grant items, including three contracted/passive and three closed/expired/cancelled statuses, yielded helper=False, denial_guard=True, brand-keyword classifier=False for **6/6**. Explicit free/open positive remains True.
- Formal `tests/test_developer_grant_negations.py` now includes all six brand-fallback adversarial statements plus unrelated GitHub free VPS and open/no-application-fee positive controls. This **updated test file is committed, not itself executed by importing the full collector and its dependencies here**. Full Windows unified suite is still not run and original business/source P06/holdout/delivery gaps remain.

**No production deployment, V3 state mutation, user accounts, paid model APIs, Work, Codex or auto merge.** The existing 09:30 ChatGPT scheduled report is enabled independently but local daily report consumer remains `OUTPUT_NOT_CONNECTED`.


## Smallest item #2: case-folded public offer selector identity — 2026-10-16

**Actual bug in exact upstream `core/public_corpus.py`**: `_semantic_query` lowercased *all* functional query keys before preserving identity. An origin may distinguish `?Batch=alpha` from `?batch=alpha`, but both normalized to the same `?batch=alpha` and were flagged `url_identity_preserved=True`. They could be treated as one campaign by future blind selection. This is not merely cosmetic when the query key names a program batch.

**Small fix uploaded on existing Draft PR36**: retain original key while normalizing display; if `original_key != original_key.lower()` for a nontracker key, set `preserved=False`. Continue dropping known tracking-only keys (even uppercase `UTM_SOURCE`) without poisoning a valid lowercase business selector. Do not change canonical keys/URL display or auto-infer claimability.

**Actually executed**: isolated Python 3.13 `python -B wool_query_identity_check.py` reproducing the exact current `_semantic_query` logic and constants. **5/5 pass exit0**: uppercase functional key now loses identity, lowercase counterpart preserves, uppercase tracking key safely removed, conflicting batches denied, sensitive token query denied. The command used a local scratch extraction, not an import of the entire repository module. A new real formal `tests/test_public_corpus_identity.py` pair is committed for producer/sampler integration: one ensures only lower-case-identity row reaches downstream blind sample, the other checks uppercase tracker removal. **Formal complete source checkout/Windows unified suite at latest PR HEAD remains unexecuted**; these narrow isolated passes must not be used to inflate the final full regression denominator.

Current code blobs should be freshly checked; no unseen real-source batch, cross-URL campaign gold, real 09:30 report consumption or user approval occurred. `DELIVERY_BRIDGE=OUTPUT_NOT_CONNECTED` unchanged.


## Smallest item #3: equal repeated resource selectors (2026-10-16)

The previous code marked only **conflicting values** of duplicate business keys as identity-lost. It collapsed `?batch=alpha&batch=alpha` into the same normalized value as `?batch=alpha` while incorrectly setting both `url_identity_preserved=True`. First/last/array query semantics vary by origin, so two different raw URLs are not proven identical.

Uploaded correction on the existing PR36: if an allowlisted semantic query key already exists in the retained map, unconditionally set `preserved=False` even when the duplicated values are equal; tracker-only keys remain removable. Added formal producer→sampler regression `test_duplicate_equal_campaign_selectors_are_not_safe_blind_identity` in `tests/test_public_corpus_identity.py`. No change to private value redaction, maximum lengths, allowed selector set or user eligibility.

**Actual isolated test**: `python -B wool_query_identity_check.py` with precisely transcribed current `_semantic_query` code/allowlists; 7/7 Python assertions exit0 (previous 5 controls plus same-value duplicate and same-value duplicate separated by a safe tracker). Old source behavior accepted the same-value duplicate as identity-preserved (source-level red condition), new code rejects. This command did not import the full `core.public_corpus` module or run the committed `unittest` producer/sampler integration, and it is not a new unseen public-source holdout. Such formal full-module and Windows integration remain pending at the final candidate SHA.

No local production reports, SQLite, account verification, source crawl, publication or GitHub PR merge.


## Smallest item #4: previously unexecuted REAL producer→sampler formal suite (2026-10-17)
This run verified the **three complete GitHub file blobs**, not merely manually reconstructed snippets:
- `core/public_corpus.py`: `18127a744d0b3e15c58af44c44aa737c861992a8`, byte-exact Git blob hash.
- `independent-quality/public-corpus-blind-dedup-20261016/freeze_public_sample_dedup.py`: `c090c6885c22fe73b876de994a1c79714c0e7051`, byte-exact Git blob hash.
- `tests/test_public_corpus_identity.py`: `45d2d51b79d2bb75405eeea15f50bc5984ef0dca`, byte-exact Git blob hash.

The files were reconstructed in a temporary isolated Python 3.13.5 checkout. The producer's sole `core.models.utc_now` dependency was stubbed with a fixed synthetic timestamp; **the full real producer, full real sampler and unmodified 11-method real test file** were run without any modification to these three hashed files. The test itself writes temporary JSON through `record_public_sample`, then calls `freeze_public_sources` on that JSON.

Actual command: `PYTHONPATH=<isolated temp root> python -B -m unittest discover -s <isolated temp root>/tests -p test_public_corpus_identity.py -v`.
**Exit 0, 11 run / 11 pass / 0 failures / 0 errors / 0 skips**. Cases cover unique batches and UTM dedup, unknown/credential-bearing selectors, SPA fragments, legacy identity proof, distinct long URL truncation, safe long tracker, functional key case-fold collisions, safe uppercase tracker, duplicated equal batch keys, and conflicting batch keys.

Runtime emitted a separate spreadsheet-package warmup warning during interpreter startup; the subprocess still returned exit0 and unittest reported all 11 pass, so the result pertains only to those actual test methods. This is a real formal producer→sampler focused suite, **not** the full WoolRadar Windows integrated suite or fresh unseen real-world independent holdout. Neither production reports nor private content were accessed.

**Next minimal task**: check percent-encoded query key collisions (`?ba%74ch=...` versus `?batch=...`) at the exact original producer/sampler boundary before claiming public campaign identity. No merge, deployment or external publication occurred.
