# 第二批100项分类工程验收清单（R2）

此处100项是 **计划核销目标**，不是已完成100轮。每项以实际源码SHA、正例和负例、原生测试的退出码、无隐性跳过及独立验收为完成条件。一次RED、一次GREEN、一次文档更新不能拆开冒充多个目标。

- 不覆盖第一批Revision42的100项工程动作。历史50项严格业务验收仍0/50。
- 源基准：WoolRadar main `e44589104585c4b2a93081d00a145263666f9264`；SAM main `668e219569aff780621bf6a1e24aa8cbe5f4e806`。
- 本批已启动SAM H04/H17独立源码PR37，CI现已跑出真实未通过结论，不可标为已验收。
- 独立 Codex Windows owner/lease/worktree 保持不动；禁止自动合并、支付、生产部署或改动机器上的私密业务源件。

## 大类数量

- W1 通知交付：8 项
- W2 SQLite数据安全：7 项
- W3 审计可靠性：6 项
- W4 来源质量和召回：9 项
- W5 URL身份与安全：5 项
- W6 交付链路闭环：8 项
- W7 自动化验收和恢复：5 项
- S1 Windows正式构建：4 项
- S2 MCP双入口和WorkBuddy：5 项
- S3 61题回答质量：7 项
- S4 522源件Gold：6 项
- S5 Claim证据审核：5 项
- S6 严格输入编码：4 项
- S7 发布产物身份：5 项
- S8 升级回滚事务：5 项
- S9 最终独立验收：6 项
- C 双仓公共：5 项

## R2-001 至 R2-100 全量可核销目标

