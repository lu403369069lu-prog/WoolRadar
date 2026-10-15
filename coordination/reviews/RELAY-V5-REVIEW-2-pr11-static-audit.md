# V5 independent review — PR #11 / actual Codex return

Date: 2026-10-15. Reviewer: ChatGPT in this conversation, using connected GitHub repository read and write operations. This is a real, user-invoked independent review, **not** evidence of unattended ChatGPT scheduling.

## Exact baseline

- Candidate: [WoolRadar draft PR #11](https://github.com/lu403369069lu-prog/WoolRadar/pull/11), `codex/relay-return-20261015`, exact head `27796df5f9847c1bb5d48d2a445e418dfb3d8e96` (open, draft, not merged at review time).
- Exact tested Python implementation commit: `a2a67761105d13f7b9f8063c2d1c1a68062f4803`. Independent GitHub compare: final head is one commit ahead; **the changes since implementation were HANDOFF.md, PROTOCOL_V3.md, evidence and review documentation only; no Python implementation changes.**
- Earlier PR #9: `1440553f892676a938135e24938010d50cdd351a`; ChatGPT PR #10: `e81afca6661918b6261297f4251f413dbee09dab`.
- Live state branch `codex/relay-state-v3`: `2ee19a2b9aa0a7122b56a110ba853d657a0a09b9`, format 1, schema v3, revision 16. Codex's `WoolRadar/RELAY-CODEX-RETURN` is `needs_approval`, owner null, head PR#11 final; SAM and WoolRadar review-2 tasks remain ready/unowned. Checkpoint branch HEAD must be re-read before each future mutation.

## Independently verified through the GitHub connector

1. Fetched live PR metadata for #9/#10/#11, the newest state branch HEAD, and current `state.json` task summary. No PR was merged or retargeted.
2. Examined exact GitHub patches for `coordination/relay.py` and `coordination/relay_git.py`. Confirmed four concrete fixes in code: persist fail-closed queue conflicts and auth blocks; narrow HTTP status parsing so account name `lu403...` is not treated as HTTP 403; reject non-bare Git object directories; reject output events with already-expired lease. New `observe` is read-only identity discovery, **not** AI execution.
3. Fetched `tests/test_return_sync.py` and examined its seven regression tests, including local bare repository checks, explicit injected stdout/stderr errors, single-writer queue ordering and SHA discovery.
4. Read `coordination/evidence/return-20261015/fixed-tests.txt`: it contains `Ran 57 tests in 22.083s\nOK`. This is **Codex's recorded Windows result**. It was **not executed by this reviewer**.
5. Read `live-recovery.json` and `live-concurrency.json`, which record subprocess crash exit 17, bounded dead-loopback proxy/retry and replay once, model_calls=0, and one accepted/one rejected GitHub branch update. These are plausible consistent remote artifacts but were **not independently reproduced** in this review.
6. Read [Codex return report](https://github.com/lu403369069lu-prog/WoolRadar/blob/27796df5f9847c1bb5d48d2a445e418dfb3d8e96/coordination/reviews/CODEX-RETURN-20261015.md) and the actual [coordination Issue #3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3); the final phase-exit comment corresponds to the revision 16 checkpoint.
7. No new PR #11 code was applied to the default branch. The return code is a stacked draft candidate. It should not be separately combined with PR #7/#8 as if they had independent bases.

## Review assessment

**Source review: no newly demonstrated blocking P0/P1 in the examined PR #11 patch.** This is not the same as a complete security approval or a fresh run of 57 tests.

- Confirmed the original P1 offline/403 misclassification was a plausible source-code defect; the new exact HTTP status regex addresses the given reproduction while retaining fail-closed unclassified network errors.
- `GitStateStore.__init__` now checks bare status with Git, and does not invoke a fetch before that check. Existing git object store symlinks/path aliases still depend on the OS and trust of the chosen workspace; keep the isolation authorization boundary.
- `Outbox.replay` persists recognized validation errors and blocks successors, preventing unbounded retries. The error-code classifier uses a conservative allowlist of uppercase tokens; unexpected exceptions can still abort the process, so operational logs remain necessary.
- The status parser is intentionally best effort over Git stderr; it is not a full HTTP status/Retry-After API transport. Do not label all 403/429/5xx production classifications covered.
- Clock and identity boundary: `actor` is auditable text; enforcement is by separately authenticated Git credentials and trusted execution. A lease is not a cryptographic identity. No server-authoritative clock or unattended AI executor is established.
- User-triggered ChatGPT PR#10 followed by Codex's actual GitHub cold read/PR#11 is real *requested* relay progress. It does **not** prove the missing automated ChatGPT trigger.

## Conclusion and next gate

**Result: independent static review + current-state readback complete.** Recorded 57/57 tests are correctly bound to implementation SHA; actual Windows test execution remains Codex evidence, not this reviewer's test run. V5 stays partial because unattended ChatGPT activation is unavailable or unverified.

The next isolated, authorized work is to demonstrate genuine V3 events from an actual ChatGPT executor (claim/start/evidence, with atomic ref CAS), with an artifact under `coordination/reviews/` and a genuine GitHub SHA. If claim/release cannot be completed safely, do not leave an indefinite owned task; disclose exact state.

No main/production merge, background agent install, paid API, Windows scheduler, credentials or business database modified.
