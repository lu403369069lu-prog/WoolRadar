# WoolRadar independent holdout protocol (candidate quality, not entitlement)

This is a **read-only** quality check against the current project. It does **not** run collectors, touch SQLite, alter pause/budget state, log into websites, or prove account eligibility.

## Freeze before adjudication

1. Freeze a code revision and predeclare the sampling window and sampling frame (source IDs, public-only collection, collection times). Do not use previously rule-fitted examples from EVALUATION.md as new independent holdout evidence.
2. On the Windows machine, copy chosen \`data/public-corpus/<source_id>.json\` files and \`config/sources.yaml\` into a **separate, non-production** root with the same relative paths. Do not scan while copying a mutable live sample. Preserve bytes and record each snapshot SHA-256 and \`sampled_at\`. Existing samples overwrite per source; a copy is needed to freeze them.
3. Reject any corpus where \`rows_truncated=true\` or \`fetched_count != stored_count\`. Record which source/time windows are missing because of SKIPPED, PAUSED, FAILED, or no sample. These are **coverage gaps**, not false negatives with known denominators.
4. Independently label **every row**, including originally rejected rows. Annotators should not see or use \`accepted\` when deciding ground truth. Use \`offer=true\` only for a real promotional/developer benefit *lead*; \`false\` for known non-offers; \`null\` if the information cannot support a reliable label. An \`offer=true\` row requires a stable \`campaign_id\` representing a real campaign, not a headline. Two distinct campaigns with the same title need different IDs; multiple posts for the same campaign need the same ID.
5. Keep a private audit ledger recording annotator, grounds/URLs checked, adjudication disagreements, revision-freeze time and label-finalization time. Do not upload private browsing data or raw account evidence.
6. Do **not** tune rules on this holdout and then report the same score as independent. After a change, freeze a new untouched window or report it as development evaluation.

## Label manifest (illustrative only)

\`\`\`json
{
  "schema_version": 1,
  "split": "holdout",
  "frozen_code_ref": "FROZEN_COMMIT_SHA",
  "snapshots": [
    {
      "source_id": "lowendbox",
      "sampled_at": "EXACT_SAMPLED_AT_FROM_SNAPSHOT",
      "sha256": "SHA256_OF_UNMODIFIED_JSON_FILE",
      "labels": [
        {"index": 0, "offer": true, "campaign_id": "campaign-001"},
        {"index": 1, "offer": false},
        {"index": 2, "offer": null}
      ]
    }
  ]
}
\`\`\`

The example indices are not the complete labels for a real snapshot: provide exactly one entry for each row. \`null\` means **unresolved** and is excluded from binary precision/recall but counted as unknown. \`sha256\` covers raw UTF-8 file bytes (not reserialized JSON).

From a checkout containing \`core/holdout_eval.py\`, against the **isolated** root only:

\`\`\`powershell
python -m core.holdout_eval --root C:\WoolRadar-Holdout-Frozen --labels C:\WoolRadar-Holdout-Frozen\labels.json
\`\`\`

Run \`python -X utf8 -m unittest tests.test_holdout_eval\` for synthetic metric-regression tests; this checks the evaluator, not actual campaign accuracy.

## Metric definitions and limits

- Candidate TP/FP/FN/TN: \`accepted\` from the preserved raw sample vs independent lead truth; precision = TP/(TP+FP), recall = TP/(TP+FN). A zero denominator is \`null\`, **never 100%**.
- Pairwise dedup (only selected *true-positive* leads): compare each pair's \`canonical_key + batch_id\` with adjudicated \`campaign_id\`. Pairwise precision = correctly merged pairs / all predicted merged pairs; pairwise recall = correctly merged pairs / all true same-campaign pairs. \`false_merge\` and \`false_split\` counts are included.
- Excluded/unknown labels, capped rows, sources that were not fetched, missing historical windows, and closed/private sources prevent extrapolating to the full 19-platform monitoring goal.
- Pairwise dedup is **conditional on retrieval** and is not an overall end-to-end duplicate delivery metric. A second, separate audit must inspect persisted cross-run notifications, annual batches, campaign reopening and post-merge evidence.
- \`OFFICIAL_VERIFIED\`, \`CLAIMABLE\`, personal qualifications and actual redemption are **not** evaluated by this lead-only instrument. They require independently timestamped official proof and explicit eligibility checks.

The fixture in \`tests/test_holdout_eval.py\` deliberately includes two *different* campaigns with the same title and two posts from one campaign with different titles. It demonstrates both false-merge and false-split measurement without claiming those synthetic counts are production estimates.
