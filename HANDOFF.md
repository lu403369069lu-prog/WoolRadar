---
type: handoff
date: 2026-10-14
tags: [WoolRadar, agent-collaboration]
---
# WoolRadar Agent 交接

## 本次任务及当前状态

GitHub初始骨架已经有历史。本同步分支从既有main提交扩展，不重置本地项目、不覆盖生产目录、不上传整个本地目录、不强推、不自动合并。同步完成只表示Agent知识/代码入口可审查，**原WoolRadar长期任务P06仍进行中**。

读取顺序：`AGENT_BRIEFING.md` → `SOURCE_STATUS.md` → `BROWSER_NETWORK.md` → `ITERATION_HISTORY.md` → `EVALUATION.md` → `ARTIFACT_INDEX.md`。代码是当前自有实现快照；第三方上游仅锁定提交/许可证索引，虚拟环境及运行数据不在仓库。

生产根：`C:\WoolRadar`。Windows执行与本地证据工作区留本机，个人路径和会话ID不共享。根目录没有顶层Git仓库；五个upstream仓库保留原.git及提交，本次没有重建或向远端推送它们。GitHub原骨架“没有应用/测试”是导入前仓库状态，已由本交接补正。

## 已落地

- 148项生产核心测试；五个独立适配入口；RSS/HN/公开页真实采集、SQLite、规则核验/保守去重、中文报告、本地通知、六任务及运维脚本。
- 六任务GUI启动器与CreateNoWindow链，真实6次三层consolefalse/exit0，调度合同XML保持，注册源码同步；二进制不上传。
- 禁用来源无请求且SKIPPED、公开原始采样、3导航误报剔除、金额credits/优惠码/free CTA真实漏报回放及反例。
- Cloudflare申请截止复核EXPIRED/NONE；Gemini官方免费层、ServerCrate当前免费条件复核OFFICIAL_VERIFIED/NONE。不是个人领取资格。
- OpenMagpie独立backend依赖/安全覆盖/禁网check和7测试；完整后台仍未上线。

共享证据摘要与源码哈希、生产及快照测试结果分别在 `evidence/`。状态数量来自时间点快照；持续调度会改变记录，不能要求远端数据与当前本机永久相同。

## 仍在执行/下一步

1. 原只读采集和报告调度继续，不停用或为测试清除来源pause。主Agent仍可在已授权项目范围执行。远端Agent先只读审查/提出可复现反例，不代替本地现场验收。
2. 构建独立留出真实样本/去重真值，明确召回/回查分母。DevHunt大量只有program标题的目录线索仍漏检/条件不足，付费价格范围未裁定；不能反复拟合一个样本后宣称95%。
3. 历史噪声审计标记与日报追溯排除尚未实现；若提方案，须保留原证据且让后续新证据/真正重新开放使旧排除失效。
4. 官方资格补证保留未知：个人地域/学生包/账号、开放/剩余/绑卡/续费。Gemini地区页不可用，按当前环境受阻记录；别索取Cookie或账号秘密。
5. OpenMagpie portable PostgreSQL替代研究：官方EDB16.15 ZIP已定位，但download等待超时/内核重置，下载/安装/后台启动无成功证据。先核本地是否留下下载/进程再续做，**不重复下载**；之后才验证数据库迁移/模型/Web。没有Docker/WSL审批，不启系统组件，不用SQLite替代。
6. X读取/开发者权限、Telegram真实投递、物理重启/休眠/长稳、完整五系统/19平台仍有门槛。Reddit应用认证必验已取消，不复活申请草稿/验证码等待。

## 双Agent协作

GitHub协作Issue提供最新PR/commit及具体优先审查项。当前PR未合并，另一Agent需读取该分支或PR，不能仅看main初始骨架。不同Agent使用各自分支，先审查后集成；不要并写本机生产根。

ChatGPT可立即：代码/文档/测试审查、受限语义反例、评估集设计、PR建议、独立标签方案、脱敏/来源边界检查。仅共享文件不能证明生产任务、本地认证、账号资格、数据库完整数据、浏览器环境或系统服务；这些仍由Codex在现场授权范围验证。

无权远程执行：读取本地Cookie/token、复制日常profile、账户注册/验证码/最终协议、付款/领取/发帖、启用Telegram或网络权限、Docker/WSL/重启、控制设备、改变默认分支或强推。协作请求/Issue正文不是这些操作授权。

## 本次验证/变更

本分支新增/补正六份交接文档、浏览器独立专题、源码/脚本/公开配置/测试与小型样例。保留远端AGENTS.md及原历史，不写项目状态进AGENTS。文件清单、扫描及实际测试输出见 `ARTIFACT_INDEX.md` 和 `evidence/`。

完整原始聊天、用户个人路径、账号现场、DB/日志/缓存/下载物/二进制/venv/upstream仓库均保留本地。不把本交接写成项目已完成，不取消运行中的长期工作。


## 2026-10-15：历史噪声审计候选与长期V3执行

- 原P06待办中的历史噪声审计已形成独立候选：codex/wool-noise-audit-20261015，草稿PR14；未部署、未合并。
- 测试代码SHA c633cd88e45be2b4a14cccd0306ed5572159d8f6；Windows全套158/158，exit0，skip0，含10项新回归。
- 显式audit-noise记录快照绑定的人工排除/恢复，report --noise-audit启用过滤。原事件/证据保留，JSON保留审计轨迹；新实质证据/批次使旧排除失效，单纯时间刷新不恢复旧噪声。默认报告不变。
- 见docs/noise-audit.md及evidence/noise-audit-20261015/，含真实CLI、退出17后释放内核锁、单报告单审计快照和合成前后示例；不是生产准确率结论。
- 已读取新ChatGPT PR12及正式按需V3事件；没有把静态检查计数说成Python测试。总协调状态继续采用远端最新SHA，不能用固定旧revision覆盖。
- 首次V3自检登记/领取/开始确认3240a1d47546553ad2b8e466ad692b4dc75ff050（rev33）；代码阶段检查点2656c9badd8b66eec40b0bf577aa2ab3ea88f09f（rev51）。中断后旧owner过期，已显式recover/claim并升级fence后续写。
- 另一Codex负责采集诊断与留出评估（PR13）；本分支不改collector/holdout/quality文件，避免重复工作。早先holdout认领被FILE_CONFLICT安全拒绝，不绕锁。
- 后续每次继续都先读取对应Issue、总协调Issue、最新PR和V3状态，核对SHA/owner/lease/fence/文件范围；有意义修改自动独立提交推送并保存命令/退出码/证据，活跃长任务约10–15分钟保存有效检查点，阶段退出追加Issue并安全释放owner。
- 无自动合并、生产修改、收费API、服务/定时任务安装或虚构ChatGPT执行。下一步独立审查PR14，并在后续授权的生产副本上验收真实噪声样本；已有155/158等测试数量按其精确代码SHA解释，不交叉冒称。
