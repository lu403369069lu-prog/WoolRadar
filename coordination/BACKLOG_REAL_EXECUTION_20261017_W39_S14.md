# Actual backlog work, 2026-10-17: WoolRadar PR39 + SAM PR14

> Provenance: interactive ChatGPT engineering execution on actual connected GitHub source. **Not** a Scheduled write/run, Windows Codex result, CI run, original frozen-39 receipt, business approval, or project-wide acceptance.

## WoolRadar historical PR39 — new concrete defect and separate candidate correction

- Original Draft [WoolRadar PR39](https://github.com/lu403369069lu-prog/WoolRadar/pull/39) exact HEAD `1aad1c98584dd2c7291ada30ef71e813dbfedd50`.
- Source: `independent-quality/public-corpus-blind-dedup-20261016/freeze_public_sample_dedup.py`, original blob `d9c3f9c2d4c88d5867ae00f7c5039f7bc9e63ab8`; producer `core/public_corpus.py` blob `383f3ad38930863fe5311260f8869b1ca65564ef`.
- Actual P2 issue: root `home.arpa` is lexically private but the sampler checks only `host.endswith('.home.arpa')`; parent root `home.arpa` enters `canonical_public_url` despite producer rejecting it. A synthetic corpus with `url_identity_preserved: true` can reach blind candidate selection. No evidence of actual publication, secrets leakage or user impact.
- Local reproduction: file `/mnt/data/backlog_execution_20261017/sampler_extract.py` **extracted equivalent function**, not GitHub-blob-identical full repo. Four isolated cases: before fix 3 pass / 1 fail (exit 1); after one-line correction 4 / 4 pass (exit 0). Public-control and near-name control retained.
- GitHub candidate [Draft PR44](https://github.com/lu403369069lu-prog/WoolRadar/pull/44), stacked directly on PR39's exact branch. Changes the sampler **one conditional**, adds five source-aware unittest methods in `tests/test_public_sample_private_root_20261017.py`. GitHub readback verified sampler blob `46750d3aad01b2f915ba00713909b064bcb10c42` and new test blob `f38ac21b1bb18a02e8d19697aea587374a5f6eb0`.
- **Not yet run**: five new tests inside a complete checkout, whole-source regressions, CI and Windows/native acceptance. For local Codex: `python -B -m unittest discover -s tests -p 'test_public_sample_private_root_20261017.py' -v` followed by `python -B -m unittest discover -s tests -p 'test_public_corpus_*.py' -v` on exact PR44 HEAD. Retest both PR39 and PR44 HEAD before adopting stacked dependency.

## SAM historical PR14 — independent source-exact helper review

- [SAM Draft PR14](https://github.com/lu403369069lu-prog/YinQieJi/pull/14) exact HEAD `0cdc3b4e81b9e143cb92fabde1828b6c8a913e14`.
- Read real changed policy and test, plus caller in `SAM/snapshot/src/server.ts` blob `ea9487c7132c5ccb2db97eed1de52a99225b2ec8` and `SAM/snapshot/src/workbuddy-excerpt.ts` blob `871bb6d542dad87dcdb9f276275379fe0004657c`.
- The 12-line policy file `SAM/snapshot/src/workbuddy-fallback-policy.ts` was copied byte-identically to isolated local runtime; `git hash-object` = **`4576911ff63d91b9512b9d69c8512e5e1ac587c7`**, equal to the connected GitHub source blob. Node v22.16.0 `--experimental-strip-types` executed **15/15 assertions pass (exit 0)**: unfiltered fallback allowed; empty arrays, claim/evidence values and malformed explicit filter presence rejected. Caller demands `workbuddyFilterFallbackAllowed(input)`, absence of repository/project scope and refusal/ambiguity guards; read as source text, not runtime tested.
- Result **TESTED_ISOLATED_HELPER / STATIC_CALLSITE_REVIEW**; no new confirmed issue in this narrowly selected helper. **Not** complete `server.ts` MCP integration, `tsx` formal suite, Windows snapshot or enterprise source-label acceptance.
- Local Codex receipt needed: execute actual `SAM/snapshot/test/workbuddy-filter-fallback.test.ts`, `workbuddy-nonempty-lines.test.ts`, full lockfile-pinned applicable suite on PR14 exact HEAD; report test command/exits/counts and any dependencies.

## Shared conclusion / next step

Both PRs remain Draft; the newly created PR44 is also Draft. Nothing merged, shipped or touched the Windows/PLC/SQLite production runtime. The historical 50-family manifest remains **inventory only**; 29 native frozen command receipts and 8 external/policy gates cannot be zeroed by these tests.

The cross-run Scheduled writer was still **UNVERIFIED** as of the last read (`checkpoint.revision=0`); ledger updates made interactively must say `INTERACTIVE_ONLY`, never `SCHEDULED_PERSISTED`.

## SAM historical PR15 — second independent verified defect + Draft PR18

- Original [SAM PR15](https://github.com/lu403369069lu-prog/YinQieJi/pull/15) exact HEAD `73a3ff3c6f8fd33fdeec05ea8b9511c73c91fa58`, source `SAM/snapshot/src/claim-audit-field-types.ts` original Git blob `fd95d6954872942db03e050648e3987f80420049`.
- Confirmed code-level trust invariant gap: `evidenceIds: []` passed runtime type validation for a positive `entailment: 'entailed'`. The downstream `cards.ts` warning condition uses `entailment/evidenceTier`, not number of evidence IDs. These are synthetic offline tests, not proof of incorrect historic card answer.
- Copied exact source to isolated Node v22.16 environment; `git hash-object` **matched GitHub original blob**. Four assertions: before patch **2 pass, 2 fail, exit 1**, after patch **4/4 pass, exit 0**. The corrected source rejects empty evidence IDs for entailed claims, but retains empty evidence IDs on `missing` verdicts.
- Submitted separate stacked [SAM Draft PR18](https://github.com/lu403369069lu-prog/YinQieJi/pull/18), based on PR15 exact SHA, corrected source blob `f649a530e1616134b3008f7d08d7b07d29d331ce`. New repo-level **three test cases** in `SAM/snapshot/test/claim-audit-positive-evidence.test.ts` new blob `2d9293bbe89dfecaea39c34eb2b9de490c1b84c3`, including real JSONL loader validation.
- **Pending:** run 3 new formal tests plus adjacent existing tests on actual PR18 checkout with lockfile-pinned `tsx`/Node; collect TAP counts and exit, test legacy frozen inputs for positive records with zero evidence IDs, obtain maintainer signoff before merge. No main branch, actual user source registry or production PLC read/write changed.

