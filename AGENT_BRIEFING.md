---
type: agent-briefing
date: 2026-10-14
tags: [WoolRadar, handoff]
---
# WoolRadar：真实项目背景与实现

本仓库同步的是 Windows 已部署程序的自有代码、测试、公开配置及经过脱敏的交接资料。不是重新开发，也不是五个上游完整系统已经验收。生产仍在本机运行；本次同步不停止任务、不改架构、不合并 PR。

## 目标及需求变化

最初目标：在 `C:\WoolRadar` 部署五个保持独立的上游系统，发现开发者额度、免费服务、赠送活动等机会；跟踪19个平台，保存官方证据和未知条件，保守去重与新批次提醒，生成中文 MD/JSON 简报并提供调度、通知、启停、诊断、回滚和卸载。

原验收包括可访问真实样本回查/召回≥95%、去重≥95%、资格结论有证据100%、未经授权领取/支付/发帖等为0。前三项尚未整体验收；不能用单元测试、空集或已配置平台数替代。

重要变化：

- 10月11日暂不登录 X/Reddit，先推进公开来源。后来用户报告日常 Chrome 两站经 Google 登录，并授权研究必要的开发者接入；普通浏览器登录仍不能证明 API 读取权限。
- 用户授权用 Work 浏览器研究和仅向 PyPI 发送包名/版本查漏洞；不授权导出 Google token、Cookie 或读取邮箱验证码。
- 10月12日交付第二份简报并 `/save` 后曾暂停；后续“继续”已恢复。旧暂停交接不能覆盖新指令。
- 10月13日明确要求受锁定流程寻求替代，仍不行则取消该验证。Reddit开发者应用创建及认证 API **不再是本轮必经验收**，取消不等于验证通过；公开 RSS 保留。
- 例行项目权限升级走自动审核，不反复询问。系统组件、管理员、重启、协议接受、付款及外部发送仍有各自授权边界。
- 10月14日新增六个定时任务黑窗口修复、原始采样、真实漏报/误报回放，以及本次 GitHub Agent 知识同步。同步的终点是另一 Agent 能准确审查，不是 WoolRadar 总验收完成。

## 实际架构

五个 `nodes/<node>/run.py` 是独立入口；它们调用自有 `nodes/run_node.py`。共享 `core` 提供采集格式、请求预算、规则、数据库和报告。共享核心不是把五个上游后台合并成一个系统，也不等于运行原上游完整产品。

处理链：公开 RSS/HTML/HN 或明确启用的专用适配器 → 来源及关键词边界 → Candidate → SQLite 事件/目击/证据 → 保守身份与批次归组 → VerificationEngine → 本地通知与中文日报。上游源码和独立虚拟环境留本地，本仓库只提供提交锁定清单。

| 能力 | 真实状态 | 实现与边界 |
|---|---|---|
| 公开发现 | 已实现、有真实运行 | `collector.py`：RSS、HTML anchor、HN API；公开访问失败保持 FAILED/PAUSED/SKIPPED |
| 信息筛选 | 已实现、有限回归通过 | 中英词边界、trial公告、品牌上下文、金额credits、专用优惠码、免费服务 CTA；不是 LLM 或完备语义判别 |
| 原始样本 | 已实现、有现场样本 | `public_corpus.py` 同一次采集保留未命中条目；公开来源限定、500行/8MB、脱敏/截断标记；不是全平台分母 |
| 真实性与官方证据 | 部分实现 | 受限白名单追踪和人工正常浏览器复核；社区外链只作 reference；没有通用自动官方搜索与完整资格抽取 |
| 去重 | 已实现、回归及有限真实案例通过 | URL追踪参数、规范标题、规格数字、共同来源；经复核的 Gleam campaign 身份；全量95%未验 |
| 新批次 | 部分实现 | 官方明确 batch/round/第N批及紧邻年份；没有泛化重新开放识别 |
| 分类 | 已实现状态分类 | 九状态；报告按状态和元数据分区。没有完备福利主题分类器 |
| 优先级 | 仅有展示入口 | 报告读取 `metadata.high_value`；没有已验证自动打分/排序系统，不能把“高价值”章节当评分功能完成 |
| 简报 | 已实现、有文件核验 | MD/JSON、first_seen与published分开、CLAIMABLE报告时重验；可能仍展示历史噪声 |
| 通知 | 本地已实现及测试 | 持久队列、去重、lease、重试、新鲜度；Telegram关闭，真实远程投递未验 |
| 调度/日志/运维 | 本地已实现、有限现场验证 | 六个任务、轮转、诊断、公开配置恢复、隔离SQLite恢复；物理重启/休眠/全栈灾备未验 |

九状态：DISCOVERED、CROSS_CHECKED、OFFICIAL_VERIFIED、CLAIMABLE、UNKNOWN、CONFLICTED、EXPIRED、FAILED、REDEEMED。只有新鲜官方证据支持 open/public 时才可能给公开申请范围；当前实现不能证明个人账户资格。`OFFICIAL_VERIFIED` 是来源确认，不是“有效优惠”或“可领取”。

## 五个上游

| 上游 | 安装/验证 | 不得冒充完成的部分 |
|---|---|---|
| Twitter Monitor | 独立venv及Playwright；自有专用Chrome只读桥接及保护测试 | 原LangGraph/LLM完整运行、登录、推荐/关注/搜索实际采集未验 |
| OpenMagpie | CLI 0.8.0 help；独立后端依赖安装、安全更新、禁网 Django check及7项SSRF/IP测试 | Postgres、模型端点、迁移、Next.js/Web/API、语义监听完整栈未上线 |
| Digest AI Agent | editable安装；UTF-8上游296 passed/1 skipped；真实RSSProvider调用 | 不是全套认证来源或所有LLM工作流已验 |
| ClawRadar | 原单文件编译/help；自有应用只读OAuth及公共热门RSS | OAuth未启用、真实app/API未验；匿名JSON/bird不启用 |
| Linux.do reference | 原userscript纯函数4项通过 | 不是服务端采集器；点赞、刷阅读/积分、反调试等不执行；自有只读节点另建 |

版本与许可证见 `UPSTREAMS.json`。不复制上游 `.git`、vendored源码或第三方环境，避免把来源审计与运行成功混为一谈。

## 环境与决策

10月11日安装审计：Windows11 Home build26200、Python3.14.5、Node26.3/npm12、PowerShell7.6.5；定时链使用系统 Windows PowerShell。版本是当日记录，不是远程 CI 实测。生产根固定 `C:\WoolRadar`，不是跨平台一键安装发行版。

OpenMagpie明确需要 Postgres/MVCC，**不以核心 SQLite 替代上游数据库**。Docker/WSL安装未批准且未执行。10月14日查证官方 Windows ZIP 可作为项目级替代，16.15匹配上游compose的16大版本；下载等待超时/内核重置，无成功下载或安装证据，不重下或宣称数据库已启动。

核心不需要模型推理。上游模型服务尚未建立；不读取其他应用配置或擅用外部API密钥。全局代理、DNS、权限、日常浏览器、设备均未改动。

来源、历史、验收、文件索引及下一步分别见 `SOURCE_STATUS.md`、`ITERATION_HISTORY.md`、`EVALUATION.md`、`ARTIFACT_INDEX.md`、`HANDOFF.md`。浏览器争议单列 `BROWSER_NETWORK.md`。
