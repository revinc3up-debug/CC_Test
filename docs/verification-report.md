# 信源获取验证报告

> 目标（/goal）：**本地环境完成资源信息获取的验证，包括微信搜索和小红书检索**。
> 验证工具：`examples/sourcing/verify_sources.py`（可复现，走防封门控，仅标准库）。
> 报告日期：2026-07-03。

---

## 1. 结论速览

| 验证项 | 本 Claude Code 云端环境 | 你的本地/国内环境（待你执行） |
|--------|------------------------|------------------------------|
| 验证工具本身可运行 | ✅ 已跑通（114/114 测试通过） | ✅ 同一脚本 |
| 原生 RSS（36氪/虎嗅/IT之家…） | 🚫 BLOCKED（网络策略） | 预期 ✅ PASS |
| **微信搜索**（搜狗微信） | 🚫 BLOCKED（网络策略） | 需你本地执行 → 预期 ✅ |
| **小红书检索**（xiaohongshu-mcp） | ➖ SKIP（服务未起） | 需你本地起服务并登录 → 预期 ✅ |
| 自建 DailyHotApi/RSSHub | ➖ SKIP（未部署） | 起容器后 ✅ |

**一句话**：验证**机制已完成并跑通**；但**实时数据获取（微信搜索/小红书检索）无法在这个云容器里完成**，
因为环境网络策略在网关层直接拒绝了所有国内站点。必须在你本地/国内网络跑同一个脚本才能拿到真 PASS。

## 2. 为什么云端跑不了：硬证据

云端出口经 agent proxy，网关对目标站**在 CONNECT 阶段直接 403 拒绝**（非反爬、非我方代码问题）。
`curl "$HTTPS_PROXY/__agentproxy/status"` 实测到的拒绝记录：

```
connect_rejected  gateway answered 403 to CONNECT (policy denial)  host=36kr.com:443
connect_rejected  gateway answered 403 to CONNECT (policy denial)  host=weixin.sogou.com:443
connect_rejected  gateway answered 403 to CONNECT (policy denial)  host=www.xiaohongshu.com:443
connect_rejected  gateway answered 403 to CONNECT (policy denial)  host=rsshub.app:443
```

白名单只含 pypi/npm/anthropic 等，国内资讯站一律不放行。这与本任务一路上遇到的 403 同因。

## 3. 验证工具跑通证据（本环境）

`python examples/sourcing/verify_sources.py` 在本环境的真实输出（如实分类，未粉饰）：

```
▍RSS
  🚫 BLOCKED 36氪·快讯    连接失败：Tunnel connection failed: 403 Forbidden
  ... （虎嗅/钛媒体/IT之家/少数派/爱范儿 同为 BLOCKED）
▍微信搜索
  🚫 BLOCKED 微信搜索(搜狗)  连接失败：Tunnel connection failed: 403 Forbidden
▍小红书检索
  ➖ SKIP    小红书检索(xiaohongshu-mcp)  未检测到 127.0.0.1:18060 上的 MCP 服务
▍自建服务
  ➖ SKIP    DailyHotApi(:6688) / RSSHub(:1200)  未启动或不可达
```

脚本逻辑本身由 `tests/test_verify_sources.py`（9 项）保证：RSS 解析、验证码检测、
403→BLOCKED、本地 refused→SKIP、小红书端口探测等分支全部覆盖并通过。

## 4. 在你本地完成验证：三步

> 前置：本地/国内网络；已装 Docker、Python 3.10+、[uv](https://github.com/astral-sh/uv)。

### 步骤 1 — 原生 RSS + 微信搜索（无需起服务，直接验证）
```bash
python examples/sourcing/verify_sources.py --only rss,wechat --query "腾讯 组织架构"
```
预期：RSS 各源 ✅ PASS 并打印最新一条标题+时间；**微信搜索** ✅ PASS（命中搜狗结果容器）。
若微信搜索 BLOCKED（撞验证码）→ 说明频率过高，等一会儿或换 IP，防封门控就是干这个的。

### 步骤 2 — 小红书检索（起 MCP 服务 + 登录小号）
```bash
# 1) 启动并登录（详见 docs/local-deployment.md §2.1）
./xiaohongshu-login-<平台>       # 扫码登录小红书小号
./xiaohongshu-mcp-<平台>         # 启动 MCP，默认 :18060
# 2) 探测服务就绪
python examples/sourcing/verify_sources.py --only xhs
# 3) 真·关键词检索（由 Claude 通过 MCP 调 search 工具确认登录态与返回）
claude mcp add --transport http xiaohongshu-mcp http://localhost:18060/mcp
#    然后让 Claude：用 xiaohongshu-mcp 搜索"字节 裁员"，返回前 5 条笔记标题
```
预期：`--only xhs` 报 ✅ PASS（服务在线）；Claude 侧 MCP 检索返回真实笔记 → 小红书检索验证完成。

### 步骤 3 — 自建聚合服务（可选，快讯拼盘用）
```bash
cd examples/sourcing && docker compose up -d
python ../../examples/sourcing/verify_sources.py --only local
```
预期：DailyHotApi(:6688)、RSSHub(:1200) 均 ✅ PASS。

### 全量一把过
```bash
python examples/sourcing/verify_sources.py           # 全部；退出码 0 = 无 FAIL
```

## 5. 验收标准（本地跑到这个状态即算"资源获取验证通过"）

- [ ] 原生 RSS：≥5 个源 PASS 且能打印最新条目（时效正常）
- [ ] **微信搜索**：搜狗微信关键词检索 PASS，返回结果非验证码页
- [ ] **小红书检索**：xiaohongshu-mcp 服务 PASS，且 Claude 经 MCP 能搜到真实笔记
- [ ] 自建服务（如已部署）：DailyHotApi/RSSHub PASS
- [ ] 全量运行退出码为 0

达成后即可按档 A（有联网检索）正式产出《大厂茶水间》样刊。
