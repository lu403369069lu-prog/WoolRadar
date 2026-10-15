# Zero-capacity verification gate — isolated candidate

Date: 2026-10-15. Base: cbe18d7f058563a5aef1fb46b8d2820095f15c06. Task: WOOL-ZERO-CAPACITY-20261015, actor codex-woolradar. Formal V3 claim/start read back at state commit147efa98f35dae8ec452fe72d56e0adca0139278/revision50. Shared state may have advanced; always re-read before changes.

## Problem and resulting behavior

A fresh official record with `open=true`, `public=true`, `remaining=0` previously produced CLAIMABLE/PUBLIC_APPLICATION. This is incorrect when the same evidence says there is no capacity. The defect was executed against the fixed PR5 snapshot (its verifier is unchanged from the base) without production access. Positive1 and unknown capacity controls preserve existing semantics; unknown is not a personal entitlement promise.

The minimal gate checks numeric zero (excluding booleans) only in official evidence timestamped within the preceding24hours. Such an offer remains OFFICIAL_VERIFIED with scopeNONE and an explicit exhausted-capacity reason. Existing conflict/closed/expiry precedence remains. A fresh zero and a fresh positive at separate pages are conservatively not advertised as claimable; this does not resolve the broader temporal-source conflict model. An old or malformed/future/naive zero record does not override a separately fresh positive record. No database schema, reindex, collector, report or notification code is changed.

## Actual verification

- Eight new contracts before implementation: three failures (int0, float0 and simultaneous fresh0/fresh1). Controls passed.
- Windows/Python3.12.14, `python -X utf8 -m unittest discover -s tests`:156 passed, zero failures/skips, exit0,9.572s. Exact command/output and source/test SHA256 are in unit-tests.json. This is base148 plus8, not PR13's158 combined.
- Independent reviewer ran8 new plus15 original verifier contract methods:23 pass; additionally19 fixed-clock boundary cases. Source and test fingerprints match. Review paths are redacted for sharing. Full156 tests were run by the primary executor, not independently repeated by the reviewer.
- Existing Digest cross-process tests use the local installed upstream runtime. Results are not proof of Linux CI, all five upstream applications, actual account eligibility or95% business accuracy.

## Boundaries and next actions

Production, actual SQLite data, scheduled tasks, authentication and main were not changed. PR13's diagnostic patch and this verifier patch are separate, unmerged candidates from the same handoff baseline. No paid API, token export, account action or automatic merge.

Two other reported defects were reproduced in disposable SQLite: same-title/different-vendor campaign merge and stored status lag after reviewed merge. They remain unfixed and are outside this narrow file claim. Existing WOOL-NOISE-AUDIT belongs to its current owner; WOOL-HOLDOUT-WINDOWS is still unclaimed due to HANDOFF.md overlap. Its PR5 full Windows read-only preflight155/155 is already preserved locally, including initial system-TEMP failure and workspace-TEMP success. Do not repeat work or bypass those locks.

At phase exit publish exact candidate SHA,156-test evidence and independent review location through validated V3/CAS, release this actor's lease for review, and mirror the milestone to Issue2. Whole P06 and overall V5 remain incomplete.
