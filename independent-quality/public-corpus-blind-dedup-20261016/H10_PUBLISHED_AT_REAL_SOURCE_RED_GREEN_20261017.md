# Historical WR-H10: exact real producer timezone parser red→green

**event_key** `history-first/wool/H10-real-published-at-red9-green57/20261017`

**Source baseline**: main Wool PR23 (also PR39 before this patch) `core/public_corpus.py` exact Git blob `412a41db4c445a6df69f0c85c082c57abc1ffd5f`. It used `'published_at': str(row.get('published_at', ''))[:80]`, which admitted untrusted email-like, private-path, token-like, timezone-naive or invalid values into later public-sample metadata without validation.

This belongs to the previously noted historical Scheduled WR-H10 family, but the old uncommitted candidate blob `72db704...` was not available for byte-for-byte recovery here. **The implementation below is an independently recreated code patch**, not a claim that those old unknown exact bytes have been restored.

**Actual red**: on the **complete old actual producer source**, 10 new standalone `tests/test_public_corpus_timestamp.py` methods with actual tempfile producer runs: **10 run / 1 pass / 9 failures / exit1** (ISO Z was only supported by accidental copy-through).

**Actual green**: conservative function `_clean_published_at(value)` admits only explicit time-zone ISO8601 (`Z`, `±HH:MM`) or bounded RFC2822 with recognized GMT/UT/±HHMM zone, parses real calendar dates, normalizes UTC to `YYYY-MM-DDTHH:MM:SSZ`; invalid/naive/untrusted/other strings become empty metadata rather than a fabricated publish date. No date input is treated as official registration eligibility/claimability. Changed production complete file Git blob **`6768c5d1a2229c6b5410c70de270ef49dc65bc26`** (GitHub commit `50777fbff4c3f82bc8cda627f75156f806feb362`). New 10 full producer cases source Git blob **`c90cb9eab13230d4c4086e51c9c1b3f6f034dd62`** (commit `54b8411cd6417dbeecb55490d1bf7205368c9433`). Both identical to actual locally tested complete bytes.

Linux Python3.13.5, exact PR39 checked-out source tree with producer+sampler+grant:
- `PYTHONPATH=$PWD python -B -m unittest discover -s tests -p 'test_*' -v` → **34/34 pass, 0 fail, exit0** (previous 24 + ten new WR-H10).
- `python -B -m unittest discover -s independent-quality/public-corpus-blind-dedup-20261016 -p test_freeze_public_sample_dedup.py -v` → **23/23 pass, exit0** (same exact full PR37 sampler).
- **57 distinct methods, both exit0**; the earlier 47 are a subset, not additive. Raw local isolated logs `/mnt/data/Wool_WR_H10_combined_new34.txt`, `/mnt/data/Wool_WR_H10_sampler23.txt` existed in this interactive run; they are not uploaded raw private data.
- Current PR39 remains Draft, source/test SHA matches exactly from GitHub readback. No main PR23 owner branch touched.

**Remaining**: explicit RFC2822 forms outside tested strict subset may now be rejected as unknown (fail-closed false negatives); timezone normalization is only public sample metadata, not actual system clock or source trust. Validate consumer date filters against published official sample contracts before integration. No real newly independent blind time-window after this patch, no 412 Windows combined tests, no X/Reddit/Linux.do login, signed 09:30 consumer remains OUTPUT_NOT_CONNECTED. `HISTORICAL_RECOVERY_CLOSED=false`.
