---
type: source-status
date: 2026-10-14
tags: [WoolRadar, sources]
---
# 信息源真实状态

快照：2026-10-14T15:20:12.165098+00:00。21个来源配置覆盖19个配置平台；下面列出每个source ID，不把配置、成功进程退出、预算跳过或HTTP成功当福利/资格完成。后续状态可能变化。

| 来源ID / 节点 | 方法 / 授权 | 最新实际状态与时间UTC | 历史验证、限制及待验 |
|---|---|---|---|
| [x-browser](https://x.com/home) / twitter-monitor | browser / manual_browser_login; enabled=False | SKIPPED/SOURCE_DISABLED; 2026-10-14T15:08:53Z; Disabled by configuration; no request attempted | Dedicated adapter/guard tests; no authenticated live search or feeds. User Chrome login reported, node disabled. |
| [reddit-oauth](https://oauth.reddit.com/search) / clawradar | reddit_oauth / oauth_required; enabled=False | SKIPPED/SOURCE_DISABLED; 2026-10-14T15:08:54Z; Disabled by configuration; no request attempted | Application-only/refresh code mock-tested; no live app request; required verification cancelled Oct13. |
| [reddit-hot-rss](https://www.reddit.com/r/freebies+vps+webhosting/hot/.rss) / clawradar | rss / public_feed; enabled=True | OK; 2026-10-14T15:08:54Z; fetched=25;sampled=25 | Public hotRSS25 read on Oct12/13/14, technical-topic/path filtering; zero matches is valid success. |
| [reddit-rss](https://www.reddit.com/r/freebies+vps+webhosting/new/.rss) / digest-ai-agent | rss / public_feed; enabled=True | SKIPPED/REQUEST_BUDGET; 2026-10-14T12:00:01Z;  | Upstream Digest RSSProvider real publicRSS25 historical success; shares reddit host budget. |
| [linuxdo](https://linux.do/latest.rss) / linuxdo-monitor | rss / public_feed; enabled=True | PAUSED/BLOCKED_403; 2026-10-14T15:09:35Z;  | Sample located, body timeout earlier; now persisted403 pause. Exact user original case unverified. |
| [nodeseek](https://rss.nodeseek.com) / linuxdo-monitor | rss / public_feed; enabled=True | FAILED/NETWORK_TIMEOUT; 2026-10-14T15:09:35Z; <urlopen error timed out> | Historical and latest network timeouts; no successful current live acceptance. |
| [v2ex](https://www.v2ex.com/index.xml) / linuxdo-monitor | rss / public_feed; enabled=True | PAUSED/CAPTCHA_REQUIRED; 2026-10-14T15:09:35Z;  | HistoricalRSS50 success; later CAPTCHA pause; not current full availability. |
| [lowendtalk-giveaways](https://lowendtalk.com/categories/giveaways-freebies/feed.rss) / linuxdo-monitor | rss / public_feed; enabled=True | PAUSED/BLOCKED_403; 2026-10-14T15:09:35Z;  | Historical page100 anchors and organizer case read; later403 pause; no bypass. |
| [lowendbox](https://lowendbox.com/feed/) / linuxdo-monitor | rss / public_feed; enabled=True | OK; 2026-10-14T15:09:35Z; fetched=20;sampled=20 | RSS20 live, known giveaways plus coupon/free backup misses fixed through offline replay. |
| [hostloc](https://hostloc.com/forum.php?mod=rss) / linuxdo-monitor | rss / public_feed; enabled=True | FAILED/NETWORK_TIMEOUT; 2026-10-14T15:09:35Z; <urlopen error timed out> | Timeouts and transient DNS failure; no success inferred. |
| [hackernews](https://hacker-news.firebaseio.com/v0/newstories.json) / openmagpie | hn_api / public_api; enabled=True | SKIPPED/REQUEST_BUDGET; 2026-10-14T15:08:54Z;  | PublicAPI20 item checkpoint/budget; real samples saved; skip is not success. |
| [producthunt](https://www.producthunt.com/feed) / openmagpie | rss / public_feed; enabled=True | OK; 2026-10-14T15:08:54Z; fetched=50;sampled=50 | PublicRSS50 live multiple rounds; many product launches are not offers. |
| [devhunt](https://devhunt.org/perks) / openmagpie | html / public_page; enabled=True | SKIPPED/REQUEST_BUDGET; 2026-10-14T15:08:54Z;  | Perks page259 anchors; exclude own host navigation; externalGemini kept; otherprogram recall unresolved. |
| [freestuff](https://freestuff.dev/) / openmagpie | html / public_page; enabled=True | PAUSED/CAPTCHA_REQUIRED; 2026-10-14T15:08:54Z;  | Challenge pause; no authenticated or bypass integration. |
| [free-for-dev](https://github.com/ripienaar/free-for-dev/commits/master.atom) / digest-ai-agent | rss / public_feed; enabled=True | SKIPPED/REQUEST_BUDGET; 2026-10-14T12:00:01Z;  | Historical publicGitHub commitfeed20 via deployed RSS collector; commit headlines are not all directory resources. |
| [github-education](https://github.blog/tag/github-education/feed/) / openmagpie | rss / public_feed; enabled=True | SKIPPED/REQUEST_BUDGET; 2026-10-14T15:08:54Z;  | Official publicblog RSS; historical retrieval, current budget skip; individual student eligibility unknown. |
| [mlh](https://news.mlh.io/feed) / openmagpie | rss / public_feed; enabled=True | SKIPPED/REQUEST_BUDGET; 2026-10-14T15:08:54Z;  | Official feed12 plus limited official trace/manual prize pages; lecture is not freePro; conditions partial. |
| [google-cloud](https://cloud.google.com/blog/topics/inside-google-cloud/whats-new-google-cloud) / digest-ai-agent | html / public_page; enabled=True | PAUSED/CAPTCHA_REQUIRED; 2026-10-14T12:00:01Z;  | HTML strategy/config exists; challenge pause. No sourcefull retrieval success from page snapshot. |
| [aws](https://aws.amazon.com/about-aws/whats-new/recent/feed/) / digest-ai-agent | rss / public_feed; enabled=True | SKIPPED/REQUEST_BUDGET; 2026-10-14T12:00:01Z;  | Historical officialRSS100 read; current skip, no newestfull eligibility or benefits coverage. |
| [cursor](https://www.cursor.com/changelog) / openmagpie | html / public_page; enabled=True | SKIPPED/REQUEST_BUDGET; 2026-10-14T15:08:54Z;  | Changelog publicHTML/host/path scope; historical limited read; no CursorPro entitlement proof. |
| [cloudflare-dev](https://blog.cloudflare.com/tag/developers/rss/) / digest-ai-agent | rss / public_feed; enabled=True | SKIPPED/REQUEST_BUDGET; 2026-10-14T12:00:01Z;  | Historical/new officialRSS20, monetarycredits miss fixed; ColdStart deadline closed from browser正文. |

## 含义与边界

OK表示该次实际source请求/解析成功，items是匹配候选数；SKIPPED表示未请求（禁用或预算），PAUSED保留屏障，FAILED保留网络/解析原因。零候选可以是真实读取成功；只有退出0不够。

公开收集不依赖Google token；账号源默认关闭。19平台仍未真实全覆盖，暂停来源不清记录或force绕过。普通网络失败下一允许扫描恢复；403/CAPTCHA持久暂停，429按退避；同host公共源之间共享预算。

## 官方补证（不是独立采集平台配置）

| 公开页面 | 已证事实 | 当前结论 |
|---|---|---|
| RackNerd×AdminBolt主办方原帖 | 100VPS一年/20licenses总量；同源转载不算独立；当前开放/名额未知 | OFFICIAL_VERIFIED，非可领取 |
| MLH活动/奖品页 | Cursor/Grok赞助讲座成立，freeCursorPro未证；Vultr金额未知、DO需Coach | 来源确认/条件待核 |
| MongoDB学生额度 | 厂商50美元依赖GitHub学生包；免费层nocard不外推 | 个人资格、额度有效/开放未知 |
| Auth0厂商定价 | B2C25000月活/0美元、注册nocard；自定义域名需卡，MLH旧7000保留差异 | 当前产品页条件，个人资格未知 |
| CloudflareColdStart | 美国/加拿大、融资<1000万美元，一名赢家50万美元credits；申请10月2日截止 | EXPIRED/NONE；10月19日是比赛 |
| GeminiAPI价格 | 官方英文免费层存在、部分模型、内容改进产品；地区页ServiceUnavailable | OFFICIAL_VERIFIED/NONE；账号/区域/配额未知 |
| ServerCrate价格 | 官方10GB/2设备/7天历史/nocard/不过期；社区旧1设备不用作现行条件 | OFFICIAL_VERIFIED/NONE；完整条款/个人准入/服务质量未验 |

## 研究但未当作接入成功

GitHub MCP读过XDK/PRAW/Twikit/twscrape/RSSHub/Nitter/ReactTweet及官方X API文档。Nitter当时archived；Cookie/token路线未采用；官方开发者权限/费用没有因为SDK可用而消失。Twikit固定源码只用于隔离后端依赖补齐，没有X登录。X已知公开帖1条探针没有搜索能力。

Reddit申请字段准备后遇验证码/协议门槛，未提交。用户取消必经验证，不再要求操作；保存草稿不是创建成功。浏览器与认证详见BROWSER_NETWORK.md。
