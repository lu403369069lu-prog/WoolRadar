# SAM × WoolRadar · V5 纯 Chat 执行规则（可恢复摘要 / 非 V5 原文）

> **性质**：根据用户在项目对话中的明确指令、已有 V5 交接记录及 GitHub 总协调 Issue #3 形成的**派生执行清单**。这不是 V5 原文的逐字镜像，不取代用户最终版 V5，不构成新 V6/V7 授权，不可据此重建工程或变更既有安全边界。供同项目的新对话**被用户启动之后**冷读；存放在 GitHub 不等于 ChatGPT 自动加载项目设置或能够唤醒对话。
>
> **原文权威位置**（用户此前提供）：Windows `C:\Users\lh\Documents\ChatGPT\总协调\SAM-WoolRadar-V5.md`；历史核验记录曾报告 SHA-256 `0387361EC8B33022AF9637469B6DD55921415F15AB9F39B462090536B76BB764`。**本次 GitHub 维护窗口未能读取 Windows 原始文件字节，因此该 SHA 仅为既有记录，不冒称本轮重新核验。** 有本地访问能力时必须比对原文、归档/附件版本和此摘要；冲突以用户较新明确要求和 V5 原文为准，未经核对不得假称“逐字忠实恢复”。

## 0. 当前操作范围 / 暂停边界

- 用户已明确“先别干”，暂停 SAM / YinQieJi 业务审核。本次用户**只授权**读取 V5 要求、整理规则、更新 GitHub 持久化指令文件、提交并验证。**本文件的写入不能解释为恢复业务代码开发、运行产品测试或抢占工程任务。**
- 未来须在用户明确恢复相应工作后才继续业务审核；单纯读取本文件、新建对话、收到 Issue 评论/PR/检查点均**不是授权启动**。
- 本文件不修改 ChatGPT「项目指令」设置；普通 Chat 一次回复结束后无法自己无限运行。不得声称持续后台干活或要求用户反复解释既已授权的规则。

## 1. 不可违反的硬约束

1. **纯 Chat、严禁定时任务**：不得创建、启用、重启或用任何自动化/cron、Scheduled、轮询机器人、后台守护服务、Windows 任务计划、GitHub Actions 定时调度、系统启动项等替代当前聊天执行。不得未经授权部署后台接力。已有历史调度记录不等于用户现在批准，不能擅自操作。
2. **禁止危险写入**：不得自动合并 PR、强制推送或重写他人历史、部署/发布、碰 Windows 生产目录与任务、PLC/TwinCAT/真实运动与 I/O、生产 SQLite/日志/缓存、真实通知/领取活动、修改系统或模型/桥接/全局配置。不得调用未经许可的收费 API。
3. **隐私与来源**：不得读取/上传未获授权的私人历史、账户令牌、Cookie、凭据、真实日报、原始数据库、厂商受限手册或其他受保护源；GitHub 仅存经审查的必要脱敏摘要/代码与验证指纹。
4. **权限与协作**：先读取共享 V3 状态，再核对 `owner/lease/version/fencing_token` 和当前 Git HEAD；无权不得 claim、续租或 CAS 更新 `state.json`。其他执行者工作树/分支只读；可在明确权限内从固定 SHA 建立**独立隔离分支 + Draft PR**，不篡改负责人分支。GitHub 走已连接且被授权的 MCP/API，不绕过安全阻断。
5. **诚实验证**：不能以模拟、静态扫描、摘录函数、局部测试、PR 数量、Issue 评论、0 步失败的 CI、`skip`、不完整 Gold 或无独立接收端回执冒充正式全量/原生/业务验收；必须明确 `PASS/FAIL/SKIP/NOT_RUN/ENV_BLOCKED/EXTERNAL_BLOCKED`。
6. **停止与暂停**：遵守用户直接的“暂停/先别干”；未经其恢复不得用“持续执行”条款反向授权。恢复后在**当前有效工具调用/回复窗口内**尽可能连续处理可执行事项；阶段汇报、一个 PR/测试结束**不是整体验收终点**。不能跨回复承诺无人值守执行。

