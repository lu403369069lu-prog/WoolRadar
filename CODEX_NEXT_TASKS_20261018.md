# Codex 接力任务 — 2026-10-18（WoolRadar / 协调）

> 用途：Codex Desktop 在 Windows 本机读取 GitHub 后直接继续既有工程。此文档是交接与待办，**不是已领取任务、锁、自动唤醒或业务验收**。不要重建仓库、推翻架构、要求用户复制其他对话。先遵守仓库 `AGENTS.md` 和现有 `HANDOFF.md`；所有 GitHub HEAD/断点以执行时冷读为准。

## 0. 已有真实结果：不要从头重复

- 2026-10-18 云端 Windows runner 在实际 WoolRadar 源代码 SHA `a0fc93c4b54d16f399c28ffb401d682fa823b107` 上运行：
  `python -m unittest discover -s tests -p test_*.py` -> **Ran359、实际pass358/skipped1，原runner exit0曾误作全绿；现已由新fail-closed门禁修正为集成FAIL**；[最新校验](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39089777897)。
- WR-H03 先前临时目录缺失引起的 CI 错误，环境修复后 6/6；WR-H07 子集 24+46+5 = 75/75。不要把原环境错误当作源码漏洞，不要无意义反复跑已绿的完全相同 SHA。
- Actions 调度文件位于 `main:.github/workflows/historical-family-relay.yml`；只读 `evaluate` + 独立最小权限 `persist` 已验证，约每3小时 UTC :23。
- 进度唯一原始机器账本：[engine.json](https://github.com/lu403369069lu-prog/WoolRadar/blob/chatgpt/actions-live-state-v1-20261018/engine.json) / [history.jsonl](https://github.com/lu403369069lu-prog/WoolRadar/blob/chatgpt/actions-live-state-v1-20261018/history.jsonl)；50家族主目录见 `chatgpt/scheduled-review-ledger-20261017:coordination/HISTORICAL_ALL_50_FAMILY_STATUS_20261017.json`。2026-10-18 查到 WoolRadar Rev14/cursor2；**执行时重读**。
- 云端 PASS 不等于真实生产冻结数据库、来源真伪、提醒送达、账户审批或 50 family 业务 COMPLETE（仍无严格验收通过）。

## 新增云端实证（2026-10-18 01:58 UTC，Codex 避免重复）

- 已部署 **[独立协调 PR 验收工作流](https://github.com/lu403369069lu-prog/WoolRadar/actions/workflows/coordination-pr-acceptance.yml)**；读取真正的 `codex/relay-return-20261015` 源 SHA `27796df5f9847c1bb5d48d2a445e418dfb3d8e96`。正式 GitHub Linux [Actions #39088393940](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39088393940) **exit0**，六组原模块 **6+11+15+5+4+7 = 48/48**；H03/H04/H05/H06 原源码专项已完成**云端子集验收**，但绝非 4 个业务 family 严格完成。
- 已部署 **[WoolRadar 新源码 PR Windows 验收工作流](https://github.com/lu403369069lu-prog/WoolRadar/actions/workflows/agent-pr-acceptance.yml)**；从实际 `a0fc93c4b54d16f399c28ffb401d682fa823b107` 源检出，正式 [Actions #39088415016](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39088415016) **Ran359/pass358/skipped1/exit0，新防伪门禁标FAIL**（不能声称359项都实际通过）。
- **Codex 不要再无条件重跑 H03~H06 的同一固定源码、同一测试、同一 Linux 环境**。以下命令保留作版本升级/Windows 原生或修复后重新验证的复现规范。Codex 的增量任务是本机/真实 Git 断点、跨 PR 叠加差异、审批和冻结外部证据，以及把正式测试逐家族联到既有 Actions 自动队列；云端全绿不能取代本地现场验收。

## 新发现的最小本机阻塞 — WR-H12 / DIGEST-UPSTREAM-01（CODEX_REQUIRED；尚未认领）

**2026-10-18 GitHub 独立正式取证，不再把 Ran359 误写成359个真正通过：** 双仓 Actions 已修复“测试成功退出却全部/部分跳过”的错误PASS判定。WoolRadar main 修复 commit `5b6dc16397927631dbdfa2d341d47b2863ab3c01`，原业务候选 SHA `a0fc93c4b54d16f399c28ffb401d682fa823b107`，正式 [Windows Actions #39089777897](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39089777897)：runner防伪回归 **8/8 exit0**，历史 WR-H03 **6/6** 与 WR-H04 **5/5** 真正通过；全量原业务源码 `python -m unittest discover -s tests -p 'test_*.py'` **Ran 359 / passed 358 / skipped 1 / exit0**，新 fail-closed 集成状态 **FAIL**，已写独立状态分支 Rev15。此 FAIL 是*未执行的原生上游门槛*，不等于358条断言失败。

**静态溯源**：`tests/test_digest_runtime.py` 真实 Git Blob `6fad926bbccecc6bab957486099647e18f8ef98b`，用 `@unittest.skipUnless(PYTHON.exists(), 'installed upstream runtime required')` 跳过 `test_upstream_provider_http_is_budgeted_across_process_invocations`，`PYTHON = Path('C:/WoolRadar/nodes/digest-ai-agent/upstream/.venv/Scripts/python.exe')`。它需要本地已安装真实上游、真实依赖 `httpx` 与其消费逻辑。云端没有该 Windows 路径，不能为了绿灯伪造目录、创建假exe、删除skip或模拟已经验收的原生服务；对应 WR-H12 日报/真实上游桥接仍要求用户授权。

**Codex 下一最小动作**：先 `git status --porcelain=v1`、读既有 owner/lease 与本地源 HEAD，在真正授权的隔离 worktree/测试复制件中确认该原始 `.venv/Scripts/python.exe` 是否存在及其依赖，确认上游文件确实是正确的被测版本；不要修改生产环境、运行真实网络任务或创建假依赖。若存在且授权，只在离线 `httpx.MockTransport` 条件下执行：
`python -m unittest discover -s tests -p 'test_digest_runtime.py' -v`
预期 **1项实际执行且pass，skip=0，exit0**；保留原工作目录和固定SHA、Python/httpx版本、最小脱敏回执。若缺失或未经允许，标 `BLOCKED_UPSTREAM_RUNTIME_OR_APPROVAL`，附缺失前置条件后转去下一家族，不得冒充已完成或重复跑同一个 skip。

注意：此项 `CODEX_REQUIRED` 是将 WR-H12 所涉上游预算/日报桥接子门槛分配给本机 Codex，不代表 WR-H12 family 完整业务范围已覆盖；WR-H12 严格仍需用户许可。**当前所有50家族严格完成数仍0。**

## 1. 优先给 Codex 的可执行工作包

### WR-CODEX-01 / COORD-H03：Webhook HMAC 验收（本地已有源码，不许重建）
- 原始源码分支：`codex/relay-return-20261015`，**查当前 HEAD 后固定**；本次观察 SHA `27796df5f9847c1bb5d48d2a445e418dfb3d8e96`。
- 文件：`coordination/github_webhook.py`、`tests/test_github_webhook.py`（六条测试：有效签名、篡改、无签名、空 secret、非 PR 事件、未知 action）。
- 从该分支独立 worktree 执行 `python -m unittest discover -s tests -p 'test_github_webhook.py' -v`，记录命令、Python/OS、exit、数量、完整 source SHA；核对 signed bytes、HMAC 和项目身份拒绝规则。云端 Actions 目前 **没有** 映射此 family。
- 后续把真实通过的测试映射到适当独立 checkout 的 Actions 校验，不要误将 WoolRadar 业务源码分支上的“不存在文件”当作零测试通过。

### WR-CODEX-02 / COORD-H04：dry-run 绝不写盘
- 相同协调源码分支，文件 `coordination/dispatcher.py`、`tests/test_dispatcher.py`。
- 精确命令：`python -m unittest discover -s tests -p 'test_dispatcher.py' -v`；特别复核 `test_dry_run_does_not_persist`、`test_dry_run_on_missing_db_has_no_filesystem_side_effects`、`test_dry_run_on_existing_db_reads_state_without_writing`。
- 在**隔离的临时路径**比较运行前后 DB 文件、WAL/SHM、配置和状态分支是否变化；记录差异和复现输入，绝不能对真实生产 SQLite 进行试写。

### WR-CODEX-03 / COORD-H05/H06：V3/V5 relay 重放、取消/租约、真实 Git return-sync
- 相同分支已有 `tests/test_relay.py`、`tests/test_relay_faults.py`、`tests/test_relay_git.py`、`tests/test_return_sync.py` 与 `coordination/relay.py`、`coordination/relay_git.py`。
- 隔离 worktree 中分别运行：
  `python -m unittest discover -s tests -p 'test_relay.py' -v`
  `python -m unittest discover -s tests -p 'test_relay_faults.py' -v`
  `python -m unittest discover -s tests -p 'test_relay_git.py' -v`
  `python -m unittest discover -s tests -p 'test_return_sync.py' -v`。
- 特别检查老 owner fencing、重复 event 幂等、网络/429/5xx 重试上限、进程强制退出后的冷恢复、同一 key 不同 payload 拒绝、过期 lease 与真 Git 竞争/CAS。离线测试与真实 Git 服务拒绝分类必须区分。**不得在未经所有权 claim 和 lease 检查时更新 V3 真实状态**。
- 每个 family 分别给出 test pass/total、exit、SHA、证据链接、未通过的子门槛；不要把四份测试简单相加当独立业务完成数。

### WR-CODEX-04：必须本地/人工提供的原生与业务门槛
- WR-H01～H11、H15～H19 等已通过的云端子集仍需按照原家族的冻结数据/原生验收命令验证；优先从主清单中 `missing_native_receipt`、`partial_linux_reconstruction` 查找真实冻结命令。
- 只对**脱敏副本**执行回滚、WAL、通知状态及真实日报桥接验证；采集必要的哈希、统计分母和脱敏日志，不上传生产数据库、账户、Cookie、原始聊天或敏感历史测试数据。
- WR-H12 用户批准、H13 新独立金标、H17 维护者批准、COORD-H07 review-only、WR-H14 旧 Scheduled 阻塞：保留外部门槛，Codex 不能擅自标 COMPLETED 或代替用户批准。

## 2. GitHub 协作和 Codex 执行约束

1. 先 `git status --porcelain=v1`、`git remote -v`、`git rev-parse HEAD`，保护正在进行的 worktree；与 [WoolRadar Issue #2](https://github.com/lu403369069lu-prog/WoolRadar/issues/2) 和 [总协调 Issue #3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3) 最新回执去重。
2. 遵守 `codex/relay-state-v3` 的实际 owner/lease/fence/CAS，**Issue 评论和此文件不是领取锁**。先查是否有别的 Agent/Codex 已持有同一任务；冲突时切换另一 family。
3. 只在独立安全分支/Draft PR 落地补丁，保留历史和真实 SHA，不自动合并、不强推、不部署、不修改生产环境。
4. 完成一项立刻继续下一项未完成 family；失败保存严格失败证据并切到其他可执行任务。所有云端已完成工作先读取，不重复初始化；不能触发收费 AI API 或绕过限额/平台审批。
5. 将实做变更、真实运行命令、exit、分母、日志/原始 SHA、剩余本地门槛按家族回写 WoolRadar #2；跨仓依赖索引写总协调 #3。最后在本文件或 HANDOFF.md 保留最新接力状态。

## 3. 交接边界

- 云端 ChatGPT 已完成：Actions 默认分支部署、机器断点/故障优先回执、Windows 云端原仓359/359测试、冻结输入缺口调查。
- 分配给 Codex：上述现存协调源码的补验与适当 CI 接入、只有 Windows/生产**脱敏**副本才能取到的真实验收证据、SAM 本地冻结发布资产回源核验（见 YinQieJi 专属交接）。
- 原始 GitHub 代码/日志的变动不能自动唤醒本地 Codex；Codex 启动后须主动从本文件读取。**50项严格验收完成数仍为0，未分配 owner 不等于已完成。**

事件键：`codex-handoff/20261018/WR-COORD-3-WINDOWS-RETURNS`
