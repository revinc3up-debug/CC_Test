# 《大厂茶水间》信源工具调研报告

> 调研日期：2026-07-03 ｜ 调研方式：GitHub 检索 + 当前运行环境实测
> 目标：为公众号日更专栏《大厂茶水间》解决"信息来源"这一最大质量瓶颈，
> 建立可支撑「档A（有联网检索）」写作的信源管线。

---

## 1. 栏目对信源的硬性要求（摘自栏目 Prompt）

| 要求 | 说明 |
|------|------|
| 时效 | 近 24~48 小时的大厂新闻 |
| 三级信源制 | 🟢官宣 / 🟡权威媒体（晚点、36氪、财新、界面）/ 🔴据传网传 |
| 人事类 | 必须 2 个独立信源（转载只算 1 个） |
| 可追溯 | 每条随文记录"来源＋日期"，发布前逐条自查 |
| 板块需求 | 头瓜、人事雷达、快讯拼盘、茶水间风声（传闻区） |

对应到工具选型：需要 **快讯流**（拼盘）、**权威公众号订阅**（🟡级主力）、
**关键词搜索**（交叉验证独立信源）、**社区传闻监测**（🔴级风声）四类能力。

## 2. 当前运行环境实测结论（重要前提）

在 Claude Code 云端环境（境外出口 + agent proxy）于 2026-07-03 实测：

| 信源 | 直连结果 |
|------|---------|
| `rsshub.app` / `rsshub.rssforever.com`（36氪快讯路由） | ❌ 403 |
| 搜狗微信搜索 `weixin.sogou.com` | ❌ 403 |
| DailyHotApi 公共演示实例 `api-hot.imsyy.top` | ❌ DNS 失效 |
| `36kr.com/newsflashes`、今日热榜 `tophub.today` | ❌ 403 |
| Claude 内置 WebSearch | ✅ 可用（能检到中文科技媒体内容，但时效/精度一般） |

**结论：公共实例不可依赖，所有中国信源工具必须自部署（国内或香港 VPS），
再以 MCP / RSS / API 方式喂给写作 Agent。WebSearch 只能作兜底降级。**

## 3. GitHub 工具检索结果与评估

### 3.1 微信公众号搜索 / 订阅（🟡级信源主力）

