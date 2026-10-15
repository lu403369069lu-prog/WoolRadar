# V5 接力候选验收报告

日期：2026-10-15。结论：安全开发与隔离验证阶段已交付；V5 总目标部分通过。
自动 AI 执行未打通，未部署，不能宣称 Codex ↔ ChatGPT 真实完整接力已实现。

## 身份与环境

- Windows；Python 3.12.14；Git 2.53.0.windows.3；Codex CLI 0.147.0。
- 已测试代码：`19826b6af9e77f650ed05e7c133dd3184f114de3`，分支 `codex/relay-v5-20261015`。
- [草稿 PR #9](https://github.com/lu403369069lu-prog/WoolRadar/pull/9) 以 #6 为基线，包含 #7/#8 一次，未合并原 PR。
- 状态分支 `codex/relay-state-v3`，已回读检查点 `9b565b7959cc64bbdd43d0f45f7c15569e556581`，revision 6。
- 本报告及交付核验属于上述代码提交之后的文档提交；测试结论固定绑定代码 SHA。
- 候选位于从 GitHub 精确文件生成的隔离快照，并非已关联的本地 Git worktree。生产目录未作为测试工作区。

## 实测结果

`python -m unittest discover -s tests -v`：退出码 0，50/50 通过，失败 0。
本地 Git 并发测试实际创建隔离 bare 仓库、提交并触发非快进拒绝；受 Windows 沙箱限制，
这些纯本地测试以经审批的沙箱外命令运行。未访问生产数据库或设备。

`python -m coordination.acceptance --output coordination/evidence/five-rounds.json`：退出码 0。

| 轮次 | 子测试数 | 退出码 | 可支持的结论 |
|---|---:|---:|---|
| 正常协作 | 1 | 0 | 状态转换通过；真实 ChatGPT 独立读取仍未验，部分通过 |
| 额度中断 | 2 | 0 | 模型不可用注入、真实子进程退出与冷读取通过 |
| 并发冲突 | 2 | 0 | 合成任务的真实本地 Git 冲突及旧 owner 拒绝通过 |
| 故障恢复 | 9 | 0 | 网络/403/429/503 注入、重复/损坏/顺序与 SQLite 错误回归通过 |
| 完整闭环 | 1 | 0 | 普通 Python 模拟另一执行者；并非真实 ChatGPT，部分通过 |

五轮子测试与全套有重叠，不相加作为独立用例数。证据见 `evidence/relay-unit-tests.json`、
`relay-unit-tests.log` 和 `five-rounds.json`。
一次第三轮本地 push 返回未分类 `REMOTE_0`；带 stderr 诊断单独重跑通过，随后五轮通过，
根因未确定，保留 `iteration-history.json`，不宣称已修复该偶发环境问题。

独立复审发现的队列乱序/阻断、非法状态替换、Windows 路径别名、过期租约发布等已修复，
有先失败再通过的回归。最后复审未报告新的可复现问题；这不替代生产长稳验收。
远端 19 个文件与本地 Git blob 完全一致，见 `evidence/delivery-verification.json`。

GitHub 合成并发分支保留首个提交 `6971a4f07cb7abbb5ebce3a773b8df2162bb4ab9`；
第二个过期预期写入返回 UNKNOWN GraphQL 错误，回读确认未覆盖，但错误不足以证明具体拒绝原因。
因此线上 CAS 错误分类仅部分验证，见 `evidence/github-cas.json`。

## 十四项交付对账

| 要求 | 交付与边界 |
|---|---|
| 1 协议与职责 | PROTOCOL_V3.md，兼容保留 V2，Issue 职责固定 |
| 2 Schema | task-state.schema.json 与 relay.py 结构/语义验证器 |
| 3 双向同步 | relay_git.py 的 read/deliver/enqueue/sync；GitHub MCP 实际提交、回读验证 |
| 4 幂等与并发 | 事件键/版本/owner/租约/fence/文件范围，真实本地非快进冲突通过 |
| 5 持久恢复 | 校验和、原子替换、历史版本、远端 Git 历史和持久 outbox |
| 6 错误重试 | 状态分类、指数退避/次数上限/Retry-After 注入通过；Git stderr 无完整 API headers |
| 7 额度处理 | quota.py 分级策略、quota_pause/无模型冷恢复；未挂接真实无人值守执行器 |
| 8 只读工作流 | 继承扩展 offline-dispatcher-selftest.yml，手动、contents:read、无保留凭据；未在线运行 |
| 9 五轮脚本证据 | acceptance.py 与真实运行记录；第一/五轮明确部分通过 |
| 10 两项目示例 | relay-examples.json 与远端 SAM/WoolRadar 审查任务；无业务完成声称 |
| 11 故障恢复说明 | PROTOCOL_V3.md 的 Run and recover 与 HANDOFF.md |
| 12 独立分支/草稿PR | PR #9；状态分支独立；没有 main/生产合并 |
| 13 三 Issue 记录 | SAM #1、WoolRadar #2/#3 追加带事件键的交付记录，保留原正文 |
| 14 最终验收报告 | 本文件；区分代码提交、测试通过、真实 AI 执行、部署 |

## 环境盘点与未打通项

两个私有仓库的 GitHub connector 读写成功。gh 未登录；不能将 connector 的认证当独立 Git CLI 的认证。
本地 WoolRadar 为非 Git 生产目录；SAM 原 checkout 状态无修改，其他 worktree 保留，未转移业务 owner。
只读核对了现有计划任务、进程名称及相关服务状态，未启停。进程名和聊天 idle 不能证明其他执行者已释放文件。
Actions 运行列表为空；权限/工作流设置端点被 connector URL 策略拒绝，启用状态、私有额度和权限设置仍未知。

官方额度工具可读账户窗口，本轮初始快照剩余 98%/37%；不是未来或当前实时保证。
CLI 帮助确认 codex exec 存在，login status 显示 ChatGPT，但所选 provider 为 custom，计费路径未确认，
因此没有启动最小模型实验、切换 provider 或调用收费 API。[官方非交互文档](https://learn.chatgpt.com/docs/non-interactive-mode)。

原 ChatGPT 协调聊天保留，已收到一次明确派单；多次读取只有用户消息和 idle，未出现接管回执、新提交或新草稿 PR。
历史聊天中的旧测试与补丁线索不算本轮执行产物。当前 agent 自己提交的 SHA 不冒充 ChatGPT 新成果。
没有部署定时执行器、服务或长期 automation；普通 Python 同步代码不会生成 AI 代码。
同步程序本地端到端通过，GitHub 发布由受信 MCP 执行；独立 Git 认证与无人值守网络长稳尚未验证。

## 下一步与审批边界

1. 有真实、获授权的独立执行后端后，读取远端最新 state/PR SHA，再领取 `RELAY-V5-REVIEW-2` 或 `RELAY-SAM-REVIEW-2`。
2. 在各自允许的审查目录生成实际命令、退出码、精确 SHA 的证据并建立独立草稿 PR；再由 Codex 冷读新 SHA 隔离复核。
3. 确认 CLI 计费路径与独立 Git 认证后，才进行最小真实执行实验。权限、部署、长期调度须单独审批。
4. SAM 的历史 8 项失败、R5 4/6、拒答 34/40 和 WoolRadar #4/#5 留出集仍是原业务待办，本轮未重测或宣称修复。

不需要用户复制交接原文：GitHub 已保存明确任务、代码与证据。但在没有真实执行后端时，
不能保证 Codex 额度耗尽后自动产生新的 AI 工作成果。整个 V5 仍有上述真实接力验收与部署待办。
