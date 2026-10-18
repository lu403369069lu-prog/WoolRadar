# Native GitHub Actions engineering relay — 2026-10-18

## Verified deployment

| Repository | Default-branch workflow | Durable checkpoint | Tested source |
| --- | --- | --- | --- |
| WoolRadar | [historical-family-relay.yml](https://github.com/lu403369069lu-prog/WoolRadar/actions/workflows/historical-family-relay.yml) | [engine.json](https://github.com/lu403369069lu-prog/WoolRadar/blob/chatgpt/actions-live-state-v1-20261018/engine.json), [history.jsonl](https://github.com/lu403369069lu-prog/WoolRadar/blob/chatgpt/actions-live-state-v1-20261018/history.jsonl) | [WR Draft PR47](https://github.com/lu403369069lu-prog/WoolRadar/pull/47) |
| YinQieJi/SAM | [historical-family-relay.yml](https://github.com/lu403369069lu-prog/YinQieJi/actions/workflows/historical-family-relay.yml) | [engine.json](https://github.com/lu403369069lu-prog/YinQieJi/blob/chatgpt/actions-live-state-v1-20261018/engine.json), [history.jsonl](https://github.com/lu403369069lu-prog/YinQieJi/blob/chatgpt/actions-live-state-v1-20261018/history.jsonl) | [SAM Draft PR15](https://github.com/lu403369069lu-prog/YinQieJi/pull/15) |

- Both workflows reside on **main**, every three hours at minute 23 UTC, with workflow_dispatch enabled. Private Actions job minutes are rounded up; this bounded cadence conserves plan quota. The scheduler can be delayed; its first literal `schedule` event is not established merely by push-triggered runs.
- Combined historical 50 family IDs = 26 WoolRadar/coord + 24 SAM; 38 have a bounded formal check mapping, 8 are external/policy gated, 4 have no adequate automated test mapping. Formal checks cover subsets only, never full business/native acceptance.
- Read-only evaluation runs on real source branch, with no write token. Separate persistence job verifies trusted queue hash, exactly ordered IDs, no business-complete claims, run replay keys and cursor CAS, then pushes only to isolated state branch. Append-only history remains committed. A failed formal test now fails the workflow **after** the result is persisted.
- Original-source tests do not write to the Windows/PLC/production system; no PR merge or release automation.
- Replay/fence safety unit tests: 4/4 in both default-branch GitHub Actions jobs.
- Verified default-branch read/run/write receipts: [WoolRadar run 39084179868](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39084179868), [SAM run 39084182504](https://github.com/lu403369069lu-prog/YinQieJi/actions/runs/39084182504). Both successful. Earlier branch-only tests also persisted evidence.
- Important: GitHub Actions **cannot invoke this ChatGPT subscription**, author arbitrary fixes, establish Windows-native corpus gold, or decide external approval by itself. The existing ChatGPT scheduled engineering task is a separate actor, not initiated by Actions. A separate approved coding agent/model connection would be needed for unattended source patch generation. No model key or PAT was added.

## Operational rules

- Read checkpoint `revision`, `cursor`, `last_run_key`, `families[id].status` and the latest full `history.jsonl` receipt before working; treat `FORMAL_SUBSET_PASS_NATIVE_PENDING` only as partial.
- If a check fails, inspect run receipt + real source SHA before patching. Any source repair must be in a separate reviewed Draft PR; do not auto-merge.
- Check GitHub Issue [#2](https://github.com/lu403369069lu-prog/WoolRadar/issues/2), [#3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3), and [SAM #1](https://github.com/lu403369069lu-prog/YinQieJi/issues/1) for changes and external gates.
- Prior transient WR-H03/WR-H07 errors resulted from the new runner initially omitting ephemeral `.test-tmp`; that prerequisite is fixed on main. Keep the original failed receipts rather than retroactively marking success. Re-evaluate when those families are reached again.
- Do not infer strict completion from an Actions green status; require original acceptance gates and real-source/Windows evidence.
