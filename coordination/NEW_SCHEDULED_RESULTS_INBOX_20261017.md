# New scheduled results inbox — separate from frozen 50 historical families

**Contract effective for the October 17, 2026 history snapshot.** This is *not* another list of backlog tasks and not a release-ready queue.

The 50-family pre-existing historical snapshot is fixed in [HISTORICAL_FREEZE_50_20261017.json](HISTORICAL_FREEZE_50_20261017.json). The scheduler may keep running at its existing cadence, but **new hourly findings must not create more H-IDs or silently reset the frozen history completion denominator**. Current periodical notifications remain unchanged (hourly already muted). The user does not want routine notification interruptions.

## Only accept an item when it has a material, novel delta

- Unique `event_key`, event timestamp, repository/PR, actual immutable source/test SHA, explicit `NEW_SOURCE`/`NEW_FAILURE`/`NEW_TEST_PASS`/`BLOCKED_EXTERNAL`, evidence link, owner and next action.
- Before writing, read the frozen machine file and existing issue comments; for a finding about a previously frozen family, update **the existing ID** without counting a new family.
- A new discovery unrelated to the frozen 50 is parked under this file or a separate new-queue issue, and **may not extend the pre-October-17 history recovery**. No hourly append unless a material source delta really exists.
- If the external Scheduled executor lacks GitHub-write permission or a safety check rejects the write: **do not bypass, retry through alternate identities, or claim success**. Put a self-contained patch/test/failure with `BLOCKED_WRITE` in the scheduler's regular task result, not a fabricated GitHub receipt.
- Do not turn routine status echo, repeated tests at identical SHA, or refreshing issue URLs into a new result. A zero-change hour is `NO_MATERIAL_DELTA` and should create **no new comment or queue entry**.
- All offline Windows/Node24+26/zod/MCP/package data/install/SQLite sensitive steps belong in the [Codex local validation handoff](CODEX_LOCAL_VALIDATION_HANDOFF_20261017.md), not a new assignment for ChatGPT cloud Scheduled.

## Frozen debt as of 2026-10-17

SAM integrated PR15 is Draft; exact complete-source Linux Node22 standalone 39/39 TAP including real rg14.1.1 572 assertions, but not full `cards.ts`/zod/MCP Node24/26/Windows. Wool unified PR39 Draft Python source 58/58 focused tests, but genuinely independent new public blind holdout is still required (old initial 47 TP1 FN3 = 25% recall, one same-campaign false split). Old coordinator PR11 historical Windows57 test receipt is not an autonomous GitHub permission grant. Real user data must remain local and excluded from GitHub.

**Meaningful success:** exact branch source diff, test exit/denominator, proven Github commit and targeted existing Issue. **Meaningful blocked:** reproducible reason, owner and fixture/command. Zero delta ⇒ silence, not an infinite queue.
