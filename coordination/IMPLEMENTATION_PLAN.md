# Three review rounds / implementation status

## Baseline
GitHub technical Issues and ChatGPT hourly conditional monitor already exist. This branch adds **only documentation/templates**. No runner, webhook, GitHub Actions, additional cost, or live task auto-execution has been deployed.

## Iteration 1 — context recovery and provenance
[x] Formalize fixed SHA, sources of truth and evidence classes.
[x] Template for zero-copy cross-conversation state.
[ ] Verify actual new Work conversation reads technical Issues before execution (requires a future run).

## Iteration 2 — deduplication, ownership and safety
[x] Design event idempotency key and state machine.
[x] Define owner claims, stale review detection and no-automerge rule.
[ ] Implement an executable event collector and dedup state persistence (not deployed).
[ ] Execute simulated concurrent edits/conflict test.

## Iteration 3 — quota-aware graceful degradation
[x] Document quota_paused mode for Codex and safe remote work routing.
[x] Separate observer automation from executor.
[ ] Verify end-to-end pause/resume with local Codex when quota is restored.
[ ] Establish user-authorized Windows executor, only if still desirable and separately approved.

## Acceptance gates for future runner
- No network write on unchanged inputs; duplicate event cannot recomment.
- Untrusted Issue text cannot grant expanded file, OAuth, PLC or billing authority.
- Fail-closed on missing SHA, insufficient review, unsafe file path or missing approval.
- Two projects independently isolated; independent owners; budgets and retries bounded.
- Fault injection: duplicate comments, stale SHA, GitHub 403/429, quota exhausted, partial write, restart.
- No claims of fully autonomous operation before such tests run.

## Next work (GitHub-only)
On a separate branch, create a small pure-stdlib offline event deduper + tests. Review any CI configuration as a PR before activation. Avoid installing full third-party frameworks while actual workload is small.
