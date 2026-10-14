---
type: evaluation
date: 2026-10-14
tags: [WoolRadar, tests, acceptance]
---
# 测试与真实验收

状态词：**已实现**指代码存在；**测试通过**指有命令输出；**现场通过**只覆盖实跑场景；**部分实现/未验证**不因清单或测试方法存在而变成完成。

## 有证据的结果

| 项目 | 结果、日期 | 实际覆盖/限制 |
|---|---|---|
| 生产核心unittest | 10月14日148项、exit0、OK；原输出在lowend-cues-deployment回执 | 规则、预算、重定向、状态、资格、去重、通知、采样、Windows包装器等固定回归；不是全面语义准确率 |
| 本次共享快照 | 单独验证结果写入 `evidence/SYNC_VALIDATION.json` | 请读实际exit/skip数；不能自动等同生产或Linux结果 |
| Digest原上游 | 10月11日UTF8：296 passed/1 skipped | 历史原上游测试；不是本次同步重新执行；GBK失败被保留 |
| Linuxdo原上游 | 4个纯函数测试pass | 不执行浏览器userscript点赞/积分；不证明Linux.do抓取成功 |
| OpenMagpie backend | 10月12日pipcheck0、禁网Django check0但ENGINE_MODEL警告、7SSRF/IP测试pass | 没有数据库迁移、模型调用、Web/API运行或完整集成通过证据 |
| PyPI审计 | 三环境pip问题修正及独立backend7包安全覆盖 | 只针对当日已安装发布包及已知advisory；editable、未安装Node环境和恶意源码不涵盖 |
| 六隐藏任务 | 10月14日01:35Z实际6新运行exit0、Ready、launcher/PS/Python consolefalse；PID对应 | Triggers/Principals/Settings/Description前后不变；不能扩大到长期每次GUI观测或源头成功 |
| 数据库 | 同步快照105记录、quick_check=ok | 1EXPIRED/19OFFICIAL_VERIFIED/85UNKNOWN、0CLAIMABLE是该时刻状态；运行继续，数量会改变 |
| 报告 | 10月14日10:01Z MD/JSON103记录与当时DB一致 | 后来同步快照105是调度新增，不是矛盾；短简报与日常原始日报不同，历史噪声保留 |
| 恢复/运维 | 历史公开配置同内容真实恢复指纹一致；隔离DB恢复integrity及计数一致；卸载WhatIf保持任务 | 没有实际卸载在线系统、物理重启/休眠、生产DB灾难切换或完整栈回滚 |

最新生成证据的时间和文件SHA见 `evidence/SYNC_EVIDENCE.json`、`evidence/SNAPSHOT_MANIFEST.json`。共享摘要只保留非敏感结果；完整DB、日志、XML和账号相关现场保留本地。

## 实际样本，不冒充指标

- 第一轮：Cloudflare20、ProductHunt50、DevHunt259，共329原始条目。人工读70条RSS摘要，DevHunt目录回放。Cloudflare金额credits漏报修复；DevHunt3条导航误命中排除、外部Gemini定价线索保留。
- 第二轮：HN20、LowEndBox20。6条明确coupon/free/giveaway线索，原命中4，修复后回放6。3条只有付费价格的范围尚未裁定；HN仅标题/摘要不能排除原页另有权益。
- 这些样本用于发现与拟合修正，**不是独立留出集**。不可宣称总体召回≥95%、准确率100%或所有原始条目都是优惠。真实95%仍需明确总体/时间窗、完整分母、独立标签和去重真值。
- 旧三条Reddit技术求助/开源介绍噪声用原完整正文离线回放拒绝；原库不删除，不称为本次新联网成功。
- 同Gleam Isp30两稿真实归组，Halloween不同ID保留；只是有限去重案例，不是95%数据集。

## 原始案例与未达标准

`tests/fixtures/known-cases.json` 明确记录：RackNerd主办方原帖已复核但当前开放未知；MLH是Cursor/Grok讲座而freePro未证；Reddit UptimeRobot精确permalink未知；Linux.do同类样本正文超时且不认定等同用户原案例。这不是四例全部通过。

未完成：五上游完整功能、19平台实际全覆盖、真实回查/召回/去重≥95%、完整资格证据、个人账户准入、Telegram真实投递、物理恢复/长稳、用户整体验收。Reddit应用认证必经验收已取消，其他标准未擅自取消。

## 安全复验

共享核心主要为stdlib，Python3.11+语法；该兼容范围不是全部版本实测。Windows特定测试依赖PowerShell，Digest跨进程测试依赖本地原上游环境；远程缺环境时须报告skip/失败，不安装系统组件来伪造pass。

```text
python -X utf8 -m unittest discover -s tests
```

测试使用临时目录/MockTransport，不需要真实平台密钥。**不要为了审查执行Start/Stop/Register/Uninstall/trace-official/capture-evidence生产脚本**；这些是运行工具，固定生产根或有状态/网络副作用。没有CI工作流自动部署本机，尚未建立远程全栈运行环境。

建议ChatGPT审查：否定/请求/量价混淆的新语义边界；真实留出集设计；不同campaign/年度/转载的去重误合并；官方来源与资格条件的分离；隐藏启动链异常清理；共享文件与敏感边界。只有可重现反例和具体修正证据才升级结论。
