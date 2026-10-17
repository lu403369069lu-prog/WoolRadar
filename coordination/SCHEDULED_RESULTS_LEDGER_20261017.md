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
| sam/scheduled/rooted-exclusion | Scheduled original new19 cases 5pass/14fail; isolated candidate19/19 plus earlier56/56; its result was NOT uploaded by Scheduled. Verified prior regression-only [commit 447aa3f](https://github.com/lu403369069lu-prog/YinQieJi/commit/447aa3fc722703fb8fce0e07361a99d073ea6df2). This interactive run then staged real source-policy fix and reused 11 + 19 formal controls, with **independent extracted Node19/19 exit0** | [SAM Draft PR12](https://github.com/lu403369069lu-prog/YinQieJi/pull/12), [SAM Issue1](https://github.com/lu403369069lu-prog/YinQieJi/issues/1#issuecomment-6227217004) | DRAFT_PATCHED; full real TypeScript test and Windows Node24/26/MCP not run |
| sam/scheduled/T009 | Scheduled synthetic source-structure 7/7 and offline projection10/10 against reported upstream blob `5257168283fd193ce6694ed8f5a8646b4e4c558b`, NOT a valid new source-bound answer | [SAM Issue1](https://github.com/lu403369069lu-prog/YinQieJi/issues/1#issuecomment-6227217004) | UNCONFIRMED_SOURCE_GOLD; do not change 10/61 official business measure |
| sam/scheduled/claim-scope | Scheduled bounded static tests 7/7 exit0 against known `claim-audit.ts`/`card-index.ts`/`cards.ts` blobs, no upload | [SAM Issue1](https://github.com/lu403369069lu-prog/YinQieJi/issues/1#issuecomment-6227217004) | REVIEW_CANDIDATE, independent source claims pending |
| wool/daily/2026-10-16 | RackNerd×AdminBolt new 150/year VPS + 30 lifetime licenses chatter reported but no verified remaining batch or mainland eligibility, other tracked projects unverified | [Wool Issue2 #6227074952](https://github.com/lu403369069lu-prog/WoolRadar/issues/2#issuecomment-6227074952) | LEAD_ONLY_NOT_CLAIMABLE |
| coordination/read-only | Exact PR/V3 read checks; main PR23 SHA `8023232586fd5d017981ea83ea0785cf381f7cc2` Windows 406/406 pass on the **separate Codex actor**; main SAM PR5 SHA `5aeb852577cc53da76f9a0b5e78dfef63a83a35b` actual 10/61 source-bound | [Cross-project Issue3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3#issuecomment-6227075815) | OVERALL_IN_PROGRESS; neither is Scheduled's own new Windows/MCP test |

## Future writeback contract

Each hour: named task, execution UTC, source channel `scheduled/interactive/codex`, immutable repo/HEAD/blob, exact command/exit/test denominator and whether actually re-run, user-visible output reference, `DONE/PARTIAL/UNVERIFIED/BLOCKED_WRITE`, privacy/scope, dedupe event_key, and an actionable next-smallest item. A changed prompt, `last_run_time`, or GitHub workflow cron in Draft does **not** count as an execution. On Scheduled permission denial, never retry through an unapproved channel or invent upload; preserve an independently readable digest for the next authorized interactive conversation. This 2026-10-17 document is a single partial **backfill checkpoint**, not a complete historical task run export.

GitHub cron Draft PR35 / YinQieJi PR10 remain unmerged and potentially bill private runner minutes; no activation. No auto merge, raw Windows reports, credentials, payments, third-party registrations, Work/Codex quota or paid AI APIs.


## Follow-up independent historical-vs-business evidence reconciliation

During the same authorized interactive backfill, main WoolRadar PR23 progressed **independently under Codex owner** from `8023232586fd5d017981ea83ea0785cf381f7cc2` to `6babbe12727652e8626e0fe6f554eb01fecd4a30`. The published clean Windows test receipt is for **source code SHA `3a71060b0134a55c60f5543382bd1758768a2b4a`**, 412/412 exit0. It does not validate the new sampler PR37, or any later code at a different SHA.

The actual, independent new-window **read-only result accounting** was separately recomputed from immutable published redacted GitHub blobs `f326ec8ff80c83ddb68fcbc33b5b6bd860cee6d8` (evaluation) and `9498f58fd78358cff4370e46b8e666ceb6a6565c` (freeze): 7 public sources, 413 raw snapshot rows, 102 previously seen and 6 identity-unverified excluded, 305 eligible URLs, 47 unique reviewed rows. TP1/FP0/FN3/TN40/unknown3, independent recall 25% (1/4), **acceptance still FAILED**. Later replay TP4/FP0 on the already exposed 47 is development only, not an unseen holdout; one same-campaign different-URL false split remained. See [independent Issue2 recount](https://github.com/lu403369069lu-prog/WoolRadar/issues/2#issuecomment-6227240468).

Do not let green synthetics (sampler/private hosts or signed report) or `last_run_time` hide the red independent business window, or claim a real 09:30 report upload. `OUTPUT_NOT_CONNECTED` and `DELIVERY_BRIDGE_VERIFIED=false` continue.


## Measured hourly productivity bottleneck and exact read-only cron defect (2026-10-17)

Audit of available historical Scheduled conversation messages found **at least 35 distinct coordination/execution rounds**. In those *reviewed* rounds, **zero successful GitHub writes were substantiated from the Scheduled executor**: attempts were blocked by the platform's GitHub safety/approval boundary. This is not a claim that every historical run was obtained or counted, nor that there were zero useful offline investigations. PR37/PR12, fixes, issue comments and this ledger were written in **authorized interactive chat**, not an unattended Scheduled run. **Task last_run_time does not equal delivered PR**. The GitHub workflow drafts are read-only, unmerged, and do not run AI development or automatically publish ChatGPT Scheduled results.

A separate real bug was confirmed in both *not-yet-deployed* GitHub checkpoint workflows: a `--jq` formatter had **double-backslash** `\\(` escaping around PR fields and silently printed literal placeholders. A real local `jq 1.7` invocation with synthetic PR `number=37, state=open, draft=true, head=abc123` returned `- PR #\(.number) ...` with the old filter (misleading exit0), versus `- PR #37: state=open; draft=true; head=abc123` after switching to jq's single-backslash interpolation. Both candidate workflows were independently repaired, committed and connector-readback matched:
- WoolRadar checkpoint PR35: workflow Git blob `2c81eae523b8b8e43d876ec47157635ce76d1b0a` → `7a9389ce2a85feaa4b59f138a89974b1121f3de8`. Actual edit commit `fb8f0be67b8c1c4e27738be1206c2498b598fb87`.
- SAM checkpoint PR10: blob `793345fe50de36b2660d0adfdb20cb20d34c28f0` → `6a5637c4744c83e39c88892a4c2fe3534a57ac38`. Actual commit `16348f8b6916a39ff2ad95205d1cda24b9106b76`.
- Evidence: [Wool technical receipt](https://github.com/lu403369069lu-prog/WoolRadar/issues/2#issuecomment-6227296359) and [SAM technical receipt](https://github.com/lu403369069lu-prog/YinQieJi/issues/1#issuecomment-6227296786).

All four *ChatGPT* hourly engineering/QA/coordination prompts were subsequently updated without altering the minute cadence: development must return one new, executable source/test diff with exact SHA and red/green exit or admit `NO_NEW_RESULT`; on a legitimate write denial it must preserve the **complete portable patch in the Scheduled task message** marked `BLOCKED_WRITE` rather than claim a commit. QA only returns genuinely new independent findings and deduplicates old ones; coordination reports actual SHA deltas and avoids re-reading/outputting identical narratives. **Prompt upgrades do not grant denied GitHub write permissions**, do not change notification settings and do not provide a durable output store by themselves. Daily 09:30 wool brief prompt and schedule remain unchanged.

Remaining acceptance: an independently observed genuine Scheduled GitHub delivery, as opposed to a later interactive salvage, remains `NOT_VERIFIED`; daily true local report consumption remains `OUTPUT_NOT_CONNECTED`. No private runner/workflow was merged or executed, and no Codex/Work/paid AI API/production data was used.
