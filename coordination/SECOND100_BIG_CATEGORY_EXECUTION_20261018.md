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
| R2-001 | W1 通知交付 | SENT 状态不可回退 | 跨进程抢占后过期 Worker 写入拒绝 | PLANNED_NOT_VERIFIED |
| R2-002 | W1 通知交付 | 外部 Telegram 超时处理 | 未知送达状态不可冒充 exactly-once | PLANNED_NOT_VERIFIED |
| R2-003 | W1 通知交付 | 重试退避跨重启 | 期限、次数和幂等键不丢 | PLANNED_NOT_VERIFIED |
| R2-004 | W1 通知交付 | 同事件入队唯一性 | 两进程竞争仅一个正式通知 | PLANNED_NOT_VERIFIED |
| R2-005 | W1 通知交付 | 多 Worker 租约 fencing | 旧持有者不能覆盖新持有者 | PLANNED_NOT_VERIFIED |
| R2-006 | W1 通知交付 | 审核撤销与待发消息一致 | 送出之前校验最新资格 | PLANNED_NOT_VERIFIED |
| R2-007 | W1 通知交付 | 本地通知原子持久化 | 文件 rename 后提交失败可恢复 | PLANNED_NOT_VERIFIED |
| R2-008 | W1 通知交付 | 429及断网故障注入 | 每一故障有确定恢复状态 | PLANNED_NOT_VERIFIED |
| R2-009 | W2 SQLite数据安全 | Schema 真实数据迁移 | 旧版拷贝升级且索引和行数一致 | PLANNED_NOT_VERIFIED |
| R2-010 | W2 SQLite数据安全 | 迁移中断事务回滚 | 故障注入后旧库不损坏 | PLANNED_NOT_VERIFIED |
| R2-011 | W2 SQLite数据安全 | WAL 在线备份 | 未 checkpoint 时可独立恢复 | PLANNED_NOT_VERIFIED |
| R2-012 | W2 SQLite数据安全 | 备份恢复完整性 | 逐表记录和关键约束可核对 | PLANNED_NOT_VERIFIED |
| R2-013 | W2 SQLite数据安全 | 新旧版本兼容拒绝 | 不支持降级明确失败不写坏数据 | PLANNED_NOT_VERIFIED |
| R2-014 | W2 SQLite数据安全 | 并发 reindex/upsert | 同键不重影且无丢更新 | PLANNED_NOT_VERIFIED |
| R2-015 | W2 SQLite数据安全 | 数据库损坏与磁盘已满 | 保守停机及可追溯恢复 | PLANNED_NOT_VERIFIED |
| R2-016 | W3 审计可靠性 | 业务状态与审计同事务 | 任一失败则均不提交 | PLANNED_NOT_VERIFIED |
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
| R2-071 | S5 Claim证据审核 | H04审查结论源件SHA绑定 | 错SHA撤销审查且保留所有旧测试 | CANDIDATE_CODE_CI_FAILURE_NOT_ACCEPTED |
| R2-072 | S5 Claim证据审核 | Claim仓库与提交作用域 | 相同ID跨库不能共享结论 | PLANNED_NOT_VERIFIED |
| R2-073 | S5 Claim证据审核 | Entailed证据ID真实性 | 空/假证据必须拒绝通过 | PLANNED_NOT_VERIFIED |
| R2-074 | S5 Claim证据审核 | 审查字段类型抗伪造 | 非预期类型及枚举失败关闭 | PLANNED_NOT_VERIFIED |
| R2-075 | S5 Claim证据审核 | 资料变动使审核失效 | 保留历史并要求重新验证 | PLANNED_NOT_VERIFIED |
| R2-076 | S6 严格输入编码 | H14真实运行时Unicode折叠 | 真实评测入口接入修复 | PLANNED_NOT_VERIFIED |
| R2-077 | S6 严格输入编码 | JSON/JSONL重复键拒绝 | 全部入口不容键覆盖 | PLANNED_NOT_VERIFIED |
| R2-078 | S6 严格输入编码 | 非法UTF-8换行拒绝 | 不被替换字符掩盖 | PLANNED_NOT_VERIFIED |
| R2-079 | S6 严格输入编码 | Windows路径别名安全 | DOS8.3符号链接越界有负例 | PLANNED_NOT_VERIFIED |
| R2-080 | S7 发布产物身份 | dist清单与源码一致 | 内容哈希可独立证明 | PLANNED_NOT_VERIFIED |
| R2-081 | S7 发布产物身份 | 缓存与工作区隔离 | 旧dist不能污染新发行 | PLANNED_NOT_VERIFIED |
| R2-082 | S7 发布产物身份 | R5正式发布验收 | 隔离发布完整退出码 | PLANNED_NOT_VERIFIED |
| R2-083 | S7 发布产物身份 | Windows正式安装运行 | 从安装目录启动MCP | PLANNED_NOT_VERIFIED |
| R2-084 | S7 发布产物身份 | 消费方发行清单验证 | 错版本明确拒绝 | PLANNED_NOT_VERIFIED |
| R2-085 | S8 升级回滚事务 | H17真实发布路径接入事务 | 不只是存在工具文件 | CANDIDATE_CODE_CI_FAILURE_NOT_ACCEPTED |
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