| 编号 | 大类 | 可独立交付的缺陷/功能目标 | 明确验收依据 | 当前状态 |
|---|---|---|---|---|
| R2-001 | W1 通知交付 | SENT 状态不可回退 | 跨进程抢占后过期 Worker 写入拒绝 | DRAFT_NATIVE_GREEN_NOT_STRICTLY_ACCEPTED |
| R2-002 | W1 通知交付 | 外部 Telegram 超时处理 | 未知送达状态不可冒充 exactly-once | DRAFT_NATIVE_GREEN_NOT_STRICTLY_ACCEPTED |
| R2-003 | W1 通知交付 | 重试退避跨重启 | 期限、次数和幂等键不丢 | DRAFT_NATIVE_GREEN_NOT_STRICTLY_ACCEPTED |
| R2-004 | W1 通知交付 | 同事件入队唯一性 | 两进程竞争仅一个正式通知 | DRAFT_NATIVE_GREEN_NOT_STRICTLY_ACCEPTED |
| R2-005 | W1 通知交付 | 多 Worker 租约 fencing | 旧持有者不能覆盖新持有者 | DRAFT_W1_NATIVE_RED_GREEN_NOT_INTEGRATED |
| R2-006 | W1 通知交付 | 审核撤销与待发消息一致 | 送出之前校验最新资格 | PLANNED_NOT_VERIFIED |
| R2-007 | W1 通知交付 | 本地通知原子持久化 | 文件 rename 后提交失败可恢复 | PLANNED_NOT_VERIFIED |
| R2-008 | W1 通知交付 | 429及断网故障注入 | 每一故障有确定恢复状态 | DRAFT_NATIVE_GREEN_NOT_STRICTLY_ACCEPTED |
| R2-009 | W2 SQLite数据安全 | Schema 真实数据迁移 | 旧版拷贝升级且索引和行数一致 | PLANNED_NOT_VERIFIED |
| R2-010 | W2 SQLite数据安全 | 迁移中断事务回滚 | 故障注入后旧库不损坏 | PLANNED_NOT_VERIFIED |
| R2-011 | W2 SQLite数据安全 | WAL 在线备份 | 未 checkpoint 时可独立恢复 | DRAFT_NATIVE_GREEN_NOT_STRICTLY_ACCEPTED |
| R2-012 | W2 SQLite数据安全 | 备份恢复完整性 | 逐表记录和关键约束可核对 | DRAFT_NATIVE_GREEN_NOT_STRICTLY_ACCEPTED |
| R2-013 | W2 SQLite数据安全 | 新旧版本兼容拒绝 | 不支持降级明确失败不写坏数据 | DRAFT_NATIVE_GREEN_NOT_STRICTLY_ACCEPTED |
| R2-014 | W2 SQLite数据安全 | 并发 reindex/upsert | 同键不重影且无丢更新 | PLANNED_NOT_VERIFIED |
| R2-015 | W2 SQLite数据安全 | 数据库损坏与磁盘已满 | 保守停机及可追溯恢复 | PLANNED_NOT_VERIFIED |
| R2-016 | W3 审计可靠性 | 业务状态与审计同事务 | 任一失败则均不提交 | DRAFT_W3_4X4_GREEN_FULL_WIN_1_SKIP_NOT_INTEGRATED |
| R2-017 | W3 审计可靠性 | 证据写入与审计引用一致 | 不能存在成功状态与失联证据 | PLANNED_NOT_VERIFIED |
| R2-018 | W3 审计可靠性 | 跨进程审计去重 | 业务键并发只生成一次权威审计 | PLANNED_NOT_VERIFIED |
| R2-019 | W3 审计可靠性 | 审计链缺口检测 | 伪造与删除可离线发现 | PLANNED_NOT_VERIFIED |
| R2-020 | W3 审计可靠性 | 未知投递恢复可追溯 | 明确已送达/不确定/撤销 | PLANNED_NOT_VERIFIED |
| R2-021 | W3 审计可靠性 | 审计脱敏与摘要 | 隐私字段不泄露且证据可验证 | PLANNED_NOT_VERIFIED |
| R2-022 | W4 来源质量和召回 | P06 来源冻结 | 原始源件时间窗口与 SHA 固定 | PLANNED_NOT_VERIFIED |
| R2-023 | W4 来源质量和召回 | 新47样本独立召回 | 固定分母出具体漏报率和漏项 | PLANNED_NOT_VERIFIED |
| R2-024 | W4 来源质量和召回 | 跨 URL 实体合并 | 同一活动合并异活动不误合 | PLANNED_NOT_VERIFIED |
| R2-025 | W4 来源质量和召回 | URL别名与活动版本分离 | 相同网址资格变化能重审 | PLANNED_NOT_VERIFIED |
| R2-026 | W4 来源质量和召回 | 官方来源优先级 | 转述与官网矛盾时保守拒绝 | PLANNED_NOT_VERIFIED |
| R2-027 | W4 来源质量和召回 | 收费绑卡否定语义 | 原始抓取与品牌兜底一同门禁 | PLANNED_NOT_VERIFIED |
| R2-028 | W4 来源质量和召回 | 截止撤回状态传播 | 撤销后日报不得重发 | PLANNED_NOT_VERIFIED |
| R2-029 | W4 来源质量和召回 | 独立盲测真实指标 | 不修改门槛不替换测试分母 | PLANNED_NOT_VERIFIED |
| R2-030 | W4 来源质量和召回 | 来源变更失效缓存 | 新版资格地区规则触发重新核验 | PLANNED_NOT_VERIFIED |
| R2-031 | W5 URL身份与安全 | H07修复合并候选源 SHA | 生产者与采样器采用相同修复 | PLANNED_NOT_VERIFIED |
| R2-032 | W5 URL身份与安全 | 多跳重定向防SSRF | 每跳域名/IP/scheme均安全 | PLANNED_NOT_VERIFIED |
| R2-033 | W5 URL身份与安全 | IDNA/主机端口规范化 | 采集与抽样身份判定一致 | PLANNED_NOT_VERIFIED |
| R2-034 | W5 URL身份与安全 | 多层编码隐私防泄露 | 路径片段查询秘密反例全部拒绝 | PLANNED_NOT_VERIFIED |
| R2-035 | W5 URL身份与安全 | DNS重绑定 | 解析地址变动不会绕过私网禁令 | PLANNED_NOT_VERIFIED |
| R2-036 | W6 交付链路闭环 | 产出与消费确认分离 | 生成文件不等于下游签收 | PLANNED_NOT_VERIFIED |
| R2-037 | W6 交付链路闭环 | 生产消费同源码 SHA | 错版消费者拒绝旧产物 | PLANNED_NOT_VERIFIED |
| R2-038 | W6 交付链路闭环 | DELIVERY_BRIDGE 脱敏 | 真实输出形态不含凭据 | PLANNED_NOT_VERIFIED |
| R2-039 | W6 交付链路闭环 | 发布签名绑定清单 | 签名或SHA错误不能发布 | PLANNED_NOT_VERIFIED |
| R2-040 | W6 交付链路闭环 | 同秒快照顺序 | 有歧义时不重启被撤销活动 | PLANNED_NOT_VERIFIED |
| R2-041 | W6 交付链路闭环 | 下游消费幂等重放 | 故障重试不重复提醒 | PLANNED_NOT_VERIFIED |
| R2-042 | W6 交付链路闭环 | 网络中断和积压恢复 | 保留期限和资格门禁 | PLANNED_NOT_VERIFIED |
| R2-043 | W6 交付链路闭环 | OUTPUT_NOT_CONNECTED 完整闭环 | 有真实消费回执或确切阻塞 | PLANNED_NOT_VERIFIED |
| R2-044 | W7 自动化验收和恢复 | 主线跨平台完整测试 | 不把skip TODO预期失败当PASS | PLANNED_NOT_VERIFIED |
| R2-045 | W7 自动化验收和恢复 | 队列所测源 SHA 对齐 | 旧队列不能核销新PR | PLANNED_NOT_VERIFIED |
| R2-046 | W7 自动化验收和恢复 | CI测试映射反伪造 | 对应真实用例才能核销大类 | PLANNED_NOT_VERIFIED |
| R2-047 | W7 自动化验收和恢复 | 跨运行checkpoint恢复 | CAS及重试不覆盖已提交记录 | PLANNED_NOT_VERIFIED |
| R2-048 | W7 自动化验收和恢复 | 自动诊断与自动修复区分 | 只有代码修改加复验才叫修复 | PLANNED_NOT_VERIFIED |
| R2-049 | S1 Windows正式构建 | Node24 Windows隔离构建 | 真实npm ci和构建执行码 | PLANNED_NOT_VERIFIED |
| R2-050 | S1 Windows正式构建 | Node26 Windows隔离构建 | 实际原生运行和进程退出 | PLANNED_NOT_VERIFIED |
| R2-051 | S1 Windows正式构建 | dist可重复身份 | 源码和产物 SHA 显式绑定 | PLANNED_NOT_VERIFIED |
| R2-052 | S1 Windows正式构建 | EPERM路径与符号链接 | 逐项修复原7个失败而非删除测试 | PLANNED_NOT_VERIFIED |
| R2-053 | S2 MCP双入口和WorkBuddy | stdio真实握手及关闭 | 帧协议和进程退出正确 | PLANNED_NOT_VERIFIED |
| R2-054 | S2 MCP双入口和WorkBuddy | direct与stdio输出权限等价 | 同源同请求结果一致 | PLANNED_NOT_VERIFIED |
| R2-055 | S2 MCP双入口和WorkBuddy | WorkBuddy显式过滤 | 禁止错误回退和越权摘要 | PLANNED_NOT_VERIFIED |
| R2-056 | S2 MCP双入口和WorkBuddy | 恶意MCP帧负例 | 畸形JSON超长帧异常关闭安全 | PLANNED_NOT_VERIFIED |
| R2-057 | S2 MCP双入口和WorkBuddy | 多个MCP客户端会话隔离 | 不同工程之间不串证据 | PLANNED_NOT_VERIFIED |
| R2-058 | S3 61题回答质量 | 61题固定分母和版本 | 每题真实原始金答案可复核 | PLANNED_NOT_VERIFIED |
| R2-059 | S3 61题回答质量 | 逐题来源绑定评分 | 正确错引语义偏差分开统计 | PLANNED_NOT_VERIFIED |
| R2-060 | S3 61题回答质量 | T009原始证据核验 | 不得用合成件代替source gold | PLANNED_NOT_VERIFIED |
| R2-061 | S3 61题回答质量 | T031 Axis/FSM修复 | 近义术语正确区分并留反例 | PLANNED_NOT_VERIFIED |
| R2-062 | S3 61题回答质量 | 错误拒答与正确拒答区分 | 理由与来源缺口准确 | PLANNED_NOT_VERIFIED |
| R2-063 | S3 61题回答质量 | 跨项目同名符号隔离 | 仓库范围影响证据资格 | PLANNED_NOT_VERIFIED |
| R2-064 | S3 61题回答质量 | 不放宽门槛提升正答 | 独立样本能证实真正改进 | PLANNED_NOT_VERIFIED |
| R2-065 | S4 522源件Gold | 522原始件目录哈希 | 缺失件不算审查通过 | PLANNED_NOT_VERIFIED |
| R2-066 | S4 522源件Gold | 引用定位准确率 | 行号与实际文件匹配 | PLANNED_NOT_VERIFIED |
| R2-067 | S4 522源件Gold | 同名多版本审查不复用 | 版本改变必须重新评判 | PLANNED_NOT_VERIFIED |
| R2-068 | S4 522源件Gold | 冲突及歧义记录 | 原始证据冲突时保守回答 | PLANNED_NOT_VERIFIED |
| R2-069 | S4 522源件Gold | 人工语义Gold审查 | 机器检查和人工评价分开 | PLANNED_NOT_VERIFIED |
| R2-070 | S4 522源件Gold | 独立三轮Gold对照 | 三套实际凭据可追溯 | PLANNED_NOT_VERIFIED |
| R2-071 | S5 Claim证据审核 | H04审查结论源件SHA绑定 | 错SHA撤销审查且保留所有旧测试 | DRAFT_SAM_4X37_GREEN_FULL_6_MISSING_FROZEN |
| R2-072 | S5 Claim证据审核 | Claim仓库与提交作用域 | 相同ID跨库不能共享结论 | PLANNED_NOT_VERIFIED |
| R2-073 | S5 Claim证据审核 | Entailed证据ID真实性 | 空/假证据必须拒绝通过 | PLANNED_NOT_VERIFIED |
| R2-074 | S5 Claim证据审核 | 审查字段类型抗伪造 | 非预期类型及枚举失败关闭 | DRAFT_NATIVE_GREEN_NOT_STRICTLY_ACCEPTED |
| R2-075 | S5 Claim证据审核 | 资料变动使审核失效 | 保留历史并要求重新验证 | PLANNED_NOT_VERIFIED |
| R2-076 | S6 严格输入编码 | H14真实运行时Unicode折叠 | 真实评测入口接入修复 | DRAFT_SAM_H14_NATIVE_RED_GREEN_FULL_6_FAIL |
| R2-077 | S6 严格输入编码 | JSON/JSONL重复键拒绝 | 全部入口不容键覆盖 | PLANNED_NOT_VERIFIED |
| R2-078 | S6 严格输入编码 | 非法UTF-8换行拒绝 | 不被替换字符掩盖 | PLANNED_NOT_VERIFIED |
| R2-079 | S6 严格输入编码 | Windows路径别名安全 | DOS8.3符号链接越界有负例 | PLANNED_NOT_VERIFIED |
| R2-080 | S7 发布产物身份 | dist清单与源码一致 | 内容哈希可独立证明 | PLANNED_NOT_VERIFIED |
| R2-081 | S7 发布产物身份 | 缓存与工作区隔离 | 旧dist不能污染新发行 | PLANNED_NOT_VERIFIED |
| R2-082 | S7 发布产物身份 | R5正式发布验收 | 隔离发布完整退出码 | PLANNED_NOT_VERIFIED |
| R2-083 | S7 发布产物身份 | Windows正式安装运行 | 从安装目录启动MCP | PLANNED_NOT_VERIFIED |
| R2-084 | S7 发布产物身份 | 消费方发行清单验证 | 错版本明确拒绝 | PLANNED_NOT_VERIFIED |
| R2-085 | S8 升级回滚事务 | H17真实发布路径接入事务 | 不只是存在工具文件 | DRAFT_SAM_4X37_GREEN_FULL_6_MISSING_FROZEN |
| R2-086 | S8 升级回滚事务 | 进程崩溃后指针恢复 | 中断点全覆盖并守恒 | PLANNED_NOT_VERIFIED |
| R2-087 | S8 升级回滚事务 | 0.4.1到0.4.2真实升级 | 保留数据及审核证据 | PLANNED_NOT_VERIFIED |
| R2-088 | S8 升级回滚事务 | 0.4.2到0.4.1真实回滚 | 还原旧版与指针 | PLANNED_NOT_VERIFIED |
| R2-089 | S8 升级回滚事务 | 跨进程锁及死owner恢复 | 不能窃取活owner锁 | PLANNED_NOT_VERIFIED |
| R2-090 | S9 最终独立验收 | 原始61题正式复验 | 真实冻结分母逐项收据 | PLANNED_NOT_VERIFIED |
| R2-091 | S9 最终独立验收 | 522 Gold正式复验 | 审查覆盖和未审数量明确 | PLANNED_NOT_VERIFIED |
| R2-092 | S9 最终独立验收 | 干净Windows全栈构建 | 原生命令及完整日志 | PLANNED_NOT_VERIFIED |
| R2-093 | S9 最终独立验收 | MCP三入口最终一致 | 同一安装包实际运行 | PLANNED_NOT_VERIFIED |
| R2-094 | S9 最终独立验收 | 独立三轮真实复验 | 各轮记录不可伪造重用 | PLANNED_NOT_VERIFIED |
| R2-095 | S9 最终独立验收 | 正式交付零隐性skip | 跳过缺源件导致验收不通过 | PLANNED_NOT_VERIFIED |
| R2-096 | C 双仓公共 | 跨仓证据账本一致 | 只根据真实执行收据变更状态 | PLANNED_NOT_VERIFIED |
| R2-097 | C 双仓公共 | CI source SHA和run防重放 | PR与复验轮次严密绑定 | PLANNED_NOT_VERIFIED |
| R2-098 | C 双仓公共 | Issue/PR候选关系去重 | 同一修复不重复核销 | PLANNED_NOT_VERIFIED |
| R2-099 | C 双仓公共 | owner lease fencing安全 | 不覆盖其他Agent生产分支 | PLANNED_NOT_VERIFIED |
| R2-100 | C 双仓公共 | V3 CHECKPOINT ZIP可离线复核 | 日志SHA与脱敏清单齐全 | PLANNED_NOT_VERIFIED |

