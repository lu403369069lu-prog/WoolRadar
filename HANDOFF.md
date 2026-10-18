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

## 2026-10-18: Native GitHub Actions relay is live (not an AI coding agent)
- Workflow on default branch: `.github/workflows/historical-family-relay.yml`; hourly UTC minute 23 and `workflow_dispatch`, plus push verification. GitHub schedule is best effort.
- Audited test/relay script: `.github/relay/worker.py`; regression tests: `.github/relay/test_worker.py`; 26 entries in `.github/relay/queue.json`. Source under test is the independent `chatgpt/wr-h07-public-corpus-url-limit-fixture-20261018` branch, **not** empty main scaffold.
- Separate unprivileged evaluation and minimally writable persistence jobs. Evidence artifact uploads hidden `.relay-report`; only `chatgpt/actions-live-state-v1-20261018` is mutated by the write job. `engine.json` records cursor/revision and each family partial disposition; `history.jsonl` is append-only per unique run. PRs never auto-merge. All check subsets remain `strictly_complete=false`.
- Continuous actual Actions read/write verified: [first full persist run](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39083789000) and [main-branch replay regression run](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39084179868), both successful. New workflows on main are not contingent on opening or merging historical Draft PRs.
- Temporary `candidate/.test-tmp` now created in disposable Actions checkout to satisfy project test fixtures. Prior transient WR-H03/H07 errors were caused by the missing temporary folder in the new runner; preserve them as historical receipts, and reevaluate the same checks before interpreting them as source defects. Existing [PR46 formal acceptance](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39082441724) separately passed 75/75.
- Not yet full user goal: Actions test/rotate/report/persist deterministically but do **not** generate arbitrary source repairs, invoke ChatGPT, resolve Windows/native gates or confer business acceptance. That needs an external coding actor with explicit authorization; no model credential configured and none is exposed to untrusted tests.
- Next: review automatic failures and source updates, map remaining formal tests, obtain original Windows/frozen business receipts, do not change production or merge PRs automatically.
