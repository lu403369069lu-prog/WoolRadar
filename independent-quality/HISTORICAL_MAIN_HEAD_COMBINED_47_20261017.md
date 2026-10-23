# WoolRadar recovered Scheduled fixes: one latest-main-head historical integration with 47 authentic Python tests

**event_key** `history-first/wool/PR23-exact-head-PR37+PR38-47-formal/20261017`  
**Actor / scope**: user-authorized interactive GitHub writes and isolated Linux Python3.13.5. Not a ChatGPT Scheduled unattended write, not private Windows production, not a live provider/region eligibility check or new unseen business holdout.

## Why this branch exists

Wool main owner [Draft PR23](https://github.com/lu403369069lu-prog/WoolRadar/pull/23) HEAD was `6babbe12727652e8626e0fe6f554eb01fecd4a30` on cold read. Old independent [Draft PR37](https://github.com/lu403369069lu-prog/WoolRadar/pull/37) was still based on **older** `8023232586fd5d017981ea83ea0785cf381f7cc2`, while [Draft PR38](https://github.com/lu403369069lu-prog/WoolRadar/pull/38) was current-based and addressed a separate grant cross-project issue. Latest main PR23 sampler was still original Git blob `c090c6885c22fe73b876de994a1c79714c0e7051` with no PR37's lexical internal-host or strict boolean URL identity gate. This isolated branch `chatgpt/wool-historical-integration-20261017` was created **from exact PR23 current HEAD** (without touching holder branch) and **ported the complete exact two PR37 files + two PR38 files byte-identically**, rather than blindly merging divergent history.

| Changed artifact | Git blob on unified branch = original tested candidate |
|---|---|
| `independent-quality/public-corpus-blind-dedup-20261016/freeze_public_sample_dedup.py` | `d9c3f9c2d4c88d5867ae00f7c5039f7bc9e63ab8` |
| `independent-quality/public-corpus-blind-dedup-20261016/test_freeze_public_sample_dedup.py` | `5cdbb67b4a7a6be4f8cc19fce873b7656a9d37dd` |
| `core/developer_grants.py` | `ce53bfdcfb75d1f9b4927f0dad762a20b9bd5bc2` |
| `tests/test_developer_grant_project_scope.py` | `26193c5b92c69c41b53a22ccc1cbb6c008ec2545` |

Unchanged true main-integration dependencies present in this single GitHub branch:
- `core/public_corpus.py` **`412a41db4c445a6df69f0c85c082c57abc1ffd5f`**;
- `tests/test_public_corpus_identity.py` **`e4e9d815b364fd95aa7e9db35574988555a25271`**;
- `core/models.py` **`7a7af3c5b913e452526f8825eca019927e0a5c71`**.

All **seven complete local byte files** were independently Git-SHA1 hashed and matched the exact GitHub blobs above. The first local reconstruction of `core/models.py` was missing its final extra newline and produced a different blob; it was corrected and the entire official test subset rerun, producing exact match to true GitHub `7a7af3c5b...`. No synthetic substitute models are used in the final run.

## Actual combined same-source tests

Two real official-test discovery invocations on the **same local checkout**:
```bash
cd /tmp/wool_exact_mu4cm9l6
PYTHONPATH="$PWD" python -B -m unittest discover -s tests -p 'test_*' -v
python -B -m unittest discover \
    -s independent-quality/public-corpus-blind-dedup-20261016 \
    -p 'test_freeze_public_sample_dedup.py' -v
```

- Actual `tests/` 24 = current main real producer→sampler public identity tests **13/13**, plus newly integrated developer grant project-boundary test **11/11**; **24/24 pass exit0**, local log SHA256 `a60871d63eb20e0ac47233162168419ecc7850e463e76380dcae21786a69f0da`.
- Exact official PR37 standalone sampler suite **23/23 pass exit0**, local log SHA256 `4696580f35ea1bdfb6a23009211142747efe39aab9a023f2224cf2df794e9834`.
- Therefore **47 distinct formal unittest methods, 47 passed, 0 fail/error/skip, both runs exit0**. These 47 encompass earlier separate 23+13+11 historical reported cases; do not sum them again as extra work.

This test environment didn't have the entire original WoolRadar repository's **412-test combined source suite**; only the selected full matching seven code/test blobs were used, with standard Python library. No DB/reindex/notification, Windows, DNS/redirect, real X/Reddit/Linux.do connections, or independent post-fix gold was executed.

## Explicit remaining business-red gates and safe review

- New Oct17 independent public holdout (before this patch) **47 items /4 positives / TP1 FN3**, first-run recall **25%**, one true same-campaign cross-URL pair predicted not merged. New untouched post-fix holdout remains **NOT TESTED**, and this code's exact URL dedup does not by itself fix semantic cross-URL matching.
- Grant PR38 only binds evidence to **separated paragraphs/bullets**. Two different projects mashed into one paragraph can still be false-positive, and official source claimability/regional limits/card conditions/expiry remain unverified.
- Private/local hostname suppression is a **lexical filter, not DNS resolution/redirect/SSRF guarantee**. Public sample production and true P06 official source gate remain separate.
- 09:30 approved signed local user report same-SHA consumer is still `OUTPUT_NOT_CONNECTED`.
- This branch is **isolated Draft review candidate, not deployed/merged**, and its source will grow stale if Codex owner's PR23 moves. Recompare exact HEAD and run all formal Windows tests/real source gold before the owner can decide integration. Don't merge PR37, PR38 and this unified candidate redundantly; choose one reviewed integration route.

All results are an interactive-chat recovery of historical artifacts; no Codex/Work/paid API/paid runner, no credentials, user private report exports, unauthorized GitHub writes or production Windows/PLC/account operations. `HISTORICAL_RECOVERY_CLOSED=false`.
