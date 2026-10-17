# 历史 80% 批量处置与本地 Codex 验收清单（2026-10-17）

**此次会话目标与边界**：原始50个家族，80%=40个。该表把**全部50类**赋予单一处置责任与精确的输入/验收命令，其中 **42类有明确本地 Codex 执行入口（84%交接就绪）**、其余 **8类**需新的外部金标/审批/真实桥接或是受限定时能力。这里的「交接就绪」**不是工程测试通过、合并、业务验收或实际完成率**。上一轮只有49/50可访问证据位置，本轮不宣称已修复40项。

**源 SHA 固定**：WoolRadar只在自有Draft [PR39](https://github.com/lu403369069lu-prog/WoolRadar/pull/39) HEAD `80c5ea18769c1312e5be5fd99a39e4f3d498c64f` 执行；SAM只在自有Draft [PR15](https://github.com/lu403369069lu-prog/YinQieJi/pull/15) HEAD `82bf36efa90cced8dafb56502812eb49f40515f3` 执行；协调器独立 [PR11](https://github.com/lu403369069lu-prog/WoolRadar/pull/11) HEAD `27796df5f9847c1bb5d48d2a445e418dfb3d8e96` 验收。所有SHA为本轮冷读参考，如果HEAD变化，请 Codex 先 `git rev-parse HEAD` 重做diff/测试，绝不静默混合不同提交。Codex V3 main owner 仍由现有actor持有，禁止抢写、自动merge、push生产。

**4条工程小时任务已暂停**：00/10/30/40分各一条；不会再因为无法自动回写而持续堆新小时结果。每日09:30公开羊毛简报仍启用且不参与Github工程写入。

## 对Codex的一次性交付指令

1. 请先在新的、与生产环境隔离的仓库副本/临时Git worktree，分别检出上述准确head SHA。拒绝在`C:\WoolRadar`生产目录、真实PLC/TwinCAT、用户浏览器会话、凭据、SQLite原件上运行。无自动安装或付费GitHub Actions。
2. 先按批次执行下方同一项目的正式测试；同一套测试覆盖不同家族时**执行一次**、分别附证据，不可把计数累加为不同成果。Windows用已存在Python / Node24、Node26 + npm离线缓存。需联网安装依赖请事先检查并确保无费用/数据外传，不访问真实用户私有sources。
3. 对每一项输出 `family_id | source_head | command | exit_code | passed/failed/skipped | log_sha256 | actual_behavior | changed_file_sha | disposition`，区分 `PASS_EXACT_HEAD`, `FAIL_REPRODUCED`, `NOT_RUN_BLOCKED`, `EXTERNAL_GOLD_REQUIRED`, `SUPERSEDED`。
4. 分别追加结果至 **SAM Issue #1、Wool Issue #2、协调 Issue #3**；Codex可以提交独立修复Draft，不更改现有持锁V3 owner/fence、不自动合并。只有达到真业务门槛才允许标记项目完成。

## 五十个家族的独立处置（不隐藏阻碍）

| ID | 优先级 | 历史目标 | 批次 / 核对对象 | 处置 | Codex本地命令或严格阻碍 |
|---|---|---|---|---|---|
| WR-H01 | P0 | 通知 SENT 不回退 | W-DB · `tests/test_notifications.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_notifications.py -v |
| WR-H02 | P0 | reindex/upsert BEGIN IMMEDIATE | W-DB · `tests/test_reindex_upsert_serialization.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_reindex_upsert_serialization.py -v |
| WR-H03 | P1 | WAL备份和 CLAIMED 恢复 | W-DB · `tests/test_config_backup.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_config_backup.py -v |
| WR-H04 | P0 | 通知状态复用及碰撞 | W-DB · `tests/test_reindex_notification_collision.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_reindex_notification_collision.py -v |
| WR-H05 | P0 | 证据事务原子性 | W-DB · `tests/test_apply_evidence_transaction.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_apply_evidence_transaction.py -v |
| WR-H06 | P1 | 快照先后/同秒排序 | W-DATA · `tests/test_report_snapshot.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_report_snapshot.py -v |
| WR-H07 | P1 | 公开生产者URL身份 | W-DATA · `tests/test_public_corpus_identity.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_public_corpus_identity.py -v |
| WR-H08 | P1 | 采样器公开域名校验 | W-DATA · `independent-quality/public-corpus-blind-dedup-20261016/test_freeze_public_sample_dedup.py` | CODEX_RUN | python -B -m unittest discover -s independent-quality/public-corpus-blind-dedup-20261016 -p test_freeze_public_sample_dedup.py -v |
| WR-H09 | P1 | 严格 URL identity true 布尔值 | W-DATA · `independent-quality/public-corpus-blind-dedup-20261016/test_freeze_public_sample_dedup.py` | CODEX_RUN | python -B -m unittest discover -s independent-quality/public-corpus-blind-dedup-20261016 -p test_freeze_public_sample_dedup.py -v |
| WR-H10 | P1 | 发布时间明确时区UTC | W-DATA · `tests/test_public_corpus_timestamp.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_public_corpus_timestamp.py -v |
| WR-H11 | P1 | 资助收费否定语义 | W-GRANT · `tests/test_developer_grant_negations.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_developer_grant_negations.py -v |
| WR-H12 | P0 | 真实日报桥接必须获批 | W-EXTERNAL · `independent-quality/delivery-bridge-20261016/test_consume_preview.py` | USER_APPROVAL | USER_APPROVAL |
| WR-H13 | P0 | 新独立盲测召回25%及漏合并 | W-EXTERNAL · `evidence/pipeline-integration-20261016/oct17/evaluation.json` | FRESH_GOLD | FRESH_GOLD |
| WR-H14 | P1 | 定时任务不能GitHub写入 | W-EXTERNAL · `coordination/HISTORICAL_FIRST_RESUME_GATE.md` | SCHEDULED_BLOCKED | SCHEDULED_BLOCKED |
| WR-H15 | P0 | 日报白名单/官方开放门禁 | W-DATA · `independent-quality/delivery-bridge-20261016/test_delivery_boundaries.py` | CODEX_RUN | python -B -m unittest discover -s independent-quality/delivery-bridge-20261016 -p test_delivery_boundaries.py -v |
| WR-H16 | P1 | 资助跨项目拼接误判 | W-GRANT · `tests/test_developer_grant_project_scope.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_developer_grant_project_scope.py -v |
| WR-H17 | P0 | 敏感历史测试数据审查 | W-EXTERNAL · `N/A` | MAINTAINER_APPROVAL | MAINTAINER_APPROVAL |
| WR-H18 | P0 | 已发通知CAS不一致uncertain | W-DB · `tests/test_notify_reindex_transaction.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_notify_reindex_transaction.py -v |
| WR-H19 | P0 | 官网资格与溯源 | W-GRANT · `tests/test_official_trace.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_official_trace.py -v |
| SAM-H01 | P0 | 严格JSONL重复键 | S-AUDIT · `test/claim-audit-input-integrity.test.ts` | CODEX_RUN | node --import tsx --test test/claim-audit-input-integrity.test.ts |
| SAM-H02 | P0 | claimKind枚举回归 | S-AUDIT · `test/claim-audit-kind-integrity.test.ts` | CODEX_RUN | node --import tsx --test test/claim-audit-kind-integrity.test.ts |
| SAM-H03 | P0 | 审查字段类型伪造 | S-AUDIT · `test/claim-audit-field-types.test.ts` | CODEX_RUN | node --import tsx --test test/claim-audit-field-types.test.ts |
| SAM-H04 | P0 | 卡片SHA绑定/旧夹具 | S-CARDS · `test/reviewed-artifact-byte-binding.test.ts` | CODEX_RUN | node --import tsx --test test/reviewed-artifact-byte-binding.test.ts |
| SAM-H05 | P0 | 目录祖先授权 | S-AUDIT · `../independent-review/20261016/rooted-source-authorization.test.ts` | CODEX_RUN | node --import tsx --test ../independent-review/20261016/rooted-source-authorization.test.ts |
| SAM-H06 | P1 | glob与rg572矩阵 | S-AUDIT · `../independent-review/20261016/glob-ripgrep-572-matrix.test.ts` | CODEX_RUN | node --import tsx --test ../independent-review/20261016/glob-ripgrep-572-matrix.test.ts |
| SAM-H07 | P0 | FTS locator访问范围 | S-WB · `test/workbuddy-rawroot.test.ts` | CODEX_RUN | node --import tsx --test test/workbuddy-rawroot.test.ts |
| SAM-H08 | P0 | 61原题只有10来源绑定答案 | S-EXTERNAL · `test/evals/real-source-eval.mjs` | FRESH_GOLD | FRESH_GOLD |
| SAM-H09 | P1 | 冻结教师JSONL和评测分母 | S-EVAL · `../independent-review/20261016-0904-audit-coverage/positive_answer_gate.test.mjs` | CODEX_RUN | node --test ../independent-review/20261016-0904-audit-coverage/positive_answer_gate.test.mjs |
| SAM-H10 | P0 | canonical路径/符号链接竞态 | S-AUDIT · `test/canonical-fail-closed.test.ts` | CODEX_RUN | node --import tsx --test test/canonical-fail-closed.test.ts |
| SAM-H11 | P0 | T009原始真实source gold | S-EXTERNAL · `test/teacher-scenarios.test.ts` | HUMAN_SOURCE_REVIEW | HUMAN_SOURCE_REVIEW |
| SAM-H12 | P0 | 审查claim来源作用域 | S-AUDIT · `test/repository-qualified.test.ts` | CODEX_RUN | node --import tsx --test test/repository-qualified.test.ts |
| SAM-H13 | P0 | dist安装升级回滚 | S-RELEASE · `test/release-040.test.ts` | CODEX_RUN | node --import tsx --test test/release-040.test.ts |
| SAM-H14 | P1 | 同fold题号唯一性 | S-EVAL · `../independent-review/20261016-0904-audit-coverage/holdout_identity_check.test.mjs` | CODEX_RUN | node --test ../independent-review/20261016-0904-audit-coverage/holdout_identity_check.test.mjs |
| SAM-H15 | P0 | WorkBuddy显式过滤不回退 | S-WB · `test/workbuddy-filter-fallback.test.ts` | CODEX_RUN | node --import tsx --test test/workbuddy-filter-fallback.test.ts |
| SAM-H16 | P1 | 异步FTS结果顺序 | S-WB · `test/workbuddy-rank-order.test.ts` | CODEX_RUN | node --import tsx --test test/workbuddy-rank-order.test.ts |
| SAM-H17 | P0 | release manifest原子化和指针 | S-RELEASE · `test/release-040.test.ts` | CODEX_RUN | node --import tsx --test test/release-040.test.ts |
| SAM-H18 | P1 | Windows glob大小写语义 | S-AUDIT · `../independent-review/20261016/glob-case-parity.test.ts` | CODEX_RUN | node --import tsx --test ../independent-review/20261016/glob-case-parity.test.ts |
| SAM-H19 | P0 | 空摘录不可成为已核验来源 | S-WB · `test/workbuddy-nonempty-lines.test.ts` | CODEX_RUN | node --import tsx --test test/workbuddy-nonempty-lines.test.ts |
| SAM-H20 | P0 | 规范source版本要求 | S-WB · `test/source-qualified.test.ts` | CODEX_RUN | node --import tsx --test test/source-qualified.test.ts |
| SAM-H21 | P0 | excerpt文本与SHA一致 | S-WB · `test/workbuddy-excerpt-integrity.test.ts` | CODEX_RUN | node --import tsx --test test/workbuddy-excerpt-integrity.test.ts |
| SAM-H22 | P1 | 题目覆盖不能代替回答正确 | S-EVAL · `test/eval-input.test.ts` | CODEX_RUN | node --import tsx --test test/eval-input.test.ts |
| SAM-H23 | P1 | 评测ambiguous分母 | S-EVAL · `test/eval-input.test.ts` | CODEX_RUN | node --import tsx --test test/eval-input.test.ts |
| SAM-H24 | P0 | T031 Axis vs FSM错配 | S-EXTERNAL · `test/teacher-scenarios.test.ts` | HUMAN_SOURCE_REVIEW | HUMAN_SOURCE_REVIEW |
| COORD-H01 | P1 | 离线调度幂等 | C-CORE · `tests/test_dispatcher.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_dispatcher.py -v |
| COORD-H02 | P1 | GitHub事件来源适配 | C-CORE · `tests/test_github_event_adapter.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_github_event_adapter.py -v |
| COORD-H03 | P0 | Webhook HMAC有效性 | C-CORE · `tests/test_github_webhook.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_github_webhook.py -v |
| COORD-H04 | P0 | dry-run绝不写盘 | C-CORE · `tests/test_relay.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_relay.py -v |
| COORD-H05 | P1 | V3/V5 relay重放与取消 | C-CORE · `tests/test_relay_faults.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_relay_faults.py -v |
| COORD-H06 | P0 | return-sync 真Git接力 | C-CORE · `tests/test_return_sync.py` | CODEX_RUN | python -B -m unittest discover -s tests -p test_return_sync.py -v |
| COORD-H07 | P1 | 架构文档/生产代理协同 | C-EXTERNAL · `coordination/PROTOCOL_V3.md` | REVIEW_ONLY | REVIEW_ONLY |

## 相同批次的退出准则
- **W-DB**：必须在临时目录/内存SQLite执行；SENT/CLAIMED不得回退，出错不重复发送；记录schema前后状态
- **W-DATA**：真实producer与采样器共同回归；URL身份不丢、隐私字段不导出、同秒逆序不抢占
- **W-GRANT**：只作候选，不用合成通过代替官方福利可申领；明确paid/closed/region
- **W-EXTERNAL**：必须提供新的独立公开样本或用户批准的本地脱敏日报；不能模拟为真实运行
- **S-AUDIT**：严格来源授权、拒绝伪造 JSONL、无越权read，Windows专测 rg大小写
- **S-CARDS**：npm ci在隔离副本；不得读生产cards；新版完整cards+zod运行与历史fixture SHA准确性
- **S-WB**：真实 direct/stdio MCP，拒绝未注册来源/空片段/不合filters上下文
- **S-EVAL**：只验证评测框架，原61/522 source truth 不随合成绿自动提高
- **S-RELEASE**：仅隔离模拟dist/upgrade/rollback和中断复原；禁止生产指针切换
- **S-EXTERNAL**：需要独立source gold与维护者审定；不得推断真实题目答案
- **C-CORE**：离线无网络fixture，重放与幂等；不得给定时Scheduled写库做越权桥
- **C-EXTERNAL**：最终人审，当前只有历史draft文档不能证明运行中代理状态

## 红灯阈值不可变

- WoolRadar：**真实首次独立47条/4正例 TP1 FN3 → 召回25%**，另有1个跨URL同活动false split；旧窗口再训练后TP4不能替代新未见窗口盲测。实际09:30脱敏签名消费仍 `OUTPUT_NOT_CONNECTED`。
- SAM：**61正例10个来源绑定答、51拒；19负例全拒**；522独立来源gold、T031 Axis/FSM证据和T009仍未独立通过；PR15隔离源码39/39与PR9 44/44并非真实业务gold。
- 协调器：PR11旧Windows**57/57历史回执**与最新源blob一致，但**不是本轮新执行，也不证明Scheduled GitHub写入**；暂停的Scheduled不得作为提交路径。
- WR-H17敏感历史保留原样，只在维护者明确批准后进行最小范围检查；不复制金融账号/地址/凭据/私人文本至GitHub。

## 结论

**50/50有独立处置，42/50具有Codex具体执行入口，本次交接覆盖>=80%。但实际工程完成率尚未证实达到80%，故 `historical_recovery_closed=false`，所有PR为Draft未合并。**

## 2026-10-17 执行命令安全校验补记
- 针对全50行（其中42条CODEX_RUN）的表格做了精确 `-s/-p` 与声明相对路径静态一致性核对，发现并修正唯一不一致 **WR-H15**：之前误把`test_delivery_boundaries.py`指向公共采样器目录，该命令可能 `Ran 0 tests` 但退出0，属假绿风险。
- `coordination/HISTORICAL_CODEX_BATCH_RUNNER_20261017.py` 新增对零测试、无法识别测试摘要的拒绝：`S-BUILD`属于纯编译不要求测试数，其余batch即使子进程exit0但无至少1项实际测试且没有成功摘要，判`exit_code=126`，不能计PASS；解析Python和Node的pass/fail/skip。详见同分支隔离回归测试。
- 这是**执行交接可靠性修复**，不代表42项真的在Windows跑过，更不代表真实羊毛source/gold合格。


## Codex真实回执校验与禁止误报

**在本地独立位置下载脚本**（不能放进被检出的仓库，否则`git status --porcelain`将判为脏仓）：[批量运行器](HISTORICAL_CODEX_BATCH_RUNNER_20261017.py) 和 [回执验收器](HISTORICAL_CODEX_RECEIPT_GUARD_20261017.py)。运行器默认只是列出计划，只有显式 `--run` 才执行离线测试，绝不安装、合并或push。先确认所用分支的实际`git rev-parse HEAD`与下面的命令固定SHA一致：

```powershell
# 例子：临时干净副本，绝不在 C:\WoolRadar 生产目录运行
python -B .\HISTORICAL_CODEX_BATCH_RUNNER_20261017.py --project wool --repo C:\temp\wool-history-qa --expected-head 80c5ea18769c1312e5be5fd99a39e4f3d498c64f --run
python -B .\HISTORICAL_CODEX_BATCH_RUNNER_20261017.py --project sam --repo C:\temp\sam-history-qa --expected-head 82bf36efa90cced8dafb56502812eb49f40515f3 --run
python -B .\HISTORICAL_CODEX_BATCH_RUNNER_20261017.py --project coord --repo C:\temp\coord-history-qa --expected-head 27796df5f9847c1bb5d48d2a445e418dfb3d8e96 --run

# 各批执行器分别生成一份本地 receipt.json，验收而不声称业务发布
python -B .\HISTORICAL_CODEX_RECEIPT_GUARD_20261017.py --receipt C:\temp\history-codex-wool-XXXX\receipt.json
```

**验收器源码＋测试确实存在且已隔离执行**：[guard](HISTORICAL_CODEX_RECEIPT_GUARD_20261017.py) Git blob `e47debb9c39c473c78d82eccdbee8d77b13c52cb`、[其六项正式测试](test_history_receipt_guard_20261017.py) Git blob `681711fafe9f78c2c65a1d7cd587fb6d3dcc3d13`，Linux Python3.13 **8/8 pass exit0**，本地完整Git blobs与远端一致。拒绝错HEAD、重复/漏批次、非零退出、无测试计数或日志SHA不合格。 `local_suite_receipt_accepted`即便为true仍永久强制 `business_gold_accepted=false` 与 `historical_recovery_closed=false`；严格防止把软件测试误充真实金标或最终发布。**回执正文与日志先人工脱敏，仅提交无秘密的family id/源SHA/exit/测试数量/日志hash到对应Issues；不得上传原始个人数据**。

注意原始SHA已经固定在脚本内，若Codex修复代码使 HEAD 变化，重新审核新SHA并把本次回执标为`NEW_HEAD_REVALIDATION_REQUIRED`，不能直接改实参或脚本常量绕过原始基线判定。 

### 2026-10-17 Wool PR39本轮新增红绿证据与SHA更新
- 当前PR39新HEAD为 `80c5ea18769c1312e5be5fd99a39e4f3d498c64f`；此前旧HEAD `80c5ea18769c1312e5be5fd99a39e4f3d498c64f` 的Linux58次结果**不能继续作为新HEAD的整包绿灯**。
- [WR-H16 新增编号/Unicode列表识别实际红→绿](https://github.com/lu403369069lu-prog/WoolRadar/blob/chatgpt/wool-historical-integration-20261017/independent-quality/developer-grant-20261017/H16_NUMBERED_SCOPE_RED_GREEN.md)：精确Git blob匹配，旧11+新6真实正式测试共17项，旧源3失败exit1，新源17通过exit0；仍缺Windows整包、独立新窗口准确率与日报签名桥。
- `HISTORICAL_CODEX_BATCH_RUNNER_20261017.py`中Wool EXPECTED已同步为上述新HEAD；先在隔离工作树新SHA上全批次检验，勿自动切换到旧SHA绕过校验。

**2026-10-17集成器修订**：当前批次执行器Git blob `2740d556f24d2ffea563026628f5a904a7a3de73` 已修复Windows `npm.cmd`和来源回执协议对齐；上方8个真实正式测试涵盖含skip/未知通过数的回执拒绝。任何测试被skip都不算已全面验收，即使process exit0。未在三个完整项目Windows执行全部批次，不可冒充验收通过。
