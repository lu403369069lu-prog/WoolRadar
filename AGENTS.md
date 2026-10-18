# Collaboration rules

- Project: WoolRadar（羊毛雷达）. Actual repository: lu403369069lu-prog/WoolRadar.
- Preserve existing local project code. The initial GitHub commit only establishes handoff scaffolding.
- Before modifying code, read HANDOFF.md and inspect the real project structure and tests.
- Keep work isolated in feature branches such as `codex/<topic>` or `chatgpt/<topic>`; integrate through pull requests where possible.
- Never commit API keys, access tokens, passwords, cookies, browser profiles, .env files, or private personal data. Check tracked files AND Git history before pushing.
- Never force-push or delete branches without explicit permission.
- Run suitable tests for the actual project stack; do not invent passing test results.
- Update HANDOFF.md with task state, changed files, commands run, blockers and next actions at every handoff.
- If local Git history already exists, preserve it and merge remote changes safely; do not reinitialize blindly.

## Codex 2026-10-18 work pickup

Read `CODEX_NEXT_TASKS_20261018.md` and `coordination/CODEX_HANDOFF_ROUTER_20261018.md` before claiming unfinished work. Those files point to already-tested cloud results and local-only Codex tasks; do not reinitialize or rerun identical fixed-source tests. Check GitHub Issue #2 and coordination Issue #3, source PR HEAD and the V3 lease/fence contract; a task document is not a lock.
