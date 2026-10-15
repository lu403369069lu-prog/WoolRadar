# Independent exact-blob generic-title regression (2026-10-15)

## Scope and basis
- Upstream draft PR #17 fixed head: `27fb5783ff5bd74394389cd57d73a598626b8377` (stacked on #16 / #15, all unmerged).
- Original `core/dedup.py` Git blob SHA: `bb6890201146f54d7ec2b964e08add738cec786a`.
- Patched `core/dedup.py` Git blob SHA: `4fd8a5998f99746f1af158a2ba623fbc39f4875f`.
- Imported unchanged `core/models.py` Git blob SHA: `7a7af3c5b913e452526f8825eca019927e0a5c71`.
- New `tests/test_generic_identity_extension.py` Git blob SHA: `00384e3af4e49f04a75b8b1628434787cef13388`.

All four blob SHAs were verified by `git hash-object` on locally materialized files and against GitHub's returned exact blob identities. This is **execution of the exact Python dedup/models code and new exact test file**, not a behavioral mirror.

## Independently executed before / after

Environment: Linux, Python 3.13.5; isolated temporary directory; no network or database required.

Command on each version:

```sh
PYTHONPATH=. python -m unittest discover -s tests -p test_generic_identity_extension.py -v
```

**Baseline exact GitHub PR #17**: `Ran 9 tests in 0.003s`, `FAILED (failures=2)`, **exit 1**. Reproduced cross-vendor collisions for:
- `Free AI credits`: two distinct vendor URLs both mapped to key `ca52240df963937869407a1a`.
- `Free VPS 1 GB`: two distinct vendor URLs both mapped to key `1afc0f116988c97676d9bd88`.

**Patched exact GitHub blob**: `Ran 9 tests in 0.002s`, `OK`, **exit 0**. Nine tests check cross-vendor separation, numeric resource size, distinct size on same landing URL, tracking variants, branded cross-post grouping, branded size grouping, year-like batch preservation, old URL-only generic identity, and explicit public browser-reviewed campaign merge.

## Minimal intervention

- Add `ai` to the generic benefit tokens (previously an unrecognized vendor-looking token).
- A bounded `_generic_resource_title` recognizes generic resource units `gb,mb,tb` and numeric quantities only in the absence of other vendor/product identity; year-like 1900–2100 tokens are not treated as resource-only.
- For resource-spec generic titles, key is based on normalized title **plus normalized URL**. This preserves different resource specifications at one shared landing page, while splitting same-title offers from distinct vendors.
- Original no-number URL-only generic key is preserved; explicit `campaign_review` override remains highest priority.

## Limitations & hazards

- This is not the entire project test suite, database notification idempotency, Windows integration, historical event migration, or production reporting.
- Remaining generic languages/amount types/colliding brands are not comprehensively solved. URL-based identity may intentionally split a genuine unreviewed cross-site promotion; explicit validated campaign review unifies confirmed members.
- PR #17 and this follow-up are stacked on unmerged PR #16/#15. **Do not merge PR #17 and this follow-up twice or modify production canonical keys without separate migration and notification review.**
- Do not auto-merge, deploy, modify SQLite, run live collect or use paid APIs.

## Next exact acceptance

In an isolated complete checkout of the patched branch, run

```sh
python -m unittest discover -s tests -v
```

and compare the 170 previously reported PR #17 tests, new 9 test definitions, true Windows git SHA and temporary SQLite behavior. Any deviation must be recorded honestly; synthetic 9/9 does not upgrade project-level precision, recall or 95% target.


## Follow-up: explicit campaign query identities and stable parameter ordering

At the next independent development cycle, the original `normalize_url` query predicate was found to be overly broad: removing **all** keys beginning with `ref` or `source` silently discarded `reference_id` and `source_campaign`, allowing distinct campaign links under an otherwise generic title to share a canonical key. At the same time, the unsorted query encoding split the same set of parameters in different URL order. The change is tightly scoped to the existing URL-normalization function on the same unmerged PR #18.

New behavior:

- Only `utm_*`, exact `ref` and exact `source` are treated as disposable tracking fields.
- Other query identifiers are preserved conservatively.
- Remaining pairs are sorted by key **stably**: reorder of different keys becomes equivalent, repeated values within one key retain their relative order.
- `campaign_review` membership uses the same normalized URLs; code to validate explicit human-reviewed campaign URLs is unchanged.

**Independent exact Python code runs:** baseline blob `4fd8a5998f99746f1af158a2ba623fbc39f4875f`, new blob `96da87677a3afda9dc92a88fcc65c50f6928ae92`, unchanged `core/models.py` blob `7a7af3c5b913e452526f8825eca019927e0a5c71`, and extended real repository test blob `670ec58e9576f0a0793f2b534b27dcd9e443a1e5`. All blob SHAs were recomputed locally with `git hash-object` on test-run files and matched remote GitHub exact blobs.

Run from isolated Linux/Python 3.13.5 using the same committed test file:

```sh
python -m unittest discover -s tests -p test_generic_identity_extension.py -v
```

- Before this second patch: **10/14 passed, 4 failed, exit 1**. Failures: unordered query keys; `source_campaign` identifiers silently removed; `reference_id` identifiers silently removed; interleaved duplicate query keys.
- After patch: **14/14 passed, 0 failed, exit 0**.

This 14-item suite includes all 9 previously submitted tests plus 5 new regression tests. It uses exact GitHub Python modules and the exact new test file, not a translated behavioral mirror. It does **not** prove the complete WoolRadar 170-test suite, a production database migration or end-to-end notification behavior. Some servers can interpret query key order semantically; this explicit conservative limitation should be evaluated against real tracked providers before any migration of historical campaign identities. Do not merge or deploy without whole-project review.