## 当次实际记录

- PR37：https://github.com/lu403369069lu-prog/YinQieJi/pull/37，SAM H04/H17 八源码/测试文件恢复成功，test/card-index原始6测试未丢。H04/H17四矩阵原生专项已无失败；全量测试因缺rg与冻结资料及部分路径环境问题失败；不核销R2-071或R2-085。
- 本表只能在对照真实SHA和新测试收据后变更状态。不可按已规划数量自动推进完成数。

## 接力追加：同一批 R2 的精确验证收据

- R2-016（W3）：https://github.com/lu403369069lu-prog/WoolRadar/pull/66 ，当前原始基线真实状态审计事务修复，在同一 SQLite 写锁下取得旧状态；新增提交包括原生独立进程竞态测试。初始真正RED https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39118350630 ；初次4×3 GREEN https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39118394861。Windows主套上个已完成run314测试成功313/314（其中跳过1项上游官方运行时），Linux因为原仓库Windows-only PowerShell诊断包装而完整套失败，未核销。
- R2-071、R2-085（SAM H04/H17）：https://github.com/lu403369069lu-prog/YinQieJi/pull/37 ，真实源码八文件移植和Windows/Linux Node24/26目标32/32每作业通过；完整原始回归 273/279，6件冻结教师/发行资料缺失，不能伪造或跳过核销。证据 https://github.com/lu403369069lu-prog/YinQieJi/actions/runs/39118217153 。
- 所有其他 R2 目标仍未执行/未验收。以上尚不能减少历史0/50严格业务缺口。

