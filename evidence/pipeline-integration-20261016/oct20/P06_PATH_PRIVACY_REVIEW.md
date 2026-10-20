# P06 URL-path privacy gate — isolated Windows evidence (2026-10-20)

Base draft PR #84: `664fbe1a00494dd13392592d412c206d45f052a6`.

## Reproduced failure and scope

- `core/public_corpus.py` previously persisted credential-like URL path and SPA fragment-route segments in `url`, `title`, and `summary`; `url_identity_preserved` incorrectly remained `true`. Three synthetic producer subcases failed before the fix.
- Legacy local snapshots could reach `freeze_public_sample_dedup.py` with those routes: three synthetic downstream subcases failed before the fix.
- Both producer and offline selector now reject/redact credential-looking paths, encoded variants and sensitive SPA routes. Redaction revokes the identity-preservation claim. Ordinary grant path and batch selectors remain reviewable.

## Checks and private candidate correction

- Producer identity tests: **15/15 passed** after fix, exit `0`.
- Offline freezer tests: **21/21 passed** after fix, exit `0`.
- Windows pinned Python local composition (PR #84 source plus **local, unpublished** PR #85 three-file security candidate plus this change): `python -B -X utf8 independent-quality/delivery-bridge-20261016/run_combined_tests.py` — **509/509, 0 errors/failures/skips, exit `0`, 38.142 seconds**. Full local log SHA256 `26B03063B04C30F779D8D90B1ADC6ADC34F3BFF98724FD48FC78A8D1824A1D8C`, retained locally. Environment reused existing pinned Digest Python; not clean install or hosted CI.
- Previously frozen local 54 distinct candidate URLs SHA256 `4832ACE6F94860A9DC60FE63EAD20E15168DCD15F353D3B9056087BB600CBD76` included **one** URL failing the new path privacy gate (hackernews). Local-only filtered revision now **53/53 distinct URLs**, SHA256 `C0A647191B68034F6C7062DEDE59997956713AE436B129399CF55BD2FC75F769`. This is a strict removal, not a new collection, no replenishment or label editing. Neither original nor filtered records are published.
- Existing source-snapshot URL identity loss (76 rows), cross-URL same-campaign adjudication, independent human Gold labels, source freshness, paid/region eligibility and the original 25% recall failure remain open. These changes do **not** establish 95% quality or ChatGPT 09:30 delivery (`OUTPUT_NOT_CONNECTED`).

## Publication boundary

Only program code, synthetic tests and this sanitized narrative may be published to the draft branch. Original public-corpus captures, 54/53 candidate records, private logs, credentials, payment data and SQLite stay on the Windows machine. No production service, scheduled task, notification, or real consumer delivery was changed.
