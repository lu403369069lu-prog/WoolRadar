# WoolRadar — developer handoff

## Current verified work
- Follow-up draft PR #11: codex/relay-return-20261015, base is PR #9; PR #9/#10 preserved.
- Tested minimal implementation: a2a67761105d13f7b9f8063c2d1c1a68062f4803, Windows 57/57 exit 0.
- Exact original implementation 19826b6af9e77f650ed05e7c133dd3184f114de3 and actual ChatGPT PR #10 e81afca6661918b6261297f4251f413dbee09dab each rerun 50/50 exit 0.
- Existing five-round runner rerun once at original PR9, exit 0; original partial gates remain.
- Actual user-invoked ChatGPT new artifact was cold-read and independently verified by Codex.
- Read coordination/reviews/CODEX-RETURN-20261015.md and coordination/evidence/return-20261015/.

## Real synchronization evidence
- Existing independent Git authentication reads/writes private state branch; no connector credentials extracted.
- Ordinary Python/Git saved an event, survived process exit 17 and controlled child-process network failure, replayed once after recovery and deduplicated the next run, with zero model calls.
- Two concurrent real GitHub clients of this Codex task produced one accepted update and one REMOTE_CONFLICT.
- One-shot observe discovered the real PR10 ref SHA and persisted a stable cache; it does not start AI.
- Meaningful state checkpoints were published within 2–5 minutes. Code checkpoint revision 12: 8e2784a72130a8b027f3ec080ca53876d5ffcb2a; always fetch latest before continuing.
- State branch codex/relay-state-v3 is independent of code. Validate checksum/schema, current owner/version/fence and remote head before writing.

## Minimal fixes
- Reject ordinary business .git and aliased workspace paths as synchronization stores.
- Persist domain conflicts and BLOCKED_AUTH terminal state without retry loops.
- Reject already-expired output leases; preserve existing expired-owner checks.
- Match explicit HTTP status syntax, avoiding account digits 403 being mistaken for a network response.

## Outstanding gates
- Formal ChatGPT tasks RELAY-V5-REVIEW-2 and RELAY-SAM-REVIEW-2 remain ready/unowned, with no fabricated claim/start/evidence.
- No unattended ChatGPT trigger, cross-machine clock authority or permanent poller has been accepted/deployed.
- Git stderr cannot provide complete API headers/Retry-After; API failure fixtures are distinguished from actual Git/network tests.
- Review PR11 before integration; do not auto-merge or separately reapply #7/#8 after PR9.
- No SAM business tests were rerun; production DB/devices/services/schedules/providers remain untouched.

## Resume
1. Read latest Issue #3, PR9/10/11 heads and state branch; a historical SHA is not permission to overwrite newer progress.
2. Preserve local edits and use a real isolated worktree; read the current V3 protocol and one-shot commands.
3. Inspect retained failed queues before reconciliation. Do not reset or silently replay a superseded event.
4. Claim only your actual task/identity. Formal ChatGPT acceptance must be performed by its real authorized executor.
5. Append meaningful Issue receipts with event-key deduplication; do not replace the entire Issue body.
