# WoolRadar（羊毛雷达）

Windows本地长期项目的非敏感代码与Agent交接快照。**整体未验收完成**；这是对现有成果的安全同步，非重新开发。

从 [AGENT_BRIEFING.md](AGENT_BRIEFING.md) 和 [HANDOFF.md](HANDOFF.md) 开始阅读。真实来源状态、迭代、验收及文件索引分别见 [SOURCE_STATUS.md](SOURCE_STATUS.md)、[ITERATION_HISTORY.md](ITERATION_HISTORY.md)、[EVALUATION.md](EVALUATION.md)、[ARTIFACT_INDEX.md](ARTIFACT_INDEX.md)；浏览器问题单列 [BROWSER_NETWORK.md](BROWSER_NETWORK.md)。

包含自有core、五个适配入口、Windows脚本、测试定义和无密钥配置示例；不包含第三方上游源码/历史、浏览器资料、凭据、数据库、日志、缓存、虚拟环境或大样本。上游版本见 `UPSTREAMS.json`。

生产10月14日148项测试通过，有限真实采集/调度/报告有证据；这些不等同完整五上游运行、19平台全覆盖、95%真实指标、个人资格或Telegram投递。快照自己的实际测试结果在 `evidence/SYNC_VALIDATION.json`，不可用生产成绩代替。

本仓库不是已完成的跨平台安装器。生产脚本固定 `C:\WoolRadar`；远端审查请先读 [EVALUATION.md](EVALUATION.md)，避免执行启停/注册/卸载脚本。仓库原骨架历史保留，变更通过独立分支与PR审查，不自动合并。
