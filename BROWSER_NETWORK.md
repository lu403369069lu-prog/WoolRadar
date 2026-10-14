---
type: technical-evidence
date: 2026-10-14
tags: [WoolRadar, browser, network]
---
# 浏览器、网络与认证：已证实与未知

此文依据10月11日至14日实际工具结果、历史证据及用户指令；没有 Cookie、token、浏览器配置、个人邮箱或会话ID。不同执行路径的结果不能互相替代。

## 环境区别

| 路径 | 实际观察 | 不能推断 |
|---|---|---|
| 用户日常Chrome | 用户报告Google及X/Reddit登录；10月12日工具曾恢复，实际看到Reddit prefs/apps登录页并填准备字段 | 不能据此认定X API/Reddit开发者权限存在；X登录主要仍是用户报告 |
| Codex真实Chrome控制 | 多次 `Unable to load browser request-header policy`；一次带 `ab.chatgpt.com` ENOTFOUND；后来短暂可用，再次失败 | 不是网站拒绝账号的证据；不能断言全机DNS故障或具体策略规则 |
| Codex本地受限命令 | DNS查询曾 ACCESS_DENIED；批准主机上下文能解析控制域、X、Reddit | 权限差异已证实，但具体网络实现/策略责任层未查明 |
| 生产HTTP采集进程 | RSS/HN等真实成功；另一些时刻 `getaddrinfo failed`、超时、403或挑战；最新RSS可再次成功 | 暂时DNS失败不表示登录失败，也不表示所有来源永久不可用 |
| 本会话Work/IAB | 曾X注册/控制台跳转、超时或page crashed；后续Google及公开官方页可读，10月14日Cloudflare/Gemini/ServerCrate正文成功 | 不能把IAB称为已证实的远端云浏览器，不能由Google页面登录认定其共享日常Chrome所有会话 |
| 另一个Work云端任务 | 历史其他Agent回报能看到X主页但未登录成功，后又报告超时；父任务未独立复现全部状态 | 不是当前本地X认证修复；不是注册成功或API权限证明 |

工具/执行器/站点/身份的边界需分别测量。“Google连接了”目前只证明存在连接能力；可见Gmail工具不提供X/Reddit API token代理能力，未读取邮件或验证码。站点OAuth和开发者API权限须各自验证。

## 故障分类与原因确定程度

| 现象 | 已确认事实 | 根因确定程度/处理 |
|---|---|---|
| Chrome控制初始化失败 | 错误发生在request-header-policy加载，部分输出带控制域DNS错误 | 具体规则/进程未知；不改永久权限/代理/DNS；用户已允许Work替代做公开读取 |
| Work页面崩溃/空AX/超时 | 控制台曾about:blank/This page crashed，X注册页或控制台无法完成 | 根因未知，不编造成Google账号封锁或X开发者拒绝 |
| 站点403 | Linux.do、LET等响应/持久来源暂停有记录 | 表示该访问路径被拒绝，具体风控原因未知；不清pause强行重试 |
| 验证码/挑战 | 公共页或申请表实际出现相关提示 | 人工/平台门槛；不解题或绕过，不执行FlareSolverr/打码/代理轮换 |
| 网络DNS失败/超时 | 10月14日生产几个来源出现getaddrinfo/超时，其他来源可成功 | 时间和进程相关；没有修改正常用户网络，无“全机DNS已修复”结论 |
| 官方地区页不可用 | Gemini available-regions可见Service Unavailable | 页面故障，地区资格继续未知，不推断用户地域 |
| 下载回执失败 | PostgreSQL16.15官方ZIP点击后的download等待超时并引发CUA内核重置 | 未确认成功文件或安装，也未确认是否浏览器留下下载；续做先检查现场，不重复派发 |

普通登录、公开页面、认证API、API开发者申请是四件不同的事。没有实验验证全部cookie隔离规则；本项目采用不共享/不导出的授权边界，而非凭记忆声称产品底层必然隔离。

## X、Reddit与无需登录的公开方法

- Reddit公共RSS（含热门技术主题）实际多轮读回25条，经过主题/路径过滤；不等于25个福利。最新生产再次OK。公共RSS不证明匿名JSON、OAuth或稳定SLA。
- X已知公开帖的嵌入/公开正文端点在10月12日读回1个示例；没有搜索、推荐、关注流或未知帖发现能力。它是历史有限探针，没有伪装成完整节点接入。
- X官方SDK、PRAW、Twikit、twscrape、RSSHub、Nitter及ReactTweet通过GitHub MCP研究过。SDK不能替代平台授权；Cookie路线因边界未采用，Nitter当时API返回archived。详见历史迭代。
- HN公开API、ProductHunt/RSS、LowEndBox/RSS、Cloudflare/RSS、公开活动/定价页实际有成功记录。成功一次不保证当前全部来源可达。
- Reddit开发者申请仅完成准备，验证码及协议未提交，没有app/token。10月13日用户取消这一必经验收；不再催促或重试注册，取消不写成通过。

没有使用账号绕过、认证信息转移、第三方转发网站或公共代理。GitHub读取使用已连接MCP；本次上传也经此连接，不从浏览器下载私有仓库或复制临时下载token。

本结论的证据入口：`evidence/SYNC_EVIDENCE.json` 中 browser-environment、public-fallback、official-reviews，以及本地证据文件名索引。完整原始会话/截图/日志保留本地，没有复制到仓库。
