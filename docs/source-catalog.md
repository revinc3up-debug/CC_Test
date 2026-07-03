# 独立站 / RSS 信源目录

> 承接 `docs/anti-ban-gate.md` 第 5 节的策略——**能从独立网站 / RSS 拿的内容，就别爬平台搜索接口**。
> RSS/独立站几乎零账号封控风险、不占防封门控配额，是《大厂茶水间》最稳的信源底盘。
> 可直接导入的订阅清单见 `examples/sourcing/feeds.opml`。
> 调研日期：2026-07-03。
>
> ⚠️ **核实声明**：以下 URL 由多份社区 RSS 清单交叉整理得出；本 Claude Code 境外环境对国内站
> 普遍 403（环境网络限制），**未能逐条实拉验证**。本地 / 国内网络导入后请自行确认每条是否可用、
> 失效的用 RSSHub 路由兜底。

---

## 0. Claude 原生 WebSearch 域名限定检索（✅ 本环境已实测通过，零封控）

**最省事、零风险、云端本地皆可用**，无需部署、无需账号、不占防封门控配额。做法是给 WebSearch
指定 `allowed_domains` 把检索限定到目标平台。2026-07-03 已实测取到真实数据（见 `docs/verification-report.md`）：

| 用途 | allowed_domains | 实测结果 |
|------|-----------------|---------|
| **微信搜索** | `mp.weixin.qq.com`, `weixin.sogou.com` | ✅ 取到腾讯/字节组织架构相关公众号文章 |
| **小红书检索** | `xiaohongshu.com`, `xhslink.com` | ✅ 取到大厂裁员/PIP 员工爆料 |
| **权威媒体交叉验证** | `36kr.com`, `latepost.com`, `huxiu.com`, `jiemian.com` | ✅ 取到 2026 当期大厂动态 |

局限：`WebFetch` 抓 CN 全文正文在云端受网络策略限制（403），只能拿 WebSearch 标题+摘要（快讯/选题够用，
头瓜要全文靠下面的自建工具补）；时效随查询而变，写作时 query 带年份并逐条核对日期。

> 优先级：**本层（WebSearch 域名限定）作为 Claude 写作流的日常首选** → 下面第 1~4 类自建/订阅作深度增强。

## 1. 原生 RSS 独立站（直连、零封控、不占门控配额）

这类站点自带 RSS，RSS 阅读器 / we-mp-rss / 框架定时任务直接拉即可，最省心。

| 媒体 | 定位 | RSS 地址 | 信源级别 |
|------|------|---------|---------|
| **36氪** | 大厂融资/business，快讯流 | `https://36kr.com/feed`（全站）、`https://36kr.com/feed-newsflash`（快讯）、`https://36kr.com/feed-article`（文章） | 🟡 |
| **虎嗅** | 商业深度、大厂评论 | `https://rss.huxiu.com/` | 🟡 |
| **钛媒体** | 科技商业 | `https://www.tmtpost.com/rss.xml` | 🟡 |
| **IT之家** | 科技快讯（时效快、量大） | `https://www.ithome.com/rss/` | 🟡 |
| **少数派** | 数码/效率/行业观察 | `https://sspai.com/feed` | 🟡 |
| **爱范儿** | 科技消费/大厂产品 | `https://www.ifanr.com/feed` | 🟡 |

> 36氪的 RSS 中心还列了更多分频道源：`https://36kr.com/rss-center`。

## 2. 需 RSSHub 的独立站 / 优质内容（自建 RSSHub :1200 兜底）

这些站没有稳定原生 RSS，走**自建 RSSHub**（`examples/sourcing/docker-compose.yml` 里的 rsshub:1200）。
高把握的路由已写进 OPML；其余用官方路由文档现查：<https://docs.rsshub.app>。

| 媒体 / 内容 | 定位 | RSSHub 路由（本地实例前缀 `http://localhost:1200`） | 信源级别 |
|------|------|------|---------|
| **晚点 LatePost** | 大厂人事/组织调整**权威一手**，人事雷达主力 | `/latepost` | 🟡（人事类可当独立信源之一） |
| **36氪快讯**（备用） | 快讯拼盘原料 | `/36kr/newsflashes` | 🟡 |
| **大厂青年**（即刻） | 大厂员工视角资讯 | `/jike/user/80543A26-D336-45CA-A958-9D59E7812612` | 🟡/🔴 视内容 |
| **字母榜 / 极客公园 / 雷峰网 / 界面新闻** | 科技商业媒体 | 见 RSSHub 路由文档搜对应站名 | 🟡 |

