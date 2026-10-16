# WoolRadar（羊毛雷达） — developer handoff

## Status
- GitHub scaffolding initialized by ChatGPT on 2026-10-14.
- Local Codex source code has **not yet been uploaded**.
- No application implementation, tests, or runnable environment verified yet.

## Source of truth
- GitHub: https://github.com/lu403369069lu-prog/WoolRadar
- Local Windows project path: **to be filled in by Codex**
- Current development branch / commit: **to be filled in**

## Next Codex session
1. Locate the actual local project and inspect `git status`, `git remote -v`, branch history, README and any task notes.
2. Inspect all candidate tracked files and prior commits for secrets, credentials, cookies, browser profile files and private data. Fix any exposure before upload; do not simply rely on .gitignore to clean tracked history.
3. Preserve the existing project and history. Integrate these remote scaffold commits with the local repository using a non-destructive workflow; preferably import via a new branch and PR. Do not force-push.
4. Push actual source code, docs, safe configuration templates and tests to GitHub.
5. Run existing tests, report truthful results, and fill the sections below.

## Most recent task
- Goal: pending local Codex task details.
- Completed: GitHub integration/scaffolding only.
- In progress: local source import.
- Blockers: ChatGPT cannot access Windows local files.

## Commands and test results
- Not run. Awaiting local environment sync.

## Changed files / decisions
- Initial README.md, .gitignore, AGENTS.md, HANDOFF.md scaffold only.

## Next actions
- Import local source and document exact current task and unfinished work.


## 2026-10-16 — Proposed repository-side recurring read-only checkpoint (not deployed)

- Dedicated branch `chatgpt/scheduled-checkpoint-contract-20261016` with `.github/workflows/read-only-checkpoint.yml` and `coordination/SCHEDULED_TASKS.md`. This independent review branch does not alter project code or V3 owner/lease/fence and will be submitted as a **Draft PR**.
- Scope: scheduled, metadata-only repository Issue/PR inspection via default GitHub token with read permissions. GitHub Step Summary is the only output. **No AI task execution, unattended source-code modification, private report forwarding, or GitHub Issue writes**.
- Critical limitation: the existing `main` was still handoff scaffolding; actual candidate code is on unmerged Draft PRs. Thus this branch is **not** a production release or complete project integration. Cron is inert until an explicitly reviewed/default-branch merge. Private Actions minutes/billing and timing variance must be verified first.
- Exact active engineering checkpoints and remaining business gates are tracked in [WoolRadar Issue #2](https://github.com/lu403369069lu-prog/WoolRadar/issues/2), [cross-project Issue #3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3), and [SAM Issue #1](https://github.com/lu403369069lu-prog/YinQieJi/issues/1). Read those and latest PR HEADs afresh. `DELIVERY_BRIDGE=OUTPUT_NOT_CONNECTED` (as of this handoff); no verified 09:30 same-SHA delivery. Neither project has passed final independent acceptance.
- Actual isolated validation done in this ChatGPT turn: GitHub connector successfully created the two new files; readback follows. No workflow run, Windows test, source crawl, user-approved publication, or scheduled execution has been performed.
