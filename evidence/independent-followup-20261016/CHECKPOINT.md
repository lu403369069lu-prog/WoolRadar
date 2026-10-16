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
