# WoolRadar — scheduled task repository contract (candidate, 2026-10-16)

## Purpose and deployment state
This file records how existing ChatGPT recurring work maps to a minimal **read-only GitHub Actions metadata checkpoint**. This branch is a Draft PR candidate, **not deployed**. GitHub's `schedule` event is evaluated on the repository **default branch only**, so merely creating this branch/PR does not start scheduled runs. Do not merge without explicit user authorization, checking private repository Actions quota/billing, and reviewing branch-protection controls.

Workflow: `.github/workflows/read-only-checkpoint.yml`; self-repository issue and PR metadata only, with `contents:read`, `issues:read`, `pull-requests:read`. It has no checkout, no third-party API, no code modification, no secrets other than default short-lived GitHub token, and no external delivery. A failed API request fails the job rather than inventing a checkpoint. Outputs are GitHub Actions Step Summaries, **not persisted Issue comments or code commits**. The workflow does **not** run AI, use Codex/Work, test Windows production, claim tasks, or read local SQLite/reports. It is **not** a replacement for the existing ChatGPT automations.

## Intended triggers
- `5 * * * *` = hourly at minute 05 UTC: read-only WoolRadar issue/PR metadata.
- `30 1 * * *` = 01:30 UTC, daily **09:30 Beijing (Asia/Shanghai)**: metadata checkpoint near the existing overseas free-offer briefing, **not** the briefing itself.

GitHub Actions cron is UTC and can be delayed, dropped or disabled, so exact-time delivery cannot be promised. GitHub-hosted runners for private repositories may consume billed Actions minutes beyond included allowances; no cost-free or enabled claim is made. `workflow_dispatch` is included for manual validation *after* a workflow exists on default.

## Fixed current repositories and handoff
- WoolRadar: https://github.com/lu403369069lu-prog/WoolRadar ; technical Issue #2, coordinator Issue #3, main integration Draft PR #23.
- SAM: https://github.com/lu403369069lu-prog/YinQieJi ; technical Issue #1, main integration Draft PR #5.
- Only **two** repositories were returned for this owner at handoff; the historic three Codex chats are not asserted to be three repositories.
- Precise PR SHA and owner/lease/fence must be freshly read, not copied from this dated note. The workflow **never** mutates V3 state.
- Additional review Draft PR #32 (public URL identity), #33 (grant open/closed denial), #34 (subsecond preview ordering). These changes are **not yet integrated and retested** at main PR #23 HEAD.
- The existing daily 09:30 ChatGPT task independently searches public sources X, Reddit, Linux.do and official issuers; GitHub cannot inherit that chat's runtime or local data. `DELIVERY_BRIDGE=OUTPUT_NOT_CONNECTED` as of this handoff. Never claim `DELIVERY_BRIDGE_VERIFIED` without reviewed real redacted export, trusted SHA/provenance, approved publication, actual read and same-SHA receipt.
- New independent frozen real-source holdout, five source nodes P06, source/region/card fees/eligibility, Windows recovery, real notification and final three independent rounds remain unaccepted.

## Next exact actions
1. Review the Draft PR and independently validate workflow YAML/shell and GitHub permissions; inspect whether private Actions spending is acceptable before any merge.
2. Only after explicit authorization and a safe integrated default branch, merge via a human-controlled process; use a manual run and inspect the job summary + actual UTC run record.
3. Continue real business review on the project’s existing Draft PR and technical Issue. Do not treat passing metadata checks or scheduled-task timestamps as code acceptance, a 09:30 report, unattended AI execution, or delivery-bridge verification.

No auto-merge, deployment, forced push, paid model API, account login/claim/payment, private Windows uploads, or live data mutation is permitted.
