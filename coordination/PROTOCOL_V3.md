# Durable handoff protocol V3

V3 adds executable state and recovery to `PROTOCOL_V2.md`; it does not activate a daemon.
V2 `independently_reviewed` maps to V3 `reviewed`; `blocked` maps to a specific blocked state.
Migration is explicit: retain the V2 record, create a complete V3 task, validate, then publish
on a dedicated state branch. Unknown versions fail closed; do not fill missing fields as done.

## Truth and transport

- SAM facts: YinQieJi Issue #1. WoolRadar facts: WoolRadar Issue #2. Coordination: WoolRadar Issue #3.
- Code candidate: `codex/relay-v5-20261015` (PR #9). State: `codex/relay-state-v3`, `state.json` only.
- The state file is a checksum envelope `{format:1, sha256, payload}`. Hash the payload's sorted,
  compact, ASCII JSON bytes; validate `task-state.schema.json` and semantic checks in `relay.py`.
- Python `GitStateStore` uses existing Git authentication, never reads a secret file, never force
  pushes, and never edits a business checkout. Its workspace is a dedicated bare object store.
- Each update is a commit whose parent is exactly the checkpoint just read. Concurrent children
  cannot both fast-forward the shared ref. On conflict, re-read and re-plan; do not rebase stale results.
- `publish` checks parent checksum, revision +1, unchanged event history and the complete output of
  one `apply_event`. Valid JSON or a fast-forward alone does not authorize state replacement.
- Connected GitHub MCP callers can make the same tree/commit/ref operations, with `expected_sha`
  and `force:false`; they must independently execute the same validator before publishing.
- Local Git concurrency tests are real Git operations; live GitHub CAS must be reported separately.

## Ownership and events

One trusted operator writes each local outbox; multi-process outbox writing is unsupported.
Remote ownership is serialized by the shared Git branch, not by Issue comments.
Owner, previous owner, executor, version, SHA, 1–900 second lease and monotonic fence travel together.
Expired owners cannot mutate state. Recovery requires expiry and freshly observed code SHA;
recovery releases ownership and increments the fence before a fresh claim. Even expired overlapping
file scopes remain reserved until explicit recovery. Windows aliases, traversal and device names
are rejected; path comparisons for ownership are case-insensitive.

Event identity is `project/task_id/head_sha/event_type:expected_version`. The version suffix permits
heartbeats and repeated claims at an unchanged code SHA. Exact duplicates return the original receipt
without a new commit. Changed content at that key is rejected. Event JSON is produced by trusted
operators, not parsed from comments. No event value is executed as a command. `actor` is an audit
identity, not cryptographic authentication; the authenticated transport/operator must enforce it.
The production sender supplies its own current UTC time via `observed_now`, never trusting a queued
timestamp to extend a lease. Duplicate receipts are not evidence that a lease is still valid.

Transitions: ready → claimed → in_progress → evidence_ready → review_pending → reviewed → done.
Exceptions: blocked_local, quota_paused, network_blocked, conflict, failed, needs_approval.
`claim`, `start`, `evidence`, `request_review`, `review`, `done` implement the normal route.
`heartbeat`, `checkpoint`, `quota_pause`, `release`, `recover`, `block` implement lifecycle events.
`register` adds a new validated ready task without replacing any existing task or resetting history.
Registration rejects owner/history/evidence fields that imply prior execution. Only ready tasks can
be registered; proposed is reserved for pre-registration intake and cannot be published by this API.
Review must be by another actor, reference the current SHA and have a safe artifact path. Done also
requires passing evidence with a positive test count; it does not mean merged or deployed.

`checkpoint` advances code SHA only within a claimed file scope, clears old evidence/reviews and
requires a new verification. Both the old and new code identities remain in Git/event history.
Each task also includes dependencies, priority, definition of done, next action, Windows need,
remote eligibility, restrictions, blockers, work branch, tree cleanliness and last sync time.

## Sync and recovery

Every meaningful event first persists a checksummed atomic local checkpoint/outbox entry. Files are
flushed and replaced within one directory. Previous valid payloads remain in `.versions/`; Git keeps
remote history. Corrupt existing checkpoints are never silently overwritten. A crash before replace
leaves the previous file usable; stale temporary files are ignored, not destructively cleaned.
No retention cleanup is enabled; monitor disk use before authorizing a retention policy.

The outbox preserves causal insertion order. A pending delay or terminal blocked item stops successors,
including on later runs. A remote success followed by a local crash is safe only because the remote
sender is idempotent. Reconciliation checks the remote branch and event receipts before retrying.
429, rate-limited 403, 5xx and network failures use bounded exponential delay and Retry-After when
available. Ordinary 403 stops writes; conflict stops and requires re-reading. An unknown Git transport
error is not enough to distinguish every API failure; API adapters should pass exact status/headers
to `RemoteError`. Git-only retries cannot promise header fidelity.

Sync on claim, baseline, meaningful code change, test result, defect, conflict, block, PR change and
safe exit. Long-running operators checkpoint useful progress every 10–15 minutes; no empty commits.
`last_sync_at` means a confirmed previous remote acknowledgement, never a pending attempt. Keep the
remote checkpoint SHA and observed sync time in a separate local receipt to avoid self-referential SHA.

## Quota and execution boundary

Official desktop usage tool can provide account window percentages. Unknown metrics stay unknown.
At 20%/10% remaining, finish smaller safe units, checkpoint and avoid large new claims. A quota error
stops new model steps. `quota_pause` releases the task; Windows-only tasks remain locally blocked.
Inference is never required to replay an already persisted event or cold-read the next action.
Do not switch providers, paid APIs, secrets or shared-limit products to escape a limit.

The local CLI is 0.147.0 and exposes `codex exec`; official documentation was read at
https://learn.chatgpt.com/docs/non-interactive-mode on 2026-10-15. Saved login reports ChatGPT, but the
selected provider is `custom`, so its billing route is unverified. No inference experiment is run
until that route is proven to respect the user's plan/billing boundary. No executor is enabled.

An Issue, webhook, dispatcher decision or successful chat-send response is not proof of AI execution.
The existing ChatGPT chat received a bounded on-demand review dispatch; a fresh acknowledgement,
actual code/test artifact and new SHA are required to count live takeover. No scheduled backend,
Windows service, new automation, merge or production deployment is enabled by this protocol.

## Run and recover

From the isolated repository, run `python -m unittest discover -s tests -v` and
`python -m coordination.acceptance --output coordination/evidence/five-rounds.json`.
Use a workspace-local TEMP/TMP on restricted Windows. Git local push tests may require execution
outside the sandbox; they only touch synthesized local bare repos and never contact a network.

Read an already configured remote without changing business files:

```powershell
python -m coordination.relay_git --workspace .relay-object-store --remote https://github.com/lu403369069lu-prog/WoolRadar.git read
```

For delivery, append `deliver --event <validated-local-event.json>`. Do not initialize the production
branch automatically; the CLI exposes no reset or initialize command. If Git authentication is absent,
report it; do not extract a connector token. MCP can still synchronize the same validated state.
On corruption, retain damaged files, inspect `.versions/` and remote Git history, then explicitly
select and validate a last-good version. On SHA/owner conflict, retain both branches and stop writes.

For durable offline delivery, use `enqueue --event <event.json> --outbox <local-queue>` followed by
`sync --outbox <local-queue>` with the same global workspace/remote arguments. Enqueue makes no
network request. Sync records the last confirmed remote SHA/time separately and preserves them on
network failure. The independent Python program can replay without a model, but existing Git
authentication is required; this machine's GitHub connector login does not prove Git CLI login.

PR #9 targets #6 and includes parallel #7/#8 once. Do not merge all three blindly. No main update,
workflow activation, production DB, SAM installation/cache, devices, credentials or services are part
of this candidate. The manual workflow remains contents:read and persist-credentials:false.
