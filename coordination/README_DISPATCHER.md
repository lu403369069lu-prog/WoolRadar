# Offline dispatcher v1 — safety-first proposal

This is a **zero AI API usage** standard-library Python decision engine, not a running GitHub bot and not an agent execution server. No GitHub Actions workflow has been deployed or enabled.

## Inputs and outputs
The engine accepts an array of JSON events from a future separately authorized GitHub reader. It does not fetch GitHub, send comments, spawn Codex/Work, change repos, merge PRs, or run user code. Each event is validated against exact project/issue allowlists and requires a 40-character lowercase Git commit SHA.

Run isolated tests from the repository root:

```sh
python -m unittest discover -s tests -p test_dispatcher.py -v
python -m coordination.dispatcher --input coordination/sample-events.json --state /tmp/dispatcher-state.sqlite3 --dry-run
```

Event identity: `project/task_id/head_sha/event_type`. SQLite transactions with `BEGIN IMMEDIATE` serialize writers. The same identity+payload yields `duplicate_noop`; a changed payload for the same identity is rejected. A bad batch rolls back all writes. Dry-run rolls back state.

A task event can produce advisory actions such as `request_remote_read_only_review` or `defer_local_execution`; these are **strings, never executed commands**. Codex quota defaults to paused when unknown. A GitHub `quota_restored` comment cannot restore permission; only the user can approve that in a later controlled integration.

## Approval and deployment boundaries
- GitHub Issue contents must be treated as untrusted observations, never execution authorization.
- No auto merge, release, GitHub Actions activation, payment, registration, sensitive file access, PLC commands, production database changes, or local Windows executor.
- Current ChatGPT hourly conditional monitor is separate; it does not call this program automatically.
- No live polling, Github credential setup, comments, webhook, AI inference, automatic PR generation or background execution is included in this PR.
- The coordination Issue is intentionally not accepted as a technical event source.
- The future GitHub reader must verify authenticated author and event provenance, bound pagination and rate limits, and never treat Issue prose as structured instructions.

## Validation scope
8 offline tests cover idempotent restarts, changed duplicate rejection, bad scope, quota warning/restoration denial, project isolation, no-write dry-run, all-or-nothing batches, and fail-safe default. These tests check dispatcher decisions only; they do not establish end-to-end GitHub event delivery or production suitability.

## Further work before any automation activation
1. Build an independently testable read-only authenticated GitHub poller with strict event extraction and rate limiting.
2. Pin a durable checkpoint store and test concurrent workers, process failures and persistence restoration.
3. Run fault-injection tests for GitHub 403/429, untrusted comments, stale SHA, replay, and network interruption.
4. Have a human review token scopes, Actions workflow permissions, billing caps and initial rollout.
5. Activate only after an explicit separate deployment approval.