## 接力追加：W1 与 H14 新代码 RED→GREEN

- R2-005 W1 局部投递所有权防回退：Draft PR67 https://github.com/lu403369069lu-prog/WoolRadar/pull/67 是前述W3候选上的独立叠加PR。原始源码中旧Worker在SQLite最终CAS失败之前即可覆盖继任者已持久化的本地JSON。真实Windows/Linux Python3.11/3.12四平台 RED https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39119101634 每个Job1目标失败，错误内容确认为 STALE_WRITER_MUST_NOT_REPLACE_VALID_RECEIPT。代码将各次租约尝试写到独立随机临时文件，最终重检和rename/SENT事务都在 SQLite BEGIN IMMEDIATE 中；GREEN https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39119246179 四Job均成功，单例新对抗测试及原通知10用例通过。只是已测安全候选，不等于Telegram外部exactly-once/所有W1工作已完成。
- R2-016 W3 同一真实事件状态写锁及审计连接历史：PR66 https://github.com/lu403369069lu-prog/WoolRadar/pull/66 新增双Windows/Linux原生进程竞争用例，目标4测试均通过；https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39118649900 Windows全套315=314成功+1跳过，Linux因真实Windows诊断PowerShell脚本有2失败及5系统相关跳过；不宣称完整工程验收。
- R2-076 SAM H14 真实评测入口Unicode去重：PR37 https://github.com/lu403369069lu-prog/YinQieJi/pull/37，原始事件 RED https://github.com/lu403369069lu-prog/YinQieJi/actions/runs/39118823745 全4 native jobs目标测试失败（QS与Qſ重复未阻止），原码改为小写后大写归一，最终专项 37/37 全4作业成功零跳过，https://github.com/lu403369069lu-prog/YinQieJi/actions/runs/39118908996；同一源码完整回归 274/280，仍有6项原始教师/正式发布冻结资料缺失，0项正式业务验收新增。
- 所有工作以各 Draft 的实际 SHA 审核，不自动合并、不推送本机、不读取私人教师材料。不把不同目标的单次GREEN重复计为R2已验收。


