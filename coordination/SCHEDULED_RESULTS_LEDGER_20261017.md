# Scheduled task outcome backfill ledger — 2026-10-17

**This ledger is a user-authorized INTERACTIVE GITHUB WRITE, NOT a successful GitHub write by ChatGPT Scheduled.** The historical Scheduled environment has rejected writes. Enablement/last_run_time alone are not proof of completed work; evidence and promotion status must remain separate. This document is staged only in a Draft PR; top-level Issue comments below are already persistent.

## Enabled tasks, verified through task service

| Active task | Schedule (Asia/Shanghai) | Last run, UTC | Backfill classification |
|---|---|---|---|
| WoolRadar 最小项逐件闭环 | hourly :00 | 2026-10-16T23:03:13Z | Historical isolated bug-fix outputs; now subset repatched in interactive PR37 |
| SAM 最小项逐件闭环 | hourly :10 | 2026-10-16T23:15:47Z | T009 and claim scope static audits; cannot count as MCP pass without real source evidence |
| SAM 独立质量与发布验收 | hourly :30 | 2026-10-16T23:34:32Z | Ancestor/root exclusion red/green candidates; test-only existing commit verified |
| SAM WoolRadar 整体目标接续检查 | hourly :40 | 2026-10-16T23:44:36Z | Read-only QA/coordination, no direct repository commits proven |
| 海外羊毛雷达每日简报 | daily 09:30 | 2026-10-16T01:54:44Z | Independent public source check; Windows report bridge not connected |

There are 5 enabled; other historical tasks were disabled/completed. Time values are execution metadata, not evidence of full outcomes. The next daily 09:30 must **not** be marked executed until actual proof is observed.

## Outcome registry

| Event key | Recovery evidence | GitHub writeback | Real status |
|---|---|---|---|
| wool/scheduled/private-hosts | Past isolated 15/15, not originally committed. Interactive source fix + 2 formal tests + host-focused 2 methods/21 denied/3 allowed exit0 | [Wool Issue2 #6227111895](https://github.com/lu403369069lu-prog/WoolRadar/issues/2#issuecomment-6227111895), [Draft PR37](https://github.com/lu403369069lu-prog/WoolRadar/pull/37) | DRAFT_PATCHED; full tests/network URL redirects pending |
| wool/scheduled/strict-bool-identity | Past isolated 27/27 NOT remotely uploaded as Scheduled output. Interactive fix exact proof only literal true + 3 new formal regressions; 5 isolated methods/20 synthetic cases exit0 | [Wool Issue2 #6227155303](https://github.com/lu403369069lu-prog/WoolRadar/issues/2#issuecomment-6227155303), PR37 | DRAFT_PATCHED; full 23-method suite not run |
| wool/scheduled/signed-delivery-v2 | Past offline synthetic Ed25519 `python -B -m unittest -v test_delivery_v2_preflight.py` 22/22 exit0; keys fake, independent runtime channel absent | [Wool Issue2 #6227074952](https://github.com/lu403369069lu-prog/WoolRadar/issues/2#issuecomment-6227074952) | PROTOTYPE_ONLY; DELIVERY_BRIDGE_VERIFIED=false / OUTPUT_NOT_CONNECTED |
| sam/scheduled/rooted-exclusion | Recent 19 new controls old 5/19→offline candidate19/19 with earlier56/56; source-policy main blob `3fe1c9a5dbf4d5834a8f9f19eb8e3284d6df51ed` still has ancestral deny hole. Preexisting regression-only [commit 447aa3f](https://github.com/lu403369069lu-prog/YinQieJi/commit/447aa3fc722703fb8fce0e07361a99d073ea6df2) actually verified | [SAM Issue1 #6227075361](https://github.com/lu403369069lu-prog/YinQieJi/issues/1#issuecomment-6227075361), [follow-up #6227084183](https://github.com/lu403369069lu-prog/YinQieJi/issues/1#issuecomment-6227084183) | TEST_EXISTS_FIX_NOT_INTEGRATED; main SAM owner in progress |
| sam/scheduled/T009 | Scheduled synthetic source-structure 7/7 and offline projection10/10 against reported upstream blob `5257168283fd193ce6694ed8f5a8646b4e4c558b`, NOT a valid new source-bound answer | Scheduled conversation record only | UNCONFIRMED_SOURCE_GOLD; do not change 10/61 official business measure |
| sam/scheduled/claim-scope | Scheduled bounded static tests 7/7 exit0 against known `claim-audit.ts`/`card-index.ts`/`cards.ts` blobs, no upload | Scheduled conversation record only | REVIEW_CANDIDATE, independent source claims pending |
| wool/daily/2026-10-16 | RackNerd×AdminBolt new 150/year VPS + 30 lifetime licenses chatter reported but no verified remaining batch or mainland eligibility, other tracked projects unverified | [Wool Issue2 #6227074952](https://github.com/lu403369069lu-prog/WoolRadar/issues/2#issuecomment-6227074952) | LEAD_ONLY_NOT_CLAIMABLE |
| coordination/read-only | Exact PR/V3 read checks; main PR23 SHA `8023232586fd5d017981ea83ea0785cf381f7cc2` Windows 406/406 pass on the **separate Codex actor**; main SAM PR5 SHA `5aeb852577cc53da76f9a0b5e78dfef63a83a35b` actual 10/61 source-bound | [Cross-project Issue3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3#issuecomment-6227075815) | OVERALL_IN_PROGRESS; neither is Scheduled's own new Windows/MCP test |

## Future writeback contract

Each hour: named task, execution UTC, source channel `scheduled/interactive/codex`, immutable repo/HEAD/blob, exact command/exit/test denominator and whether actually re-run, user-visible output reference, `DONE/PARTIAL/UNVERIFIED/BLOCKED_WRITE`, privacy/scope, dedupe event_key, and an actionable next-smallest item. A changed prompt, `last_run_time`, or GitHub workflow cron in Draft does **not** count as an execution. On Scheduled permission denial, never retry through an unapproved channel or invent upload; preserve an independently readable digest for the next authorized interactive conversation. This 2026-10-17 document is a single partial **backfill checkpoint**, not a complete historical task run export.

GitHub cron Draft PR35 / YinQieJi PR10 remain unmerged and potentially bill private runner minutes; no activation. No auto merge, raw Windows reports, credentials, payments, third-party registrations, Work/Codex quota or paid AI APIs.
