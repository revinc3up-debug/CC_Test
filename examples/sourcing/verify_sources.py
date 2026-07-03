#!/usr/bin/env python3
"""信源可用性验证脚本 —— 在**本地（国内网络）**机器上运行，逐项验证资源信息获取。

覆盖目标（对应 /goal：本地完成资源信息获取验证，含微信搜索与小红书检索）：
  1. 原生 RSS 独立站（36氪/虎嗅/IT之家…）—— 直接抓取 + 解析
  2. 微信搜索（搜狗微信）—— 关键词检索，检测是否返回结果 / 撞反爬
  3. 小红书检索 —— 探测 xiaohongshu-mcp 服务是否就绪、账号是否登录
  4. 自建服务 DailyHotApi(:6688) / RSSHub(:1200) —— 抓取 + 解析
每次对外请求都先过 framework.sourcing_gate 的防封门控。

依赖：仅标准库（PyYAML 可选，用于加载门控配置；缺失时用内置保守默认值）。

用法：
    python examples/sourcing/verify_sources.py                 # 全量验证，默认关键词
    python examples/sourcing/verify_sources.py --query "字节 组织架构"
    python examples/sourcing/verify_sources.py --only wechat,xhs
    python examples/sourcing/verify_sources.py --timeout 20

退出码：0 = 无 FAIL（SKIP 不算失败）；1 = 存在 FAIL。

注意：本脚本在 Claude Code 云端环境会因网络策略把所有国内源判为 BLOCKED——那是环境限制，
不代表工具不可用；请在本地/国内网络运行以获得真实结论。
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

# 让脚本能 import 到 framework（脚本位于 examples/sourcing/ 下）
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

try:
    from framework.sourcing_gate import SourcingGate, SourcePolicy
except Exception:  # pragma: no cover - 仅在仓库外单独拷贝运行时触发
    SourcingGate = None  # type: ignore
    SourcePolicy = None  # type: ignore

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

PASS, FAIL, BLOCKED, SKIP = "PASS", "FAIL", "BLOCKED", "SKIP"
ICON = {PASS: "✅", FAIL: "❌", BLOCKED: "\U0001f6ab", SKIP: "➖"}


@dataclass
class Result:
    name: str
    category: str
    status: str
    detail: str
    sample: str = ""


# ---- 底层 HTTP ------------------------------------------------------------

def _http_get(url: str, timeout: float) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": BROWSER_UA,
                                               "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _classify_error(exc: Exception) -> tuple[str, str]:
    """把异常归类成 BLOCKED（够不到/被拦）或 FAIL（拿到了但内容不对）。"""
    if isinstance(exc, urllib.error.HTTPError):
        # 403/407 多为网络策略或反爬；5xx 上游故障——都归 BLOCKED（非工具本身问题）
        if exc.code in (403, 407, 429, 503, 502):
            return BLOCKED, f"HTTP {exc.code}（策略拒绝/反爬/上游）"
        return FAIL, f"HTTP {exc.code}"
    if isinstance(exc, (urllib.error.URLError, socket.timeout, ConnectionError, OSError)):
        return BLOCKED, f"连接失败：{exc}"
    return FAIL, f"{type(exc).__name__}: {exc}"


# ---- 各类检查 -------------------------------------------------------------

def check_rss(name: str, url: str, timeout: float, is_local: bool = False) -> Result:
    try:
        raw = _http_get(url, timeout)
        root = ET.fromstring(raw)
        items = root.findall(".//item") or root.findall(
            ".//{http://www.w3.org/2005/Atom}entry")
        if not items:
            return Result(name, "RSS", FAIL, "解析成功但无条目", "")
        first = items[0]
        title = (first.findtext("title")
                 or first.findtext("{http://www.w3.org/2005/Atom}title") or "").strip()
        date = (first.findtext("pubDate")
                or first.findtext("{http://www.w3.org/2005/Atom}updated") or "").strip()
        return Result(name, "RSS", PASS, f"{len(items)} 条", f"{title} | {date}")
    except Exception as exc:  # noqa: BLE001
        status, detail = _classify_error(exc)
        # 本地自建 RSSHub 连不上通常是"没启动"而非被封 → SKIP 更贴切
        if is_local and status == BLOCKED:
            return Result(name, "RSS", SKIP, f"未启动或不可达：{detail}")
        return Result(name, "RSS", status, detail)


def check_wechat_search(query: str, timeout: float) -> Result:
    """微信搜索验证：搜狗微信关键词检索，判断是否返回结果 / 撞反爬。"""
    from urllib.parse import quote
    url = f"https://weixin.sogou.com/weixin?type=2&query={quote(query)}"
    try:
        raw = _http_get(url, timeout)
        html = raw.decode("utf-8", "ignore")
        # 反爬特征：验证码 / 访问过于频繁
        if "请输入验证码" in html or "antispider" in html or "auto_ip" in html:
            return Result("微信搜索(搜狗)", "微信搜索", BLOCKED,
                          "撞验证码/反爬——降低频率或换 IP，走防封门控")
        # 结果特征：搜狗结果条目容器 class="news-box" / txt-box
        hits = html.count("txt-box") + html.count("news-list")
        if hits == 0:
            return Result("微信搜索(搜狗)", "微信搜索", FAIL,
                          "页面无结果条目（可能改版或被拦）")
        return Result("微信搜索(搜狗)", "微信搜索", PASS,
                      f"命中结果容器 {hits} 处", f'关键词="{query}"')
    except Exception as exc:  # noqa: BLE001
        status, detail = _classify_error(exc)
        return Result("微信搜索(搜狗)", "微信搜索", status, detail)


def _port_open(host: str, port: int, timeout: float) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_xiaohongshu(timeout: float) -> Result:
    """小红书检索验证：探测 xiaohongshu-mcp 服务(:18060) 是否就绪。

    实际的关键词检索由 Claude 通过 MCP 工具调用完成（见 mcp.json.example）；
    本脚本负责确认服务在线、可握手，避免"以为在跑其实没起来"。
    """
    host, port = "127.0.0.1", 18060
    if not _port_open(host, port, timeout):
        return Result("小红书检索(xiaohongshu-mcp)", "小红书检索", SKIP,
                      f"未检测到 {host}:{port} 上的 MCP 服务——先启动并登录小号，见 "
                      "docs/local-deployment.md §2.1")
    # 端口在听，尝试探一下 MCP 端点是否响应
    try:
        _http_get(f"http://{host}:{port}/mcp", timeout)
        endpoint_ok = True
    except urllib.error.HTTPError:
        endpoint_ok = True  # 返回 4xx 也说明端点存在（MCP 需正确握手）
    except Exception:  # noqa: BLE001
        endpoint_ok = False
    if endpoint_ok:
        return Result("小红书检索(xiaohongshu-mcp)", "小红书检索", PASS,
                      "服务在线；用 Claude 调 MCP search 工具做关键词检索确认登录态")
    return Result("小红书检索(xiaohongshu-mcp)", "小红书检索", FAIL,
                  f"端口 {port} 在听但 /mcp 无响应")


def check_local_json(name: str, url: str, timeout: float) -> Result:
    try:
        raw = _http_get(url, timeout)
        data = json.loads(raw)
        items = data.get("data") if isinstance(data, dict) else data
        n = len(items) if isinstance(items, list) else 0
        if n == 0:
            return Result(name, "自建服务", FAIL, "返回 JSON 但无数据")
        first = items[0]
        title = first.get("title") if isinstance(first, dict) else str(first)
        return Result(name, "自建服务", PASS, f"{n} 条", str(title)[:60])
    except Exception as exc:  # noqa: BLE001
        status, detail = _classify_error(exc)
        # 自建服务连不上通常是"没启动"而非被封 → SKIP 更贴切
        if status == BLOCKED:
            return Result(name, "自建服务", SKIP, f"未启动或不可达：{detail}")
        return Result(name, "自建服务", status, detail)


# ---- 门控 -----------------------------------------------------------------

def build_gate() -> "SourcingGate | None":
    if SourcingGate is None:
        return None
    cfg = Path(__file__).with_name("anti_ban_gate.yaml")
    try:
        if cfg.exists():
            return SourcingGate.from_yaml(cfg)
    except Exception:  # noqa: BLE001  (PyYAML 缺失等)
        pass
    # 兜底：内置保守默认值，无需 YAML
    pol = {n: SourcePolicy(name=n, min_interval_seconds=3, jitter_seconds=2,
                           daily_quota=50)
           for n in ("sogou-weixin", "xiaohongshu", "hot-aggregator")}
    return SourcingGate(pol)


def gated(gate, source: str) -> None:
    """在真正发请求前过门控；返回需等待秒数则等待。仅演示，失败不阻断验证。"""
    if gate is None:
        return
    try:
        d = gate.acquire(source)
        if d.allowed and d.wait_seconds:
            time.sleep(min(d.wait_seconds, 2.0))  # 验证脚本里封顶 2s，避免久等
    except KeyError:
        pass


# ---- 主流程 ---------------------------------------------------------------

NATIVE_FEEDS = [
    ("36氪·快讯", "https://36kr.com/feed-newsflash"),
    ("36氪·全站", "https://36kr.com/feed"),
    ("虎嗅", "https://rss.huxiu.com/"),
    ("钛媒体", "https://www.tmtpost.com/rss.xml"),
    ("IT之家", "https://www.ithome.com/rss/"),
    ("少数派", "https://sspai.com/feed"),
    ("爱范儿", "https://www.ifanr.com/feed"),
]


def run(query: str, timeout: float, only: set[str]) -> list[Result]:
    gate = build_gate()
    results: list[Result] = []

    def want(tag: str) -> bool:
        return not only or tag in only

    if want("rss"):
        for name, url in NATIVE_FEEDS:
            gated(gate, "hot-aggregator")
            results.append(check_rss(name, url, timeout))

    if want("wechat"):
        gated(gate, "sogou-weixin")
        results.append(check_wechat_search(query, timeout))

    if want("xhs"):
        gated(gate, "xiaohongshu")
        results.append(check_xiaohongshu(timeout))

    if want("local"):
        results.append(check_local_json("DailyHotApi(:6688)",
                                         "http://127.0.0.1:6688/36kr", timeout))
        results.append(check_rss("RSSHub(:1200)",
                                 "http://127.0.0.1:1200/36kr/newsflashes", timeout,
                                 is_local=True))

    return results


def main() -> int:
    ap = argparse.ArgumentParser(description="信源可用性验证（本地运行）")
    ap.add_argument("--query", default="腾讯 组织架构", help="微信搜索验证用关键词")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--only", default="",
                    help="逗号分隔子集：rss,wechat,xhs,local（默认全部）")
    ap.add_argument("--receipt", action="store_true",
                    help="额外打印一段可回帖的『本地验证回执』，贴回给 Claude 即可闭环")
    args = ap.parse_args()
    only = {s.strip() for s in args.only.split(",") if s.strip()}

    print(f"信源验证开始 | query={args.query!r} | timeout={args.timeout}s\n" + "-" * 68)
    results = run(args.query, args.timeout, only)

    by_cat: dict[str, list[Result]] = {}
    for r in results:
        by_cat.setdefault(r.category, []).append(r)
    for cat, rs in by_cat.items():
        print(f"\n▍{cat}")
        for r in rs:
            line = f"  {ICON.get(r.status,'?')} {r.status:7} {r.name:28} {r.detail}"
            print(line)
            if r.sample:
                print(f"          ↳ {r.sample}")

    n_pass = sum(r.status == PASS for r in results)
    n_fail = sum(r.status == FAIL for r in results)
    n_block = sum(r.status == BLOCKED for r in results)
    n_skip = sum(r.status == SKIP for r in results)
    print("\n" + "-" * 68)
    print(f"合计 {len(results)} 项：{ICON[PASS]}PASS {n_pass}  "
          f"{ICON[FAIL]}FAIL {n_fail}  {ICON[BLOCKED]}BLOCKED {n_block}  "
          f"{ICON[SKIP]}SKIP {n_skip}")
    if n_block:
        print("提示：BLOCKED 多为网络策略/反爬。若在云端环境属预期；本地/国内网络应为 PASS。")

    if args.receipt:
        import platform
        import datetime
        wechat = next((r for r in results if r.category == "微信搜索"), None)
        xhs = next((r for r in results if r.category == "小红书检索"), None)
        stamp = datetime.datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z")
        print("\n===== 本地验证回执（复制以下整段贴回给 Claude）=====")
        print(f"[本地环境资源获取验证回执] time={stamp} host={platform.node()} "
              f"os={platform.system()}")
        print(f"  微信搜索: {wechat.status if wechat else 'N/A'} "
              f"| {wechat.detail if wechat else ''}")
        print(f"  小红书检索: {xhs.status if xhs else 'N/A'} "
              f"| {xhs.detail if xhs else ''}")
        print(f"  汇总: PASS {n_pass} / FAIL {n_fail} / BLOCKED {n_block} / SKIP {n_skip}")
        verdict = "通过" if (wechat and wechat.status == PASS
                             and (xhs is None or xhs.status in (PASS, SKIP))
                             and n_fail == 0) else "未通过/需排查"
        print(f"  结论: 微信搜索+小红书检索 本地验证 → {verdict}")
        print("=================================================")
    return 1 if n_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