## 2026-10-18 R2 W1/W2 六项原生候选证据（严格核销仍为0）

均是隔离、未合并的草稿PR，Windows/Linux × Python3.11/3.12四平台真实作业成功。R2-001/002/008/013有实际RED→GREEN；R2-003/004是既有源码的跨重启/真实双进程正向验证，不伪称修复不存在的故障。

- **R2-001** SENT终态跨进程约束：[PR68](https://github.com/lu403369069lu-prog/WoolRadar/pull/68)。[RED39131300302](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39131300302) → [GREEN39131365517](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39131365517)。SQLite触发器拒绝已发送→待发，既有10条通知及旧Worker防覆盖回归亦通过。
- **R2-004** 双真实进程同事件唯一入队：[PR69](https://github.com/lu403369069lu-prog/WoolRadar/pull/69)、[GREEN39131550086](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39131550086)。同键仅一个ONE一个ZERO，正式表和本地文件仅一条。
- **R2-003** 故障退避重启：[PR70](https://github.com/lu403369069lu-prog/WoolRadar/pull/70)、[GREEN39131633974](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39131633974)。数据库新实例保留重试截止和计数，过早不发送，到期才发送。
- **R2-002** Telegram未知送达：[PR71](https://github.com/lu403369069lu-prog/WoolRadar/pull/71)、[RED39131763811](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39131763811) → [GREEN39131821912](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39131821912)。异常后持久UNCERTAIN+有限重试，仍仅at-least-once，绝非exactly-once。
- **R2-008** 429/断网故障注入：[PR72](https://github.com/lu403369069lu-prog/WoolRadar/pull/72)、[RED39131994551](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39131994551) → [GREEN39132054614](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39132054614)。模拟429带Retry-After:120覆盖较短本地间隔；断网持久UNCERTAIN。其他HTTP-date退避形式未验。
- **R2-013** SQLite未来版本先读拒绝：[PR73](https://github.com/lu403369069lu-prog/WoolRadar/pull/73)、[RED39132251927](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39132251927)、首个候选[39132322563](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39132322563) Linux绿Windows因测试夹具未close而失败、修复测试后[GREEN39132418582](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39132418582)。只用合成库验证新版本被只读拒绝，旧版0→1保留数据；未接触生产DB。

目前此前5项局部候选 + 本次6项局部候选 = 11项进入不同程度工程验证（不是11项严格完成）。R2业务验收仍**0/100**、历史50大类严格完成仍**0/50**。所有上述PR仍需源码整合、完整无skip回归、业务证据及独立验收；不合并、不改Windows生产、不发送真实消息。


### 后续R2-011 / R2-012 独立WAL备份恢复原生收据

- [Draft PR75](https://github.com/lu403369069lu-prog/WoolRadar/pull/75) 源码上真实执行两个区分明确的测试：R2-011 在现存读事务固定旧快照时，新增提交进入WAL且未checkpoint，调用真实reindex在线备份，证明备份包含刚提交的事件、官方模拟证据及入队通知；R2-012 将备份文件复制到独立数据库，逐表比对8表全部记录、SQLite integrity_check=ok、foreign_key_check空。
- [Actions39132865286](https://github.com/lu403369069lu-prog/WoolRadar/actions/runs/39132865286) Windows/Linux × Python3.11/3.12 四平台均执行成功，每平台2项新增备份恢复测试与2项前序Schema版本测试通过，零跳过。没有刻意制造RED故障，也没有宣称修正了原本不存在的备份错误。
- 仅合成数据与隔离草稿；未触碰生产数据库或改动主线。R2-011、012正式业务恢复演练和全部回归仍未进行，**不能核销为严格完成**。目前R2有先前5项候选、本次W1/W2先登记6项、此次新增2项，即共13项曾进入不同程度候选验证；R2严格验收仍0/100。


### SAM R2-074 真实审查字段类型防伪红绿收据

- [YinQieJi Draft PR38](https://github.com/lu403369069lu-prog/YinQieJi/pull/38) 在真实SAM snapshot的source-qualified资格函数入口验证：有效官方合成来源的review body/SHA/原文件行锚点先正常通过；将来源ID与对应subclaim引用一起篡改为数字、布尔、null或空白，或将subclaim文本改数字并重新计算review hash，必须拒绝。源TS接口声明string不能替代JSON运行时类型检查。
- [RED39133161071](https://github.com/lu403369069lu-prog/YinQieJi/actions/runs/39133161071) Windows/Linux × Node24/26四平台均真实失败，旧代码确实错误接受非字符串来源ID。修复运行时类型校验后[GREEN39133234955](https://github.com/lu403369069lu-prog/YinQieJi/actions/runs/39133234955)四平台成功，保留原评测输入回归测试。
- 此为孤立源资格安全修复，未包含522个真实源件或正式教师gold的认可，R2-074严格验收仍未完成。此前13项不同程度候选加上本次1项，第二批共14项有部分工程验证；严格核销0/100。
