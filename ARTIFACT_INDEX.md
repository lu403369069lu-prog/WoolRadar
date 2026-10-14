---
type: artifact-index
date: 2026-10-14
tags: [WoolRadar, index]
---
# 可审查文件及本地资产索引

## 共享内容

| 位置 | 内容 | 状态/使用方法 |
|---|---|---|
| 根目录六份交接文档 | 背景、来源、迭代、评估、索引、交接 | 根据历史和现状重新归纳，不上传原始聊天 |
| `BROWSER_NETWORK.md` | 单独区分控制通道/本地HTTP/Work/历史云端/认证 | 观测和推测明确分开 |
| `UPSTREAMS.json` | 五个上游repo/commit/安装时许可证 | 原上游源码和.git不复制，不是完整安装器 |
| `core/*.py` | 自有规则/预算/SQLite/采集/核验/去重/通知/报告/诊断 | 当前生产源码快照，UTF8规范化；不是已验证全栈 |
| `nodes/run_node.py`、五个node入口 | 独立入口及共用调用层 | 需要本地source配置；节点名包含连字符 |
| `nodes/digest-ai-agent/rss_collect.py` | 调用原RSSProvider的进程桥接 | 依赖本地原上游安装，不提供第三方环境 |
| `nodes/twitter-monitor/browser_collect.py` | 专用Chrome/CDP只读桥接 | 当前禁用，不读默认profile，不证明真实登录 |
| `config/*` | 21source/19platform公开endpoint、关键词、安全默认关闭、官方trace、专用X参数 | 没有密钥；sources.yaml内容是JSON，加载器不接受任意YAML |
| 两个 `credentials.*.example.json` | Reddit应用只读/refresh模板 | 全部FILL_LOCALLY/YOUR占位，实际credentials.json不共享 |
| `tests/*.py`、`tests/fixtures/known-cases.json` | 固定回归定义及明确未验的案例 | 复验边界见EVALUATION，不运行真实账户或设备 |
| `scripts/*.ps1/*.py/*.cs` | Windows启停/注册/诊断/回滚/卸载/报告、GUI启动器源码、后台Python | 固定C:\WoolRadar，运行工具有副作用；只读审查不执行部署 |
| `evidence/SYNC_EVIDENCE.json` | 脱敏选定生产输出、来源状态、官方复核摘要及原证据指纹 | 原始完整输出留本地，日期保持历史 |
| `evidence/SYNC_VALIDATION.json` | 本次快照实跑命令/exit/pass/skip | 与生产148结果分别记录 |
| `evidence/SNAPSHOT_MANIFEST.json` | 共享文件清单（路径/大小/SHA256）与规范化说明 | 用于核GitHub树/本地快照一致；不含个人工作区路径 |
| `evidence/SHARING_AUDIT.json` | 文件/大小/敏感模式/模板检查结果、排除资产类别 | 自动扫描加人工审查，不承诺绝对没有任何未知秘密 |

README/HANDOFF替换原占位内容；原main提交仍保留。远端AGENTS.md保持原文，无项目状态写入其中。`.gitignore`在原规则上增加本地状态/上游/下载物排除；白名单和扫描比ignore更重要。

## 保留本地且不上传

| 资产 | 原因 |
|---|---|
| `data/woolradar.db`、WAL、request-budget、备份DB | 包含活动/证据/状态/通知与运行记录；动态数据、过大/可能含个人关联；只共享聚合状态 |
| `data/inbox`、`data/public-corpus`、329/40/后续完整样本 | 可能带公共作者/正文、敏感查询或噪声；只是有界采样，不作为默认全量上传；测试仅有必要小文本 |
| `reports`、`logs`、原XML/截图/原始_outbox | 日常运行及个人环境路径/账号现场/错误内容；共享整理后的结论和结果指纹 |
| `credentials.json`、.env、Cookie、token、Google会话/profile | 敏感认证信息，不读取以便上传，不导出、不迁移 |
| 五个upstream源码/.git、venv/node_modules、第三方轮包/Twikit材料 | 第三方历史/环境/体积/许可范围；留原本机，UPSTREAMS锁定来源 |
| `.codex`、原始rollout/记忆/Stop契约/会话ID、其他工程 | 私有对话和运行控制资产，非远端源码/文档授权范围 |
| Run-Hidden.exe/DLL/ZIP/编译缓存/Postgres下载 | 二进制/下载物未共享；C#源码可审查，安装和实际文件需本地验证 |

本地证据定位（只列逻辑文件名）：安装审计/验收记录；`lowend-cues-deployment-20261014.json`、`hidden-task-fix-20261014/{migration,verification}.json`、`public-corpus-live-20261014.json`、`directory-scope-deployment-20261014.json`、官方三份review/import-proof、`backend-package-advisories.json`、`openmagpie-backend-readiness.json`、历史browser-environment/known-post/RSS探针和save/continuity文档。

完整文件枚举及大小不在正文硬编码，见SNAPSHOT_MANIFEST。共享快照不覆盖或移动原生产目录；上游历史和持续任务保留。