## 2. 权威项目与恢复入口

| 项目 | GitHub 权威入口 | 边界 |
| --- | --- | --- |
| 总协调 / V5 / V3 | [WoolRadar Issue #3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3) | 唯一跨项目总索引；不是锁或自动唤醒 |
| SAM / YinQieJi | [YinQieJi Issue #1](https://github.com/lu403369069lu-prog/YinQieJi/issues/1) | SAM 实际代码、Skill、产品审核证据 |
| WoolRadar | [WoolRadar Issue #2](https://github.com/lu403369069lu-prog/WoolRadar/issues/2) | 采集、准确率、日报、W1–W7/P06 证据 |
| RealProjectFeedBack / PLC | 原仓/原 Issue（执行时核验） | 独立技术审核；静态分析不能替代 TwinCAT 真机/编译 |

- 共享状态唯一权威：`lu403369069lu-prog/WoolRadar` 分支 `codex/relay-state-v3` 的 `state.json`。读取后确认顶层 schema/payload、revision、任务身份、租约与 CAS 最新 blob；**本文件不修改共享状态**。
- 可参考两仓 `CODEX_NEXT_TASKS_20261018.md`、`HANDOFF.md`、各 Draft PR 及 Issue 最新独立回执。各类旧评论、V6/V7 式纠偏总结是历史证据，不能自动覆盖最终 V5 或最新用户禁令。
- 新对话若需接续：先冷读本文件、Issue #3 / SAM #1 / Wool #2、最新 PR HEAD 和 V3 state，再用所能访问的完整 V5 原文校验；若本地原文不可访问，标注限制，**不要索要用户重复已记录的规则**。

## 3. 业务优先级与四大类闭环

- **SAM 优先**：在 SAM 存在可独立执行的工作时先核对 SAM；只有 SAM 可执行审核已处理完，或经明确核验确实受阻、需要切换时，才处理 WoolRadar。协调与 RealProjectFeedBack 保留各自待办/owner，避免跨仓抢工。若用户给出新的明确优先级，以用户新要求为准。
- 原 V5 “四大类 / 四本账”的**确切划分与验收条款由原文、原始父任务和 GitHub 任务账本决定**，不可用这里的简写重新规划，也不可把“4项小步骤”当“四大类”。执行账至少覆盖：①全量 PR/技能/需求审核；②真实缺陷复现与修复；③正式测试、跨 PR/平台集成与 V3 协作；④产品业务 Gold / 实际来源 / 发布恢复 / 独立终验。领域归属涉及 SAM、WoolRadar、总协调和 RealProjectFeedBack，分别存放记录，统一按 canonical task 去重。
- 已登记的原始约束和分母**不能因做摘要而删除**：历史 50 家族（42 可执行族 / 39 去重正式命令，8 外部门槛）、118 原始追踪行、20 条上下文依赖、12 条混合项目（旧记录也称“32 混合/上下文”，须逐行对账、不得重复计数）、37 父级业务身份及验收链、SAM 技能权威清单、61 正例 / 19 负例 / 522 来源、WoolRadar P06 + W1–W7、原产品五系统/跨端和最后 3 轮终验。上述是**历史待核证范围，不是完成比例或即时分母**；随执行时权威账本锁定。
- 旧“5小时额度剩余25%就停并上传”等触发条件已被用户撤销，不能再据此中断。不能擅自恢复 Schedule 作为补偿。

## 4. 当前交互内的执行循环（收到有效恢复授权后）

1. **READ**：实际读取完整既有交接、最新 GitHub Issue/PR、固定 HEAD/base、源 blob、脏树、V3 owner/lease/fence；不可访问则明确 `ENV_UNAVAILABLE` 而非宣称已读取。
2. **DEDUP + PICK**：按原父任务 ID、来源、根因、PR 依赖去重；优先 P0 安全/数据/错误 PASS，再已有 RED 与 P1，继之正式矩阵和业务 Gold。防止为同问题重复开 PR 或重复统计。
3. **REPRODUCE → FIX → RETEST**：真实原版本最小反例 RED、最小源码修复、GREEN；运行同 SHA 正式测试、完整模块/整仓、Windows/Linux/Node24/26 可运行矩阵、独立交叉审查。若仅隔离摘要/类型替身/静态编译，要直接写明不代表全量。
4. **GATE**：CI 0 step / 无 runner / 404 日志标 `RUNNER_STARTUP_UNVERIFIED`、根因未知；skip 不算 PASS；业务 Gold、盲评、09:30 实际接收、PLC 编译/设备结果和发布/回滚必须有独立真实回执。
5. **PERSIST + NEXT**：确切 branch/head/base/blob、执行环境、命令、exit code、run/pass/fail/skip、日志哈希、证据边界、未测/阻塞原因、下一动作写对应 Issue 和可回读 Git 文件。确认提交与 readback 后，当前窗口中若仍有可执行未完成项就继续下一项。客观阻碍记录后切到下一可做项；**不以一次提交或阶段汇报结束项目**。
6. **EXIT**：只有全部原验收项均具可复核业务证据才能标 `BUSINESS_ACCEPTED`；任何未解决外部依赖必须逐项保留 `EXTERNAL_BLOCKED / NOT_ACCEPTED`，不能把“已有交接文档”算完成。实际会话/宿主工具窗口结束时只报告真实断点，不声称在后台运行。

## 5. 每条证据的最低结构

`canonical_task_id | source_requirement | repo | owner/lease/fence | fixed_base_sha | candidate_head_sha | changed_blob_sha | red_case | patch | exact_test_command | OS/runtime/deps | exit_code | run/pass/fail/skip | log_sha256 | full_native_matrix | independent_gold | acceptance_status | blockers/unlock | next_action`

修复前后必须保留历史失败，源 HEAD 变化时相关通过记录必须 `REVALIDATION_REQUIRED`；同一原始需求、多个 PR 不得重复计入完成率。GitHub 写入必须 CAS/最新内容核对，回读可验证。不得更改 `AGENTS.md` 作为项目进度日志；使用本协调文件或既有本地 `网页AI-任务台账.md` / handoff，并在 Issue 留索引。

## 6. 跨新对话说明（边界真实）

GitHub 存储**只是持久化来源**，本文件只在新对话**实际读取**后可用；不会自动变成 ChatGPT 项目设置，不会主动唤醒新对话，也不保证模型对所有指令零失误。可供项目指令配置引用，但本次未取得直接修改 ChatGPT 项目设置的接口。用户无需再次粘贴整段 V5；能够访问原文的执行端应自行读取、比对，并保留无法访问时的真实性边界。

## 7. 本文件本次验证范围

- 任务为**规则持久化**而非 SAM/WoolRadar 业务验收。当前创建独立 Draft PR、不改 main、不改 V3、不改任何生产源码与任务调度。
- 与本次整理直接关联的实证来源：WoolRadar [Issue #3](https://github.com/lu403369069lu-prog/WoolRadar/issues/3) 中的 `V5_EXECUTION_CONTRACT_20261024_NO_RETRIGGER` 记录、`CHAT_ONLY_V6_EXECUTION_CONTRACT_20261024` / V7 历史纠偏评论和原仓交接文档；以及用户在 Chat 中明确的“严禁定时任务 / 纯 Chat / SAM 优先 / 暂停 / 只更新指令文件”。
- 后续如果拿到 V5 原文并发现摘要缺失或冲突，应再建立新的隔离修订，记录逐条差异；**不悄悄更改用户原要求**。
