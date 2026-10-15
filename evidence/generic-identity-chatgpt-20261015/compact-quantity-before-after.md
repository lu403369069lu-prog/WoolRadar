# Compact-size and numeric-credit dedup — exact source regression

Date: 2026-10-15. Source: [draft PR #18](https://github.com/lu403369069lu-prog/WoolRadar/pull/18), head fixed at `cd6361928e7e0a0274b2b1955b40ae3edd8ee97b` at branch creation.

## Defect and minimized patch

The preceding generic-title patch handled `Free VPS 1 GB` with spaces, but `normalize_title("Free VPS 1GB")` preserves the compact `1gb` token, which fails the resource-unit classifier. A numeric, brandless reward such as `Free $100 API credits` contains a bare number but no `GB/MB/TB` unit, so it also remained title-keyed. Both led to the **same canonical key for unrelated vendors**.

Patch `core/dedup.py` changes only generic-title classification: split compact `1GB`-style tokens for classification (not the normalized title itself), accept brandless generic benefit + numeric quantity, continue to keep 1900–2100 year-like identifiers non-generic, and continue to reject brand/product tokens from generic fallback. An accepted generic quantity uses `normalized title + "|" + normalized URL`; tracking parameters remain normalized. Explicit verified browser campaign association remains higher priority. No retroactive SQLite keys are modified.

## Independently executed source-identity and before/after tests

Python 3.13.5 on Linux, isolated temporary directories. The original and patched **byte-exact** GitHub source modules were materialized, and independently verified with `git hash-object`:

| File | GitHub/source blob |
|---|---|
| Original `core/dedup.py` at PR #18 fixed head | `96da87677a3afda9dc92a88fcc65c50f6928ae92` |
| Patched `core/dedup.py` | `9b8be5123b98a96c6164dc758299b11fc02aaad2` |
| Unmodified `core/models.py` | `7a7af3c5b913e452526f8825eca019927e0a5c71` |

Both versions ran **the same 10 synthetic `unittest` cases** against the actual `core.dedup` and `core.models` modules:

```sh
cd /tmp/relay_base
PYTHONPATH=. python -m unittest discover -s tests -p test_smoke_exact.py -v
# exit 1, 10 run, 2 failed

cd /tmp/relay_test
PYTHONPATH=. python -m unittest discover -s tests -p test_smoke_exact.py -v
# exit 0, 10 run, all passed
```

Baseline failures:
- `Free VPS 1GB`: unrelated vendors both produced key `dd688f5f6df099cc83f96c8c`.
- `Free $100 API credits`: unrelated vendors both produced key `bc612844759840c4d6472e7a`.

Unchanged controls successfully exercised in both runs: differing numeric amounts on same URL, tracking variants, branded compact-size reposts, year/batch key, source_campaign query field, verified member review, URL query-key order and differing compact sizes on one URL. The same 10 synthetic tests were saved in the local isolated harness `test_smoke_exact.py` rather than claiming that `test_generic_quantity_identity.py` was executed.

## In-repository regression definitions

Added `tests/test_generic_quantity_identity.py` with seven explicit regression tests, including a **temporary SQLite `Database.upsert_candidate`** test for distinct vendors and idempotent tracking duplicate. These seven repository definitions have **not** been executed as a suite, nor has the full WoolRadar project test suite or SQLite integration. Do not describe the database test as passed based on the independent 10-test module run.

This is a stacked, unmerged draft on PR #18 (which in turn depends on PR #17/#16/#15). Do not merge both stacked branches twice; no production DB, historical key reindex, scraper or notifier touched.

## Next gate

In a complete isolated checkout, re-read the new PR head and run:

```sh
python -m unittest discover -s tests -p test_generic_quantity_identity.py -v
python -m unittest discover -s tests -v
```

Then verify temporary SQLite event IDs, previously reported 170+ tests, and cross-PR integration using real SHA. No deployment or paid API.
