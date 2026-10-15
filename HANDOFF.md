# WoolRadar（羊毛雷达） — developer handoff

## Status
- V3 durable relay candidate is in draft PR #9, `codex/relay-v5-20261015`.
- It incorporates parallel PR #7/#8 onto #6 without modifying their branches.
- No PR is merged, no production deployment or long-running executor is enabled.
- Read `coordination/PROTOCOL_V3.md` and `coordination/evidence/` before resuming.

## Source of truth
- GitHub: https://github.com/lu403369069lu-prog/WoolRadar
- Production directory is not a Git checkout; do not use it as the candidate workspace.
- Current identity: read the full head SHA of PR #9; do not trust a copied old head.
- Machine checkpoint: `codex/relay-state-v3:state.json`, version 3, checksum envelope.

## Next Codex session
1. Read Issue #3, latest PR #9 and state branch; validate SHA, Schema, ownership and leases.
2. Preserve local modifications; use an isolated candidate, not the production directory.
3. Check for an actual ChatGPT takeover receipt/new SHA. A delivered chat message is insufficient.
4. Run current precise-file tests and the five-round acceptance runner, recording partial live gates.
5. Fix findings through a new reviewed commit, not by merging or replaying #7/#8 twice.

## Most recent task
- Goal: V5 reliable cross-executor relay, scoped to coordination infrastructure.
- Implemented candidate: versioned state/validator, owner fencing, file scopes, durable outbox,
  local versions, Git non-force synchronization, quota policy, cold recovery and fault acceptance.
- Limitations: ChatGPT automatic execution has no confirmed acknowledgement/artifact; CLI supports
  exec but selected custom provider billing route is unknown; Actions workflow settings endpoints
  are blocked by the connector. No deployment authorization is inferred from development authority.

## Commands and test results
- `python -m unittest discover -s tests -v`; exact counts/exit in `coordination/evidence/relay-unit-tests.json`.
- `python -m coordination.acceptance --output coordination/evidence/five-rounds.json`.
- Isolated tests use synthetic data. Round 1/5 remain partial without live ChatGPT execution evidence.
- Use workspace-local TEMP/TMP on restricted Windows; local Git push tests may require elevation.

## Changed files / decisions
- Coordination core, matching tests, schema, recovery protocol and redacted evidence only.
- Windows SQLite preview handle leak and corrupt-database rollback masking reproduced and fixed.
- State branch is independent of code branch; Issue #3 is the unique coordination index.

## Next actions
- Finish live independent takeover once a real authorized backend is available.
- Independently review and approve candidate integration; do not auto-merge or enable schedules.
