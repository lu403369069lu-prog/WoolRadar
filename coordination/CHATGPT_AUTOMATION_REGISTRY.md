# ChatGPT + repository recurring task registry (observed 2026-10-16)

This is a *human-readable handoff snapshot*, not an importable ChatGPT automation file. Tasks live in ChatGPT scheduling; GitHub cannot awaken a ChatGPT/Codex conversation by adding cron YAML. The existing scheduled jobs were actually inspected in this turn. Do not infer that their last-run timestamps certify GitHub writes, production behavior, live sources or self-directed development.

| ChatGPT task | Status at inspection | Beijing-time cadence | Durable checkpoint target |
| --- | --- | --- | --- |
| 海外羊毛雷达每日简报 | enabled | Every day 09:30; next configured start 2026-10-17 | User briefing; *only reproducible* false-positive/false-negative cases to WoolRadar Issue #2 when permitted |
| WoolRadar 全量推进 | enabled | Hourly at minute 00 | WoolRadar Issue #2; cross-project blockers to Issue #3 |
| SAM 全量推进 | enabled | Hourly at minute 10 | YinQieJi Issue #1; major cross-project blockers to WoolRadar Issue #3 |
| SAM 独立质量与发布验收 | enabled | Hourly at minute 30 | YinQieJi Issue #1; only new independently checked evidence |
| SAM WoolRadar 整体目标接续检查 | enabled | Hourly at minute 40 | WoolRadar Issue #3; this track is read-only when scheduled authorization is restricted |
| WoolRadar 质量与简报验收 (second QA) | **disabled** | Had an hourly minute 20 schedule | Do not reactivate without user direction |

All times above are reported in Asia/Shanghai; UTC minute offsets are the same for hourly tasks. The daily report is independent public-source research (X, Reddit, Linux.do and official issuers). It does **not** have automatic access to local Windows `reports/`, SQLite, browser sessions or an approved publication channel.

## GitHub-side candidate: different and strictly smaller behavior
- [WoolRadar Draft PR #35](https://github.com/lu403369069lu-prog/WoolRadar/pull/35): read-only metadata snapshots at UTC minute 05 each hour and at UTC 01:30 (Asia/Shanghai 09:30). The 09:30 event **does not** scan offers or deliver a real briefing.
- [SAM Draft PR #10](https://github.com/lu403369069lu-prog/YinQieJi/pull/10): read-only metadata snapshots at UTC minute 15 each hour.
- Both are inactive on their review branches until explicitly approved and merged to default. No cron run or model execution has been verified. GitHub Actions private repository minutes may cost money beyond free quota; budget and security must be checked before any activation.

## Strict record format for every future checkpoint
A meaningful engineering checkpoint must include:
1. Source actor and time zone; current source PR URLs and **fresh** HEAD/blob identities.
2. Exact command/runtime, exit status, passed/failed/skipped denominator, or explicitly NOT_EXECUTED.
3. Outcome grouped as DONE, PARTIAL or UNVERIFIED, with reproducer and evidence links.
4. V3 task owner/lease/fencing boundaries respected; no unsupported claims or second-owner takeovers.
5. One exact next engineering action; do not label unchanged metadata as progress or say a new PR is merged simply because a previous stacked PR merged.

Known current hard gates: WoolRadar producer URL batch identity, grant denial and subsecond preview fix integration/Windows regression, frozen unseen real-source quality, P06 live source and regional/payment gates, privacy-controlled real report publication & same-SHA consumer receipt (currently OUTPUT_NOT_CONNECTED). SAM 61 positives (3 answered, 58 refused), 522-source semantic ground truth, release/cache/rollback and the two projects' final three independent rounds.

## Security and execution boundary
No ChatGPT task may write to the repository if its scheduled context blocks GitHub writes; no alternate route to bypass platform review or approval. The ordinary chat may use authorized GitHub mutation tools to checkpoint **verified** work. No silent login, account claim, payment, Work, paid AI APIs, forced push, production Windows/PLC/SQLite mutation, unpublished local data or auto merge.
