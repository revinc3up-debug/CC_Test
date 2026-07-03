# 信源防封门控（Anti-Ban Gate）

> 信源工具全部无官方授权，账号 / IP 极易被风控。本文件把各平台的封控机制调研
> 落成一套**可执行门控**：`framework/sourcing_gate.py` + `examples/sourcing/anti_ban_gate.yaml`。
> 核心理念——**主动限速，不要等被封**；任一信源撞墙就降级板块（宁缺毋滥），绝不硬拉。
> 调研日期：2026-07-03。

---

## 1. 各平台封控机制（实测调研）

### 1.1 搜狗微信搜索
- **封禁手段**：封 IP + 封 Cookie（靠 `SNUID` 判断访问频次，请求需带 `SUV`）。
- **触发阈值**：约 5 秒翻一页、连翻 ~20 页即触发验证码 / 302 跳转。
- **访问上限**：未登录只能看**前 10 页**，登录也仅能到前 100 页。
- **门控对策**：`min_interval 12~20s`、`daily_quota 40`、翻页不超过 10 页；撞验证码/302 → 冷却 1h。

### 1.2 小红书（2025 风控升级）
- **封禁手段**：请求签名（`x-s`）校验、**Cookie 有效期缩短至 10 分钟**、IP 高频阈值下调。
- **官方经验值**：请求间隔建议 **3~8 秒/次**；间隔需随机化，避免规律性。
- **行为画像**：**只采集不互动 → 判定僵尸号**；直奔目标、连续收藏同类笔记会被盯上。
- **门控对策**：`min_interval 8~14s`、`daily_quota 60`、`max_accounts 2`（备小号轮换）；
  单账号**不可多端同时在线**（登录 MCP 后别再网页登录该号）。

### 1.3 微信读书系（we-mp-rss / wewe-rss）
- **封禁手段**：底层走微信读书接口，关注公众号过多 / 刷新超频 → 验证码 → 持续触发**关 24h 小黑屋**。
- **实测上限**：约 **10 个公众号 × 每天刷新 2 次**；要订更多号就**加账号**，不是加频率。
- **恢复**：账号正常时可重启容器清小黑屋记录；已进小黑屋则等 24h。
- **门控对策**：`min_interval 6h`、`daily_quota 2`（次/日）、`block_cooldown 24h`；订阅号 >10 时扩账号池。

### 1.4 微博
- 相对宽松，但同样不高频：`min_interval 5~9s`、`daily_quota 100`、冷却 30min。

### 1.5 自建 DailyHotApi / RSSHub
- 自带缓存（DailyHot 默认 60min）。命中缓存不发请求，`min_interval 1h`、`daily_quota 24` 足够。

## 2. 门控设计：三道闸门

`SourcingGate.acquire(source)` 依次过三道闸门，返回 `Decision(allowed, wait_seconds, reason, account_index)`：

| 闸门 | 规则 | 命中结果 |
|------|------|---------|
| ① 熔断冷却 | 上次 `report_block` 后仍在 `cooldown_until` 内 | `allowed=False`，返回剩余冷却秒数 |
| ② 每日配额 | `used_today >= daily_quota` | `allowed=False`，跳过该信源直到次日 |
| ③ 最小间隔 | `now < next_allowed_at` | `allowed=True`，返回需 `wait_seconds` 再发 |

关键点：
- **门控只做决策不 sleep**——等待交给调用方，时间 / 抖动可注入，单测零等待。
- **随机抖动**（`min_interval + rand(0, jitter)`）打散规律性，规避频次画像。
- **`report_block()` 即熔断**：进入冷却 + 轮换账号，**禁止立刻重试**；同日多次被封冷却时长线性翻倍（越撞越退避）。
- **每日配额跨自然日自动重置**。

## 3. 用法

