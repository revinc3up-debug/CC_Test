"""Network-free tests for examples/sourcing/verify_sources.py.

We patch the module's ``_http_get`` so no real requests are made; this guards
the RSS-parsing and error-classification logic, not live connectivity.
"""

import importlib.util
import socket
import sys
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "examples" / "sourcing" / "verify_sources.py"

spec = importlib.util.spec_from_file_location("verify_sources", MODULE_PATH)
vs = importlib.util.module_from_spec(spec)
sys.modules["verify_sources"] = vs  # dataclass 注解解析需模块在 sys.modules 中
spec.loader.exec_module(vs)


RSS_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <title>36Kr</title>
  <item><title>字节又调整了一条业务线</title><pubDate>Fri, 03 Jul 2026 12:00:00 GMT</pubDate></item>
  <item><title>另一条快讯</title><pubDate>Fri, 03 Jul 2026 11:00:00 GMT</pubDate></item>
</channel></rss>""".encode("utf-8")


def test_check_rss_parses_items(monkeypatch):
    monkeypatch.setattr(vs, "_http_get", lambda url, t: RSS_SAMPLE)
    r = vs.check_rss("36氪", "http://x", 5)
    assert r.status == vs.PASS
    assert "2 条" in r.detail
    assert "字节又调整了一条业务线" in r.sample


def test_check_rss_empty_is_fail(monkeypatch):
    monkeypatch.setattr(vs, "_http_get",
                        lambda url, t: b"<rss><channel></channel></rss>")
    r = vs.check_rss("空源", "http://x", 5)
    assert r.status == vs.FAIL


def test_check_rss_403_is_blocked(monkeypatch):
    def boom(url, t):
        raise urllib.error.HTTPError(url, 403, "Forbidden", {}, None)
    monkeypatch.setattr(vs, "_http_get", boom)
    r = vs.check_rss("被封", "http://x", 5)
    assert r.status == vs.BLOCKED


def test_check_rss_local_refused_is_skip(monkeypatch):
    def boom(url, t):
        raise urllib.error.URLError(ConnectionRefusedError(111, "refused"))
    monkeypatch.setattr(vs, "_http_get", boom)
    r = vs.check_rss("RSSHub", "http://127.0.0.1:1200/x", 5, is_local=True)
    assert r.status == vs.SKIP


def test_wechat_search_detects_captcha(monkeypatch):
    monkeypatch.setattr(vs, "_http_get",
                        lambda url, t: "请输入验证码".encode())
    r = vs.check_wechat_search("腾讯", 5)
    assert r.status == vs.BLOCKED
    assert "反爬" in r.detail or "验证码" in r.detail


def test_wechat_search_detects_results(monkeypatch):
    html = '<div class="news-list"><div class="txt-box">结果</div></div>'
    monkeypatch.setattr(vs, "_http_get", lambda url, t: html.encode())
    r = vs.check_wechat_search("腾讯", 5)
    assert r.status == vs.PASS


def test_xiaohongshu_skip_when_port_closed(monkeypatch):
    monkeypatch.setattr(vs, "_port_open", lambda h, p, t: False)
    r = vs.check_xiaohongshu(5)
    assert r.status == vs.SKIP


def test_xiaohongshu_pass_when_service_up(monkeypatch):
    monkeypatch.setattr(vs, "_port_open", lambda h, p, t: True)
    monkeypatch.setattr(vs, "_http_get", lambda url, t: b"ok")
    r = vs.check_xiaohongshu(5)
    assert r.status == vs.PASS


def test_classify_error_timeout_is_blocked():
    status, _ = vs._classify_error(socket.timeout("timed out"))
    assert status == vs.BLOCKED


EVIDENCE = {
    "wechat": {
        "allowed_domains": ["mp.weixin.qq.com"],
        "items": [
            {"title": "晚点独家丨林俊旸提出离职", "url": "https://mp.weixin.qq.com/s/x"},
            {"title": "腾讯XR业务解散部分团队｜36氪独家", "url": "https://mp.weixin.qq.com/s/y"},
        ],
    },
    "xiaohongshu": {
        "allowed_domains": ["xiaohongshu.com"],
        "items": [{"title": "大厂裁员/PIP", "url": "https://www.xiaohongshu.com/x"}],
    },
}


def test_evidence_wechat_pass():
    r = vs.check_from_evidence(EVIDENCE, "wechat", "微信搜索", "微信搜索")
    assert r.status == vs.PASS
    assert "2 条" in r.detail
    assert "林俊旸" in r.sample


def test_evidence_xhs_pass():
    r = vs.check_from_evidence(EVIDENCE, "xiaohongshu", "小红书检索", "小红书检索")
    assert r.status == vs.PASS


def test_evidence_empty_is_fail():
    r = vs.check_from_evidence({"wechat": {"items": []}}, "wechat", "微信搜索", "微信搜索")
    assert r.status == vs.FAIL


def test_evidence_item_missing_url_is_fail():
    bad = {"wechat": {"items": [{"title": "缺url"}]}}
    r = vs.check_from_evidence(bad, "wechat", "微信搜索", "微信搜索")
    assert r.status == vs.FAIL


def test_run_with_evidence_passes_both():
    results = vs.run("q", 5, {"wechat", "xhs"}, evidence=EVIDENCE)
    by_cat = {r.category: r.status for r in results}
    assert by_cat["微信搜索"] == vs.PASS
    assert by_cat["小红书检索"] == vs.PASS
