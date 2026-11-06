# Historical WoolRadar WR-H16 — unrelated grant projects stitched into one false lead

**event_key** `history-first/WoolRadar/H16-exact-grant-per-section-synthetic-redgreen/20261017`  
**provenance** authorized interactive chat only. Linux Python3.13.5 source tests using fully reconstructed exact GitHub production module at main Draft PR23 SHA `6babbe12727652e8626e0fe6f554eb01fecd4a30`. No network, live provider pages, private user report, application, paid service or original real holdout labels.

## Real defect reproduction

Actual main source `core/developer_grants.py` original complete Git blob **`76994c181da6503fd52123e69a7d0580749b0ee9`** was recreated byte-for-byte and imported directly into Python. Original code normalized *all* concatenated text before looking independently for scope, program, application and amount cues. Hence a feed containing Project Cedar's open-source funding discussion, Project Birch's unrelated speaker applications and Project Elm's unrelated grant amount could be incorrectly flagged as one potential current developer grant. Same for multi-source bullet lists. It also failed to understand valid `Applications are now open` and fail-closed negative `Applications are now closed` due missing combined `are now` grammar.

The new complete committed `tests/test_developer_grant_project_scope.py` is source-matched Git blob **`26193c5b92c69c41b53a22ccc1cbb6c008ec2545`** and contains 11 independent formal unittest methods (subtests exist in one method). Against authentic old original blob:
`PYTHONPATH=$PWD python -B -m unittest discover -s tests -p test_developer_grant_project_scope.py -v` — **11 run, 7pass, 4fail, exit1**. Failures: unrelated project paragraphs, unrelated bullet list, current real `are now open`, explicit `are now closed` not rejected.

## New minimal conservative correction in own independent Draft

Branch `chatgpt/wool-historical-grant-project-scope-20261017`, created from PR23 exact HEAD above. **Do not modify Codex-owned PR23.**

Changed actual `core/developer_grants.py` Git blob to **`ce53bfdcfb75d1f9b4927f0dad762a20b9bd5bc2`**:
- retain **global** denial, payment/fee and applicant-question refusal to avoid reviving any closed/paid lead from adjacent blocks;
- positive `_SCOPE/_PROGRAM/_APPLY/_AWARD-or-_AMOUNT` evidence must occur within *one explicit paragraph or bullet section*. This guards cleanly delimited unrelated-project concatenations, not arbitrary same-line name crossovers;
- recognize `Applications are now open` and `Applications are now closed` without treating payment-required or only-questions as actual openings.

The same exact 11 original formal controls on new complete module: **11/11pass, 0fail, exit0**; local green log SHA256 `65a8b5456bc1534e39b838d208e7efaea4b17c2feb54d900ab9b338bb6c57527`. New module Git SHA1 `ce53bfd...` and formal test Git SHA1 `26193c5...` recomputed locally and matched GitHub remote.

Also used the **18 original negative English phrases** appearing in official `tests/test_developer_grant_negations.py` main Git blob `ec55b3de6629726510e1cdbd8438c8f1c37b3c6a` to exercise **direct real `is_developer_grant_lead`**: all 18 rejected, and the original explicit fee-waiver positive retained true. **Not** the full authentic collector `contains_keyword` test — the official test file imports `core.collector` plus other large system dependencies, and was not rerun in this isolated checkout. Thus no claim of main 412/412 or full collector integration from these checks.

## Residual risk and next acceptance

This is **a conservative partial quality fix** against visibly separated paragraph/bullet source projects. Two unrelated programs crammed into one paragraph (without explicit boundaries) can still supply a false semantic combination; project identity cannot be inferred reliably from regex alone. Manual official provider-page eligibility/terms/geo/date/paid verification remains required. New independent time-window blind sample (old47 first-run TP1 FN3 recall25%, plus cross-URL same-campaign false split1), current-head full official suite on Windows, and integration review with PR23 owner remain **NOT DONE**. This code only generates unverified lead candidates and may have false negatives for multi-paragraph descriptions; do not turn it into user claimability/automatic sign-ups. Keep Draft, no merge, no accounts/payment/production Windows/PLC work. `HISTORICAL_RECOVERY_CLOSED=false`.
