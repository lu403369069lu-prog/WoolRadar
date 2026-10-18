# Codex 双仓任务路由 / ChatGPT→Codex 交接索引（2026-10-18）

**任务入口（Codex 应逐项执行而非重新规划）**：

- **WoolRadar + V3/V5协调**：[WoolRadar/CODEX_NEXT_TASKS_20261018.md](https://github.com/lu403369069lu-prog/WoolRadar/blob/main/CODEX_NEXT_TASKS_20261018.md)；技术回执写 [WoolRadar Issue #2](https://github.com/lu403369069lu-prog/WoolRadar/issues/2)。
- **SAM / YinQieJi**：[YinQieJi/CODEX_NEXT_TASKS_20261018.md](https://github.com/lu403369069lu-prog/YinQieJi/blob/main/CODEX_NEXT_TASKS_20261018.md)；技术回执写 [SAM Issue #1](https://github.com/lu403369069lu-prog/YinQieJi/issues/1)。
- 总协调与跨仓依赖：[WoolRadar Issue #3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3)。机器断点分别见两仓 `chatgpt/actions-live-state-v1-20261018:engine.json`；50家族唯一目录 `chatgpt/scheduled-review-ledger-20261017:coordination/HISTORICAL_ALL_50_FAMILY_STATUS_20261017.json` 和同分支 `coordination/AUTOMATION_RELAY_LEDGER_V1.json`。**所有状态在执行时重新读取，不以本文日期做最后 HEAD**。

## 分工与不会重复的成果

| 工作 | 当前实证 | 当前承接方 / 严格剩余门槛 |
|---|---|---|
| WoolRadar 原仓 Windows 云端完整测试 | [#39088415016](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39088415016)，固定业务源 `a0fc93c4b54d16f399c28ffb401d682fa823b107`，359/359 exit0 | **ChatGPT/Actions 已做**，Codex无需对相同源与环境原样重测；Codex 继续真实本地生产脱敏副本/冻结 SQLite/外部审批 |
| COORD-H03/H04/H05/H06 原协调单测 | [#39088393940](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39088393940)，`codex/relay-return-20261015` SHA `27796df5f9847c1bb5d48d2a445e418dfb3d8e96`，6+11+15+5+4+7 = 48/48 exit0 | **ChatGPT/Actions 云端专项已做**；Codex 负责 Windows 本地/真 Git fence/跨 PR 回归、将独立工作流映射回50项机器队列的可信证据协议 |
| SAM 原仓完整 Node 测试 | [#39088430854](https://github.com/lu403369069lu-prog/YinQieJi/actions/runs/39088430854)，实际候选 `ba24b3db342fc5c648effd95d477eda154cff909`，构建 exit0，测试 288/294、6 fail、exit1 | **云端继续保留红灯**；**Codex 必须从本地原插件工作区核验六份真实冻结发布资产**，不得伪造指针、清单、答案或源哈希 |
| SAM-H18 Windows 大小写语义 | [PR22](https://github.com/lu403369069lu-prog/YinQieJi/pull/22) 的真正 Windows / rg [Actions #39088993315](https://github.com/lu403369069lu-prog/YinQieJi/actions/runs/39088993315) **1/1 exit0**：rg 在混合大小写时仍枚举合成受保护文件，但 SAM 策略正确拒绝；源 SHA `80c0b390f63407f3142efe8477bd15d17ef45a86` | **ChatGPT/Actions 已做原生合成用例**；Codex 不必同SHA重测，只需补真实更多 Windows 设备/FS及跨入口集成；仍非严格完成 |
| 独立金标/业务审批等外部门槛 | 原历史家族 50 中有8项 gated | **用户/授权维护者/合格业务证据**；Codex不能代为签收 |

## 已部署的 Actions 能力

- 两仓默认分支 `main:.github/workflows/historical-family-relay.yml`：每3小时 UTC :23，`workflow_dispatch`，每轮读、测、故障优先、独立状态分支CAS写回。
- WoolRadar `main:.github/workflows/agent-pr-acceptance.yml`：新业务 PR 读权限 Windows 全量测试；
  `main:.github/workflows/coordination-pr-acceptance.yml`：新协调 PR 读权限专项测试。
- SAM `main:.github/workflows/agent-pr-acceptance.yml`：新代码 PR 读权限 Node 构建 + 全量测试。缺少可信冻结物时保持 CI 红灯，而非篡改测试。
- GitHub Actions **不会调用 ChatGPT/Codex 对话或擅自写任意补丁**；Copilot Cloud Agent 另需已授权的独立编程模型资格。当前本机 Codex 只在真实启动/领取后执行，不能将这份文档当作已唤醒或已 claim。

## Codex 下一次启动的执行契约

1. 从上述两个专属文档和 Issue #1/#2/#3 冷读最新状态、当前 HEAD、其他执行者的 owner/lease/fence；不得覆盖已占用任务，也不修改用户正在运行的工作树。
2. 对能够本地解决的最高优先级缺口，先做**完整原始数据 provenance 审查**。冻结文件确实缺失则记录 `BLOCKED_ORIGINAL_RELEASE_SOURCE`，继续下一独立 family；不要把多次尝试同一缺失文件算成多项完成。
3. 在独立安全 worktree 修补真正的源码缺陷、附正式失败→通过测试，提交 Draft PR，利用现有工作流验证。测试日志须说明 repo/source完整 SHA、命令、系统/依赖版本、exit、总数与失败标题；PR 不自动合并。
4. 本地仅汇报经授权的脱敏哈希、来源链、统计、最少量代码/测试；禁止生产数据库、个人资料、浏览器Cookie、厂商受限手册、私人聊天或秘密上传。不得绕过平台安全/权限阻拦。
5. 每解决一个可执行缺口便领取下一不同 family；云端部分验收与原生业务严格 COMPLETE 分开，所有真实证据回写所属技术 Issue + 协调 Issue 的新事件键，重复进度不刷屏。

**严格业务验收仍0/50；本交接文件与 Issue 评论不会自行启动 Codex。**

交接索引事件键：`interactive-20261018-codex-handoff-original-48-wr359-sam288`
