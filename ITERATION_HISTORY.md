---
type: iteration-history
date: 2026-10-14
tags: [WoolRadar, engineering]
---
# 迭代历史与审查意见

这是从可访问交接、现有源码、部署回执和当前Agent审查还原的历史；不是所有会话的逐字记录。不可访问的其他Agent完整讨论和用户账号内部状态明确未知。日期及测试数以各轮回执为准，旧“latest”说明不当实时状态。

| 日期/阶段 | 起因、方案与采用意见 | 实际验证 | 遗留与否定方案 |
|---|---|---|---|
| 10月11日安装审计 | 五个上游分别锁定提交/许可证/环境；Windows只读适配核心 | Digest UTF8：296pass/1skip；Linuxdo纯函数4pass；公开三节点采集 | GBK初失败不计成功；userscript点赞/积分禁止；OpenMagpie LFS初失败不等于完整源码/运行失败，缺git-lfs仍记录 |
| 核心证据/身份 | 普通新闻/转载不能变福利或独立交叉证明；保留规格数字与共同provenance | 九状态/去重/证据归档；核心早期66→68→70→72是历史轮次 | 真实≥95%分母未建立；空CLAIMABLE不冒100%资格 |
| 10月12日预算/韧性 | HN子请求/redirect预算缺口，source-only pause、通知/诊断问题 | 逐HTTP与逐跳SQLite预算、HN24h断点、模拟401/429/503、报告轮转/退出码、配置和隔离DB恢复 | 不主动断网/制造平台限流；不删屏障；不以隔离恢复当全栈灾备 |
| 10月12日官方条件 | 公开flag被误当个人资格；到期时间/年度批次存在混淆 | 限公开申请scope、未来/无时区时间不冒claim、官方显式年度批次；自由叙述互补、结构化冲突保留 | 完整条件抽取、重新开放、账号资格未实现 |
| NAS活动去重 | 两文章标题变化而同Gleam Isp30；Halloween另一ID | 正常公开复核后生产合并1条，98→97；UTM一致，碰撞原证据归档 | 不凭相似标题合并不同奖品/新批次；旧作者截止声明不等当前官方开放 |
| 官方案例复核 | MLH赞助讲座被误解为会员赠送；主办方条款不等厂商最新条款 | Cursor/Grok讲座成立但freePro未证；Auth0厂商25000月活vsMLH旧7000、MongoDB学生50美元依赖学生包 | 免费层nocard不外推额度；RackNerd100/20是总量而非余量；DO/Vultr条件未知 |
| 无网页接入研究 | 用户Chrome已登录但工具路径失败，研究GitHub实现 | RedditRSS25、热门RSS25、X已知帖1；应用只读adapter模拟验证 | XDK/PRAW需平台权限；Twikit/twscrape/RSSHub Cookie路线未采用；Nitter当时归档；单帖探针不等搜索 |
| 10月12日依赖 | PyPI审查先被自动审核拒绝，用户后来明确允许包名版本外发 | 三环境51/22/55包审计、仅pip26.1.1→26.2；pipcheck及已扫描包复查 | 已知漏洞查询不是全源码安全证明；本地editable及未装Node环境不覆盖 |
| OpenMagpie后端准备 | CLI被误当完整后端；原依赖存在已知漏洞 | 独立backend环境、锁定Twikit38文件Git blob一致；7包安全更新，pipcheck、禁网Django check、7SSRF/IP通过 | ENGINE_MODEL未设警告保留；Postgres/模型端口连接未建立；不用SQLite替代，不启挑战绕过 |
| 10月12日/save后续 | stage123关键词初稿还未生产，随后用户恢复 | 独立复审追加真实正例，生产127；原3 Reddit噪声完整正文离线回放拒绝 | 曾考虑历史日报审计排除，相关3测试已撤回，功能没有实现；旧噪声不被追溯删除 |
| 10月13日禁用来源 | 禁用OAuth被误记认证故障，拖低公共RSS节点 | 4测试先3失败；生产131；禁用SKIPPED无请求、公共RSS25/0新匹配真实OK | 全跳过不报成功；启用源真实403/auth失败仍暂停；注册必验取消不等通过 |
| 10月14日公开原始采样 | 仅命中Inbox无法建立漏报分母 | 同次采集保留未命中，隐私/UTF8硬上限/大小写URL/错误隔离；生产142 | 公开source+kind双约束；不额外fetch；500行/8MB仍是有界最新样本，不是全量分母 |
| 六任务黑窗口 | 真实六Action直接启动console PowerShell | GUI C#启动器、PS/Python/后续子进程CreateNoWindow；142生产；六实际新运行退出0，三层consolefalse，XML trigger/principal/settings保持 | 不用Task.Hidden或停采集冒修复；只SetAction，不Force重建触发；运行观察非长期桌面保证 |
| 启动链审查返工 | reviewer复现普通异常回执仍running、诊断失败可遗留子进程 | Python finally终态、best-effort回执，立即并行drain，owned-child cleanup；ValueError/exit7/写失败边界复查 | 不读取私有profile；不通过诊断失败伪造正常exit；C#只结束后有终态回执，早期运行中回执缺口记录 |
| 金额credits漏报 | Cloudflare winner receives $500000摘要未命中 | 新正例失败后修正；求助/否定/等价付费负例；144生产；原样本0→1命中 | 正文申请10月2日已截止，10月19日是比赛；入库EXPIRED/NONE，不推当前可领取 |
| DevHunt导航 | 4命中里3为自站导航，1为外部Gemini定价 | 精确exclude_hosts仅该来源；145生产；259行回放删3导航留1外部线索 | 不用全域/perks路径排除误伤外部；大量目录program标题的召回仍未完成 |
| 后续LowEndBox | 专用coupon code和Start Using for FREE两漏报 | reviewer补无券/求券、免绑卡/不过期边界；148生产；20行原样本明确6线索由4→6 | 同一修正样本不是留出评估；付费仅价格3条范围未裁定；不能宣称95% |
| 最新官方补证 | Gemini/ServerCrate社区线索条件不足 | Work英文官方读；Gemini2=OFFICIAL_VERIFIED/NONE；ServerCrate112=OFFICIAL_VERIFIED/NONE，10GB/2设备/7天/nocard，旧1设备保留 | Gemini地区页ServiceUnavailable；个人准入、完整条款、服务质量未验，不注册上传 |
| PostgreSQL替代研究 | Docker/WSL阻塞，查项目级portable方案 | 官方Windows页指EDB ZIP；观察16.15，运行库文件存在 | 下载等待失败/内核重置，没有成功包/安装/启动证据；不要重复下载或用方案当部署 |

## 其他Agent与方案归属

- `/root/budget_review` 是只读reviewer：指出采样凭据/大文件/错误标记边界、启动链生命周期、金额credits和coupon/free CTA负例。以上意见经主Agent实际改动与验证后采纳，不把reviewer“未发现阻断”当现场通过。
- 另一个协调会话提供六任务黑框线索、确认本任务Stop契约绑定及不并写。主Agent读取真实任务XML/脚本后实施和独立核验；协调回执不是完成证据。
- 历史Work云端X任务只回报可见/超时/未注册。完整对话不可访问，不能扩写其结论，也不重复创建任务。
- 当前GitHub协作Agent先创建骨架。骨架的“没有实现/测试”只描述当时仓库内容，不是本地项目不存在。本PR补真实状态；未与其虚构讨论或发送其他渠道消息。

主要否定方案：凭Chrome登录/Gmail连接推导API权限、Cookie/token迁移、匿名接口直接当合法稳定接入、FlareSolverr/挑战绕过、根目录全量上传、用CLI/单元测试冒完整上游成功、用便携方案设计冒Postgres上线、用Stage结果冒生产结果。