```python
from framework.sourcing_gate import SourcingGate

gate = SourcingGate.from_yaml("examples/sourcing/anti_ban_gate.yaml")

d = gate.acquire("xiaohongshu")
if not d.allowed:
    log(d.reason)                 # 冷却/配额 → 跳过，按栏目规则降级该板块
else:
    if d.wait_seconds:
        time.sleep(d.wait_seconds)  # 满足最小间隔
    try:
        result = do_request(account=d.account_index)
        gate.report_success("xiaohongshu")
    except Blocked:                # 验证码 / 403 / 302 跳验证 / 小黑屋
        gate.report_block("xiaohongshu")   # 熔断 + 轮换，别立刻重试
```

阈值集中在 `examples/sourcing/anti_ban_gate.yaml`，调参不改代码。测试见 `tests/test_sourcing_gate.py`。

## 4. 门控之外的配套纪律

门控挡住"频率"，但账号安全还得靠这些人肉纪律：
1. **一律小号**：微信、小红书都用工具专用小号，主号绝不碰任何工具。
2. **单端在线**：小红书登录 MCP 后别在网页端登录同一账号，否则掉线。
3. **缓存优先**：命中缓存不发请求；DailyHotApi 60min 缓存别绕过。
4. **每日 1~2 轮**：整条管线每天拉取 1~2 轮足矣，别循环重试。
5. **降级不硬刚**：某信源冷却/配额耗尽就删对应板块，栏目规则本就允许"没有就少写"。
6. **住宅/本地出口**：本地部署天然是住宅出口，最稳；迁云端选国内/香港，避免机房 IP 被重点盯。

## 5. 关注策略：优先"资讯号 + 独立站"，少直连搜索

直接爬搜索接口封控风险最高。更稳的姿势是**订阅成熟的大厂资讯号**（走 we-mp-rss，风险可控），
把搜索类 MCP 只用于"人事类第二信源交叉验证"。重点关注：

| 类型 | 号 / 站 | 说明 | 接入方式 |
|------|--------|------|---------|
| 大厂新闻八卦聚合 | **大厂日爆**（独立站 dachangribao.com + 公众号） | 每日大厂动态/爆料聚合，选题密度高 | 优先抓独立站；公众号走 we-mp-rss |
| 大厂员工向社区 | **大厂青年**（即刻 / 公众号） | 大厂员工视角资讯与讨论 | we-mp-rss / 即刻 |
| 权威科技媒体 | **晚点 LatePost**、**36氪**、**Tech星球**(tech618)、**字母榜**、**蓝鲸财经**、**界面新闻**、**财新** | 🟡 级主力信源，人事/组织调整的权威出处 | we-mp-rss 订阅 |
| 榜单发现 | werss.app/rank、今日热榜 tech 频道 | 找还没订阅的优质号 | 人工 |

> 提示：能从**独立网站 / RSS** 拿到的内容，就别去爬平台搜索接口——网站几乎没有账号封控风险，
> 也不占门控配额。`大厂日爆` 有独立站正是这个原因值得优先。（注：dachangribao.com 在本
> Claude Code 境外环境 DNS 解析失败，属环境网络限制；本地/国内网络应可正常访问，落地时请自行核实。）

## 6. 调研来源
- 搜狗微信反爬：[知乎·搜狗微信爬虫](https://zhuanlan.zhihu.com/p/270296193)、[CSDN·搜狗微信反爬机制](https://blog.csdn.net/sinat_23069795/article/details/89888507)
- 小红书风控：[CSDN·2025 小红书反爬](https://blog.csdn.net/shanwei_spider/article/details/155629115)、[CSDN·小红书风控行为检测](https://blog.csdn.net/klj3388/article/details/146016922)
- 微信读书封控：[wewe-rss](https://github.com/cooderl/wewe-rss)、[we-mp-rss](https://github.com/rachelos/we-mp-rss)、[少数派·WeWe RSS](https://sspai.com/post/93845)
- 防封通用：[LoongProxy·UA 轮换](https://www.loongproxy.com/ipdaili/3260.html)、[顶象·反爬三阶段](https://www.dingxiang-inc.com/blog/post/637)
- 资讯号：[大厂日爆](https://dachangribao.com/)、[大厂青年·即刻](https://m.okjike.com/users/80543A26-D336-45CA-A958-9D59E7812612)、[werss 公众号榜](https://werss.app/rank)