## 3. 聚合入口（选题雷达，不作单一信源）

| 来源 | 用途 | 接入 |
|------|------|------|
| **大厂日爆**（独立站 dachangribao.com + 公众号） | 大厂新闻八卦聚合，选题密度最高 | 优先抓独立站；公众号走 we-mp-rss |
| **自建 DailyHotApi**（:6688） | 36氪/微博/知乎/IT之家 热榜一把梭 | REST，见 docker-compose |
| **今日热榜 tech 频道** / **werss.app/rank** | 发现还没订阅的优质号 | 人工浏览 |

## 4. Newsletter / 邮件订阅（每周深度，补充背景）

| 名称 | 主理 | 节奏 | 说明 |
|------|------|------|------|
| **科技爱好者周刊** | 阮一峰 | 周五 | 中文科技 newsletter 标杆；博客有 RSS `https://www.ruanyifeng.com/blog/atom.xml` |
| **今日三句半** | 纽约科技投资圈 | 每日 | 精选当日最重要科技新闻 |
| **产品沉思录** | — | 每周 | 互联网产品/运营视角 |

## 5. 英文 / 海外看中国科技（交叉验证 + 换个视角）

| 媒体 | RSS | 用途 |
|------|-----|------|
| **TechNode** | `https://technode.com/feed/` | 英文中国科技新闻，大厂动态 |
| **PingWest 品玩（英文）** | `https://en.pingwest.com/feed` | 英文科技媒体 |
| **SCMP Tech** | scmp.com/tech（栏目 RSS 见站内） | 港媒视角中国科技 |

## 6. 怎么用（对应栏目板块）

- **快讯拼盘** ← 36氪快讯 + IT之家 + DailyHotApi 热榜（量大、时效快）
- **今日头瓜 / 人事雷达** ← 晚点 LatePost + 36氪 + 虎嗅（🟡 权威，人事类还需第二独立信源交叉验证）
- **茶水间风声（🔴）** ← 大厂日爆 / 大厂青年 / 即刻等社区向内容，**只作传闻，挂"据传/网传"**
- **背景补充** ← 科技爱好者周刊等 newsletter、英文源

优先级：**原生 RSS 独立站（第1类）> RSSHub 独立站（第2类）> 聚合热榜（第3类）> 搜索类 MCP（最后手段，走防封门控）**。
前两类零封控、无需登录、不占门控配额，应当是日常拉取的主力。

## 7. 一键导入

`examples/sourcing/feeds.opml` 是标准 OPML，可直接导入 RSS 阅读器 / we-mp-rss。
其中 RSSHub 类条目指向 `http://localhost:1200`（自建实例），与本地部署一致；迁云端时把前缀换成 VPS 地址即可。

## 8. 调研来源
- RSS 源清单：[weekend-project-space/top-rss-list](https://github.com/weekend-project-space/top-rss-list)、[amazingcoderpro/rss-recomanded](https://github.com/amazingcoderpro/rss-recomanded)、[少数派·RSS 永久链接合集](https://sspai.com/post/73138)
- 各媒体 RSS：[36氪 RSS 中心](https://www.36kr.com/rss-center)、[虎嗅](https://rss.huxiu.com/)、[钛媒体](https://www.tmtpost.com/rss.xml)、[IT之家](https://www.ithome.com/rss/)、[少数派](https://sspai.com/feed)
- 晚点 RSS：[RSSHub /latepost](https://rsshub.rssforever.com/latepost)、[LPRSS 项目](https://github.com/JonathanChen-JC/LPRSS)
- 英文源：[TechNode](https://technode.com/)、[PingWest EN](https://en.pingwest.com/)、[Feedspot·China Tech RSS](https://rss.feedspot.com/china_technology_rss_feeds/)
- Newsletter：[大邓·高质量 Newsletter 汇总](https://textdata.cn/blog/newsletter-list/)、[少数派·Newsletter](https://sspai.com/post/65892)