| 项目 | 形态 | 状态（2026-07） | 评估 |
|------|------|----------------|------|
| [rachelos/we-mp-rss](https://github.com/rachelos/we-mp-rss) | 公众号→RSS/API/Webhook | ✅ 活跃，3.7k★，v1.5.2（2026-04） | **首选**。按公众号订阅晚点/36氪/界面等，支持 Webhook 推送与鉴权；需微信扫码授权，Python+FastAPI，Docker 一键部署 |
| [cooderl/wewe-rss](https://github.com/cooderl/wewe-rss) | 公众号→RSS（基于微信读书） | ⚠️ 9.6k★ 但 **2026-05 已归档停维** | 只读参考，不建议新部署；有"添加频率过高被封控 24h"的前科 |
| [ptbsare/sogou-weixin-mcp-server](https://github.com/ptbsare/sogou-weixin-mcp-server) | MCP（搜狗微信搜索） | 小众（8★），Python 3.10+，uvx 可直接跑 | 关键词搜公众号文章，返回 title/snippet/url/公众号名/日期，结构正好够"人事雷达"挂信源标签；依赖搜狗接口，反爬风险自担 |
| [fancyboi999/weixin_search_mcp](https://github.com/fancyboi999/weixin_search_mcp) | MCP（公众号搜索+正文获取） | 小众 | 同样走搜狗入口，能取正文，可作上一个的备选 |
| [chyroc/WechatSogou](https://github.com/chyroc/WechatSogou)、[ctwj/wechat_search](https://github.com/ctwj/wechat_search) | 老牌爬虫库 | ⚠️ 年久失修 | 仅作实现思路参考，不进管线 |

### 3.2 小红书搜索（薯厂动态 + 打工人风声）

| 项目 | 形态 | 状态 | 评估 |
|------|------|------|------|
| [xpzouying/xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) | MCP（Go，本地浏览器方案） | ✅ 活跃，**14.5k★**，2026-06 仍在发版 | **首选**。支持关键词搜索（可按发布时间过滤）、帖子详情、评论；需登录真实小红书账号，单账号不可多端同时在线，有账号风控风险 → 用小号 |
| [iFurySt/RedNote-MCP](https://github.com/iFurySt/RedNote-MCP)、[ShunL12324/xhs-mcp](https://github.com/ShunL12324/xhs-mcp)、[chenningling/Redbook-Search-Comment-MCP2.0](https://github.com/chenningling/Redbook-Search-Comment-MCP2.0) | MCP（Node/Playwright） | 活跃度不一 | 备选；Playwright 方案更重 |

### 3.3 微博热搜 / 搜索（🔴级传闻 + 快讯信号）

| 项目 | 形态 | 评估 |
|------|------|------|
| [Yooki-K/weibo-mcp-server](https://github.com/Yooki-K/weibo-mcp-server) | MCP（热搜榜+详情+评论） | 拉热搜榜做"今日大瓜雷达"，命中"字节/腾讯/裁员"等关键词再深挖 |
| [qinyuanpei/mcp-server-weibo](https://github.com/qinyuanpei/mcp-server-weibo) | MCP（用户/内容/话题搜索） | 功能最全的微博 MCP，适合按公司名搜内容做交叉验证 |
| [Selenium39/mcp-server-weibo](https://github.com/Selenium39/mcp-server-weibo) | MCP（TypeScript） | 备选 |

### 3.4 聚合热榜 / 快讯（快讯拼盘的原料）

| 项目 | 形态 | 评估 |
|------|------|------|
| [imsyy/DailyHotApi](https://github.com/imsyy/DailyHotApi) | 聚合 API + RSS（微博/知乎/36氪/IT之家/澎湃等数十源） | **首选**。自部署后一个接口拿全网热榜，默认 60min 缓存，Docker/Vercel 皆可 |
| [DIYgod/RSSHub](https://github.com/DIYgod/RSSHub) | 万物皆可 RSS | 自部署实例跑 `/36kr/newsflashes`、`/weibo/search/hot` 等路由；公共实例已证实不可用 |
| [fancyboi999/daily-hot-mcp](https://github.com/fancyboi999/daily-hot-mcp)、[wopal-cn/mcp-hotnews-server](https://github.com/wopal-cn/mcp-hotnews-server) | 热榜 MCP | 想跳过 RSS 直接给 Agent 用时的轻量选择 |

### 3.5 脉脉（职言）—— 结论：不进自动管线

GitHub 上只有年久失修的逆向脚本（[lsongdev/maimai-js](https://github.com/lsongdev/maimai-js) 等），
脉脉反爬强、需登录态、且抓匿名区有合规争议。**建议主理人人工刷职言喂素材（档B），
不做自动化。** 职言内容本身也只配 🔴级，人工筛选反而更稳。

## 4. 推荐信源管线（四层）

```
第一层｜快讯基线（每天定时拉取）
  自部署 DailyHotApi / RSSHub → 36氪快讯、IT之家、微博热搜、知乎热榜
  → 供【快讯拼盘】【今日头瓜】选题                        信源级别：🟡

第二层｜权威公众号订阅（🟡级主力，人事雷达的信源标签来源）
  自部署 we-mp-rss → 订阅：晚点LatePost、36氪、界面新闻、财新网、
  Tech星球、雷峰网、量子位 等公众号 → RSS/Webhook 推送      信源级别：🟡

第三层｜关键词交叉验证（人事类"2个独立信源"靠这层凑齐）
  sogou-weixin-mcp-server（公众号全文搜索）
  + qinyuanpei/mcp-server-weibo（微博内容搜索）
  + xiaohongshu-mcp（小红书关键词+时间过滤）
  → 对头瓜/人事雷达逐条验证                    信源级别：🟢（搜到官宣）/🟡/🔴

第四层｜兜底降级
  Claude 内置 WebSearch → 检索"公司名+人事/架构/裁员+日期"
  → 只在自部署层不可用时启用，并在判档声明中说明降级         信源级别：按命中媒体定
```

配套的机器可读清单见 `examples/wechat_column_sourcing.yaml`。

## 5. 落地步骤建议（本地部署优先）

> 已定策略：**先在本地机器部署，有机会再迁移云端**。
> 完整操作手册见 `docs/local-deployment.md`，配置文件见 `examples/sourcing/`。

1. 本地 Docker 起三件套：`DailyHotApi`（:6688）、`RSSHub`（:1200）、
   `we-mp-rss`（:8001，微信扫码授权用小号）——`examples/sourcing/docker-compose.yml` 一键启动。
2. 本地 Claude Code 挂 MCP：`sogou-weixin-mcp-server`（uvx 直跑）、
   `mcp-server-weibo`（uvx）、`xiaohongshu-mcp`（:18060，需登录小红书小号，注意单端在线限制）。
3. 写作流程：每晚 20:00 拉第一层+第二层 → 选头瓜 → 第三层逐条交叉验证 →
   按栏目 Prompt 生成样刊 → 发布前跑"信源自查清单"。
4. 风控提醒：搜狗/小红书/微博接口均无官方授权，**控制频率（每天 1~2 轮足够）、
   用小号、缓存结果**；wewe-rss 的封控史（24h 小黑屋）是前车之鉴。
5. 后续迁移云端：选国内/香港 VPS（境外机房已实测 403），compose 与 `./data/`
   目录原样平移即可保留授权与订阅，详见本地部署指南第 5 节。

## 6. 本次检索来源

- 微信搜索类：[weixin_search_mcp](https://github.com/fancyboi999/weixin_search_mcp)、[sogou-weixin-mcp-server](https://github.com/ptbsare/sogou-weixin-mcp-server)、[WechatSogou](https://github.com/chyroc/WechatSogou)、[wechat_search](https://github.com/ctwj/wechat_search)、[go-weixin-sogou](https://github.com/reveever/go-weixin-sogou)
- 公众号订阅类：[wewe-rss](https://github.com/cooderl/wewe-rss)、[we-mp-rss](https://github.com/rachelos/we-mp-rss)
- 小红书类：[xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp)、[RedNote-MCP](https://github.com/iFurySt/RedNote-MCP)、[xhs-mcp](https://github.com/ShunL12324/xhs-mcp)、[Redbook-Search-Comment-MCP2.0](https://github.com/chenningling/Redbook-Search-Comment-MCP2.0)、[mcp-xiaohongshu](https://github.com/timecyber/mcp-xiaohongshu)
- 微博类：[weibo-mcp-server](https://github.com/Yooki-K/weibo-mcp-server)、[mcp-server-weibo (qinyuanpei)](https://github.com/qinyuanpei/mcp-server-weibo)、[mcp-server-weibo (Selenium39)](https://github.com/Selenium39/mcp-server-weibo)
- 聚合类：[DailyHotApi](https://github.com/imsyy/DailyHotApi)、[RSSHub](https://github.com/DIYgod/RSSHub)、[daily-hot-mcp](https://github.com/fancyboi999/daily-hot-mcp)、[mcp-hotnews-server](https://github.com/wopal-cn/mcp-hotnews-server)
- 脉脉类：[maimai-js](https://github.com/lsongdev/maimai-js)（仅参考，不推荐）
