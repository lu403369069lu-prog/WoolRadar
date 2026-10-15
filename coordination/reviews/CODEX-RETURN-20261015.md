# Codex Windows 回接验收

2026-10-15。本轮复用 V3，没有重建协议或调度器。
结论：**真实按需 ChatGPT → GitHub → Codex 回接、独立 Git 同步及故障恢复已验证**。
正式 ChatGPT V3 claim 执行链与无人值守 AI 触发仍未验证；不据此宣称 V5 全部自动化。

## 精确来源与独立回接

- PR9 当前 head：`1440553f892676a938135e24938010d50cdd351a`；测试实现 `19826b6af9e77f650ed05e7c133dd3184f114de3`。
- PR10 当前 head：`e81afca6661918b6261297f4251f413dbee09dab`，包含另一新增提交 `9084368f66b93187b4c81203a986654fa878a4e5`。
- 原审查检查点：`9b565b7959cc64bbdd43d0f45f7c15569e556581`，v3/revision6。
- 已在 Windows 通过独立 Git 获取三分支，在新 bare 对象库建立真正 linked worktree；原生工作树工具因协调仓库缺少目标对象失败后采用此回退。
- Git 独立重算19/19 blob一致；PR9从实现到head只新增 ACCEPTANCE_REPORT.md、delivery-verification.json。
- PR10只新增 `RELAY-V5-REVIEW-2-advisory.md`。其承认未运行Python测试、未正式claim，与远端回执一致。
- 新提交不属于此前 Codex 提交链中的旧成果，日期和审查内容与[ChatGPT回执](https://github.com/lu403369069lu-prog/WoolRadar/issues/3#issuecomment-6182890233)一致。来源归因依据用户明确说明及新远端产物链；共享GitHub账号没有密码学模型签名，不能单靠author字段证明模型身份。
- 本轮写入新状态后，旧revision6只保留为历史审查快照；用于新写入必须重新读取，旧快照对领取已 STALE。

## 实跑与判定

| 验收项 | 结果 | 证据 |
|---|---|---|
| PR10独立Windows复核 | 完全通过，限定为按需审查回接 | return-verification.json、两项新提交及原回执 |
| PR9精确实现重测 | 50/50，exit0 | relay-pr9-exact-unit.txt |
| PR10精确head重测 | 50/50，exit0 | relay-pr10-exact-unit.txt |
| 既有五轮脚本 | 原PR9只复跑一次，exit0；原1/5轮仍partial | pr9-five-rounds.json；没有新增模拟闭环冒充进展 |
| 最小修复代码 | 57/57，exit0 | fixed-tests.json / fixed-tests.txt |
| 独立Git认证与状态发布 | 完全通过，现有认证、无秘密读取 | git-setup.json、live-initial.json、code-checkpoint.json |
| 崩溃/断网/额度不可用边界 | 完全通过，限定普通程序故障场景 | live-recovery.json：exit17、队列持久、断网后恢复、零重复、model_calls=0 |
| 自动发现真实ChatGPT新SHA | 完全通过，发现层 | observe读到PR10新ref，重复观察changes=[]；不代表启动AI |
| 两客户端真实GitHub并发 | 完全通过，单任务心跳争用 | live-concurrency.json：一胜一REMOTE_CONFLICT，未强推 |
| 正式ChatGPT V3执行链 | 未验证 | 原两项任务仍ready/owner=null，未代写ChatGPT事件 |
| 无人值守AI触发/长期部署 | 阻塞：无已验证授权后端；未部署 | 没有调用其他历史聊天、收费API或创建服务/定时任务 |

所有证据路径相对 `coordination/evidence/return-20261015/`。全套命令均为
`python -m unittest discover -s tests -v`；五轮为
`python -m coordination.acceptance --output <OUTPUT>`，次数与SHA见 baseline-results.json。
本轮最小修复代码 SHA：`a2a67761105d13f7b9f8063c2d1c1a68062f4803`。
其后文档提交仅添加回执、脱敏证据和运行说明；测试不冒称运行在未知未来SHA。

## 新发现与最小修复

1. **P1，真实断网误判403**：旧代码搜索stderr任意`403`，误命中仓库账号 `lu403...`，使连接错误成为permission_denied。先复现失败，再匹配明确HTTP状态语法；真实恢复流程通过。首次失败队列保留为first-offline-failure.json，未偷偷清零。
2. **P1，隔离目录**：普通仓库 `.git` 同样有HEAD/objects；新增Git实际bare检查与路径别名拒绝，实际临时普通仓库被拒，未产生FETCH_HEAD。
3. **P2，队列冲突**：预期ValueError曾逃逸，尝试计数不落盘。现在保存受控错误码和conflict/invalid_event，阻断后续，不无限重试。
4. **P2，输出租约已过期**：保留当前接收时钟验证，并拒绝将已经过期的输出claim/heartbeat发布。保持原EXPIRED_OWNER错误契约。
5. 明确401/BLOCKED_AUTH及ref锁竞争分类；新增一次性observe缓存，补齐普通程序发现新SHA入口。

独立子代理复审后无新增已复现P0/P1。没有重新修改 #7/#8；其在PR9的集成保留，SQLite损坏原异常及Windows dry-run回归仍通过。

## 真实检查点与安全限制

状态实际推进：revision6 → 9（登记/领取/开始，owner=codex-windows）→ 10（恢复心跳）→ 11（真实并发胜出）→ 12（代码检查点）。
确认SHA分别见 live-initial.json、live-recovery.json、live-concurrency.json、code-checkpoint.json；相邻有意义同步间隔约2–5分钟，早于10–15分钟上限。
代码完成确认：`8e2784a72130a8b027f3ec080ca53876d5ffcb2a`。阶段退出另存最终回执、证据及释放本轮owner。
初始三事件和后续事件都先保存持久队列，Git远端确认后落回执；不依赖额度耗尽后的模型总结。
额度不可用试验在一个独立普通Python进程内完成，允许的子命令只有Python/Git；AI进程与provider均未调用。
断网只通过子进程死回环proxy注入，不改用户系统网络。HTTP错误分类和认证失败使用明确stderr回归，不声称真的耗尽GitHub速率。

传输身份依赖现有Git认证及受信操作者；actor只是审计字符串，不能阻止已拥有仓库写权限的恶意操作者绕过客户端。
当前lease会拒绝时钟倒退/过期结果，但没有跨机器服务器时钟权威保证；发生显著偏差应停止写入并人工核对，不能自动抢占。
Git错误文本不提供完整API headers，因此不能保证原始Retry-After精确传递；401/403/429/5xx回归与真实非快进拒绝分别记录。
one-shot observe/sync可独立运行，但本轮没有安装永久轮询器。无后台执行后端时，不能保证Codex停止后持续产生AI成果。

## Issue与下一执行者

- 追加[总协调回执](https://github.com/lu403369069lu-prog/WoolRadar/issues/3#issuecomment-6183256854)与[WoolRadar结果](https://github.com/lu403369069lu-prog/WoolRadar/issues/2#issuecomment-6183261426)，未替换正文，避免整体正文更新竞态。
- 仅协调基础设施与Windows新证据；本轮没有SAM业务新测试，所以不更新SAM #1，也不改其正式审查任务。
- [独立草稿PR11](https://github.com/lu403369069lu-prog/WoolRadar/pull/11)待审查，不覆盖/合并PR9或PR10。
- 下一执行者从最新状态读取代码与owner，审查PR11；ChatGPT正式协议验收必须由其真实执行端按实际身份领取并产生证据。Codex不冒充其claim或心跳。
