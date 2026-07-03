# 《大厂茶水间》信源管线 · 本地部署指南

> 策略：**本地部署优先，之后再平移到云端 VPS**。
> 本地机器在国内网络环境下运行，天然绕开了云端环境实测到的 403 问题
> （详见 `docs/wechat-column-sourcing.md` 第 2 节）。
> 部署命令均核实自各项目 README（2026-07-03）。

## 0. 前置条件

- Docker + Docker Compose
- Python 3.10+ 与 [uv](https://github.com/astral-sh/uv)（提供 `uvx`，跑两个 MCP server 用）
- 本地 Claude Code / Claude Desktop（写作 Agent 宿主）
- 两个"工具小号"：微信（we-mp-rss 扫码授权）、小红书（xiaohongshu-mcp 登录）

## 1. Docker 三件套（快讯基线 + 公众号订阅）

配置文件：`examples/sourcing/docker-compose.yml`

```bash
cd examples/sourcing
docker compose up -d
```

| 服务 | 端口 | 用途 | 验证方式 |
|------|------|------|---------|
| DailyHotApi | 6688 | 聚合热榜（36氪/微博/知乎/IT之家…） | `curl http://localhost:6688/36kr` |
| RSSHub | 1200 | 快讯 RSS 路由 | `curl http://localhost:1200/36kr/newsflashes` |
| we-mp-rss | 8001 | 公众号订阅 → RSS/API/Webhook | 浏览器打开 `http://localhost:8001` |

**we-mp-rss 初始化**（一次性）：
1. 打开 `http://localhost:8001`，用微信小号扫码授权；
2. 添加订阅：晚点LatePost、36氪、界面新闻、财新网、Tech星球、雷峰网、量子位；
3. 添加频率放慢（每次间隔几分钟），避免触发微信侧封控；
4. 订阅数据在 `./data/we-mp-rss/`，**迁移云端时整个目录带走即可保留授权与订阅**。

## 2. MCP 三件套（关键词交叉验证层）

### 2.1 xiaohongshu-mcp（需先登录，HTTP 方式接入）

```bash
# 方式一：Docker
docker pull xpzouying/xiaohongshu-mcp
# 按仓库 docker/ 目录的 compose 启动

# 方式二：二进制（以 macOS ARM 为例，其他平台在 Releases 下载对应产物）
./xiaohongshu-login-darwin-arm64   # 先跑登录工具，扫码登录小红书小号
./xiaohongshu-mcp-darwin-arm64     # 再启动 MCP 服务，默认端口 18060
```

登录态存在本地 cookies 文件；**同一账号不可同时在其他网页端登录**，否则 MCP 掉线。

### 2.2 接入 Claude Code

```bash
claude mcp add --transport http xiaohongshu-mcp http://localhost:18060/mcp
claude mcp add sogou-weixin -- uvx --from git+https://github.com/ptbsare/sogou-weixin-mcp-server.git sogou-weixin-mcp-server
claude mcp add weibo -- uvx mcp-server-weibo
claude mcp list   # 确认三个都是 connected
```

Claude Desktop / 其他 MCP 客户端用配置文件方式：见 `examples/sourcing/mcp.json.example`。

微博 MCP 提供 `get_trendings()`（热搜榜）、`search_content()`（内容搜索）、
`search_topics()`（话题）等工具；搜狗微信 MCP 返回 title/snippet/url/公众号名/日期。

## 3. 每晚写作流（21:00 发布倒推）

```
20:00  拉取第一层：curl DailyHotApi(36kr/weibo/ithome) + RSSHub 快讯
       拉取第二层：we-mp-rss 各订阅号当日新文章
20:15  选头瓜/人事雷达候选 → 第三层逐条交叉验证：
       sogou-weixin 搜公众号原文（找🟢官宣/🟡权威媒体）
       weibo search_content 找独立信源（人事类须凑齐 2 个）
       xiaohongshu 搜风声（只进🔴"茶水间风声"板块）
20:40  按栏目 Prompt 生成样刊（档A，随文记录来源＋日期）
20:50  发布前自查清单（每条有出处？具名任免有信源？传闻挂标签？）
21:00  发布
```

## 4. 频率与风控（本地同样适用）

**每次对外请求前先过防封门控** `framework/sourcing_gate.py`（阈值见
`examples/sourcing/anti_ban_gate.yaml`，各平台封控机制与门控设计详见 `docs/anti-ban-gate.md`）：

```python
from framework.sourcing_gate import SourcingGate
gate = SourcingGate.from_yaml("examples/sourcing/anti_ban_gate.yaml")
d = gate.acquire("xiaohongshu")
if d.allowed:
    if d.wait_seconds: time.sleep(d.wait_seconds)
    ...  # 发请求；成功 gate.report_success()，被封 gate.report_block()
else:
    ...  # 冷却/配额耗尽 → 跳过并降级该板块
```

配套人肉纪律：
- 搜狗/微博/小红书接口均无官方授权：**每天 1~2 轮拉取足够**，结果落盘缓存，别循环重试；
- 所有登录态一律小号；主号不碰任何工具；小红书登录 MCP 后勿多端在线；
- DailyHotApi 自带 60 分钟缓存，不必反复请求；
- **优先订阅资讯号 + 独立站**（大厂日爆、大厂青年、晚点、Tech星球…），少直连搜索接口；
- 某路信源挂了就按栏目规则降级（板块可删、条数可减），**宁缺毋滥**。

## 5. 之后迁移云端的路径

1. 选国内或香港 VPS（境外机房已实测被搜狗/微博/RSSHub 源站 403）；
2. `docker-compose.yml` 原样上传，`./data/` 目录整体迁移（保留 we-mp-rss 授权、
   xiaohongshu cookies）；
3. 三个服务端口只绑内网/加反代鉴权，不要裸露公网；
4. 本地 Claude Code 的 MCP 配置把 `localhost` 换成 VPS 内网地址（或走 SSH 隧道）；
5. 用 cron / 框架的定时任务在 VPS 上做 20:00 的两层预拉取，写作时直接读缓存。
