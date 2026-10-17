# Developer grant: diagnostic-only continuation (2026-10-17)

Current independent [Draft PR43](https://github.com/lu403369069lu-prog/WoolRadar/pull/43)
HEAD at authoring: 5bb2abee3d2a9608a7e2a6aed085e1a7febe2f09.
Base: chatgpt/wool-historical-integration-20261017. Never merge/rebase
automatically; re-read SHA before each local Codex test.

## Why this is a separate scope

The previously reported seven-source / 56-row freeze has two false
negatives. Those rows have already been used for development, so neither
tuning regexes against them nor rescoring them proves 95% independent
recall. Official application dates, geography, fee/card eligibility and
actual funding conditions must be validated from official sources.

This PR deliberately does **not** change the original
core/developer_grants.py Boolean lead decision. It adds an explainable,
reason-only analysis to inform an independent human review without
revealing source text or pretending the lead is confirmed.

## Local analysis in a disposable worktree

1. Verify the PR43 HEAD SHA exactly and that git status --porcelain is
   empty; do not run the scripts in the real WoolRadar production folder.
2. Run the authored tests, then the existing classifier tests:

       python -B -m unittest discover -s tests -p "test_grant_lead_diagnostic*.py" -v
       python -B -m unittest discover -s tests -p "test_developer_grant_*.py" -v
       python -B -m unittest discover -s tests -v

   All tests must have actual nonzero counts, zero skip, zero errors,
   exit 0. These commands have NOT been executed in this chat against
   the current exact PR43 full checkout, and cannot be marked PASS now.
3. Run the report on **local deliberately sanitized public JSONL
   snapshots only**, never accounts or raw private user records:

       python -m core.grant_lead_diagnostics < local_public_sanitized.jsonl

   Accepted fields per JSONL object: text or title+summary. The output
   contains only aggregate reason counts; no source text/URLs. An invalid
   row makes the command exit nonzero and does not echo the row.
4. Compare missing-application vs missing-award vs global-denial gates,
   with a human checking original public sources locally. Source-level
   correction requires independent evidence and negative regressions.
5. Any rule edit turns that set into development data. Freeze a **new,
   unseen, different time-window** source corpus, independent labels
   first, then actual collector predictions; report TP/FP/FN/TN/unknown,
   precision/recall/denominators, duplicates, and official eligibility
   separately. An empty selection cannot be called 95% precision.
6. WoolRadar full delivery still needs source qualification and
   09:30 Asia/Shanghai trusted consumer receipt; OUTPUT_NOT_CONNECTED
   is an independent hard gate.

No scheduled GitHub writer, automatic registration or offer claim, card
binding, live notifications, production SQLite or user-secret upload.
