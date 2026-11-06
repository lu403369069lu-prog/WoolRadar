# WoolRadar Scheduled recovery: exact PR37 official Python tests, 2026-10-17

**event_key:** `scheduled-history/pr37/exact-full-sampler-23-and-producer-13/20261017`

**Provenance:** this result was executed in an authorized **interactive** ChatGPT session on a disposable Linux Python 3.13.5 environment. It is NOT a ChatGPT Scheduled autonomous GitHub write and NOT an execution on user's Windows production. The prior PR37 evidence had run only extracted/transcribed function controls and marked its 23 official methods unexecuted; this document closes exactly that pending gap.

## Exact immutable sources / official formal test

Reconstructed the complete actual GitHub PR37 Python module from source Git blob `c090c6885c22fe73b876de994a1c79714c0e7051` and the actual PR37 changes. Independently reproduced the entire **original published formal unittest file** exactly from GitHub, rather than reauthoring a replacement test. Verified complete local bytes via `SHA1("blob <length>\\0" + bytes)`:

| Exact Python artifact | Locally recomputed Git blob = GitHub readback |
|---|---|
| `independent-quality/public-corpus-blind-dedup-20261016/freeze_public_sample_dedup.py` | `d9c3f9c2d4c88d5867ae00f7c5039f7bc9e63ab8` |
| `independent-quality/public-corpus-blind-dedup-20261016/test_freeze_public_sample_dedup.py` | `5cdbb67b4a7a6be4f8cc19fce873b7656a9d37dd` |
| `core/public_corpus.py` current producer | `412a41db4c445a6df69f0c85c082c57abc1ffd5f` |
| `tests/test_public_corpus_identity.py` actual end-to-end producer→sampler tests | `e4e9d815b364fd95aa7e9db35574988555a25271` |

These four full-file bytes were present and hash-checked during the run. Only `core/models.py` was a minimal isolated `utc_now` stub for deterministic temporary synthetic corpus output; no whole WoolRadar production data, DB, credentials or network access was used. The 13 producer tests use the complete authentic `core/public_corpus.py` source and complete authentic sampler as imported modules.

## Exact tests actually executed in this turn

1. `python -B -m unittest discover -s /tmp/wool_exact_mu4cm9l6/independent-quality/public-corpus-blind-dedup-20261016 -p test_freeze_public_sample_dedup.py -v` — **23/23 pass, 0 failures/errors/skips, exit 0**. Includes local-only CLI temp output `0o600` on POSIX, overwrite blocking, URL identity proof, private address controls, unsafe tokens/contact rejection, distinct SPA/campaign rounds, duplicate/cap handling and strict source JSON.
2. `cd /tmp/wool_exact_mu4cm9l6 && PYTHONPATH="$PWD" python -B -m unittest discover -s tests -p test_public_corpus_identity.py -v` — **13/13 pass, 0 failures/errors/skips, exit 0**. Includes real producer canonicalization handling of percent-encoded functional keys, tracker stripping, identity loss and sampler suppression. An initial attempt from the wrong current working directory failed test-module import `ModuleNotFoundError: core` (1 test discovery error), corrected by setting `cd` and `PYTHONPATH`, then the actual correct package-context tests passed. Do not hide the initial environment error.
3. Log fingerprints from exact successful reruns: sampler `ad66dd8142d76d4c282d01b904c5e4c89c8993a7d9ea6c2ecab183b534e31926`; producer `b239e1dcca70e3d40fb8dd60d462b0a417c504cb14aff03b7809c178efec65b3` (SHA256, logs remain isolated locally, not uploaded).

## Real admission boundary still open

This verifies the two authentic files and source-integrated synthetic public samples, **not** the newer main [Draft PR23](https://github.com/lu403369069lu-prog/WoolRadar/pull/23) HEAD `6babbe12727652e8626e0fe6f554eb01fecd4a30` combined 412-test Windows suite, on Windows. PR37 is stacked on old PR23 HEAD `8023232586fd5d017981ea83ea0785cf381f7cc2`; main holder must compare current exact HEAD for conflicts. It does not prove live DNS rebinding/redirect security, fresh 47-row business recall, cross-URL campaign false-split (still 1), regional eligibility, or actual user-approved daily consumer (`OUTPUT_NOT_CONNECTED`). Keep PR37 DRAFT/unmerged. `HISTORICAL_RECOVERY_CLOSED=false`.
