"""Tests for framework.sourcing_gate.SourcingGate.

Time and jitter are injected so tests are deterministic and never sleep.
"""

import pytest

from framework.sourcing_gate import (
    Decision,
    SourcePolicy,
    SourcingGate,
    SECONDS_PER_DAY,
)


class FakeClock:
    """Manually-advanced clock."""

    def __init__(self, start: float = 1_000_000.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def no_jitter(_lo: float, _hi: float) -> float:
    return 0.0


def make_gate(clock, **overrides):
    policy = SourcePolicy(
        name="xiaohongshu",
        min_interval_seconds=10.0,
        jitter_seconds=0.0,
        daily_quota=3,
        block_cooldown_seconds=100.0,
        max_accounts=2,
        **overrides,
    )
    return SourcingGate({"xiaohongshu": policy}, clock=clock, jitter=no_jitter)


def test_first_request_allowed_no_wait():
    clock = FakeClock()
    gate = make_gate(clock)
    d = gate.acquire("xiaohongshu")
    assert d.allowed is True
    assert d.wait_seconds == 0.0


def test_second_request_must_wait_min_interval():
    clock = FakeClock()
    gate = make_gate(clock)
    gate.acquire("xiaohongshu")
    d = gate.acquire("xiaohongshu")
    assert d.allowed is True
    assert d.wait_seconds == pytest.approx(10.0)


def test_wait_shrinks_as_time_passes():
    clock = FakeClock()
    gate = make_gate(clock)
    gate.acquire("xiaohongshu")
    clock.advance(4.0)
    d = gate.acquire("xiaohongshu")
    assert d.wait_seconds == pytest.approx(6.0)


def test_no_wait_once_interval_elapsed():
    clock = FakeClock()
    gate = make_gate(clock)
    gate.acquire("xiaohongshu")
    clock.advance(10.0)
    d = gate.acquire("xiaohongshu")
    assert d.allowed is True
    assert d.wait_seconds == 0.0


def test_daily_quota_blocks_further_requests():
    clock = FakeClock()
    gate = make_gate(clock)  # quota = 3
    for _ in range(3):
        clock.advance(20.0)
        assert gate.acquire("xiaohongshu").allowed is True
    clock.advance(20.0)
    d = gate.acquire("xiaohongshu")
    assert d.allowed is False
    assert "配额" in d.reason


def test_quota_resets_next_day():
    clock = FakeClock()
    gate = make_gate(clock)
    for _ in range(3):
        clock.advance(20.0)
        gate.acquire("xiaohongshu")
    assert gate.acquire("xiaohongshu").allowed is False
    clock.advance(SECONDS_PER_DAY)
    assert gate.acquire("xiaohongshu").allowed is True


def test_report_block_enters_cooldown_and_rotates_account():
    clock = FakeClock()
    gate = make_gate(clock)
    first = gate.acquire("xiaohongshu")
    assert first.account_index == 0
    gate.report_block("xiaohongshu")

    d = gate.acquire("xiaohongshu")
    assert d.allowed is False
    assert "冷却" in d.reason
    assert d.wait_seconds == pytest.approx(100.0)
    assert d.account_index == 1  # rotated to the alt account


def test_cooldown_expires():
    clock = FakeClock()
    gate = make_gate(clock)
    gate.acquire("xiaohongshu")
    gate.report_block("xiaohongshu")
    clock.advance(100.0)
    d = gate.acquire("xiaohongshu")
    assert d.allowed is True


def test_repeated_blocks_escalate_cooldown():
    clock = FakeClock()
    gate = make_gate(clock)
    gate.acquire("xiaohongshu")
    gate.report_block("xiaohongshu")            # 1st block -> 100s
    clock.advance(100.0)
    gate.acquire("xiaohongshu")
    gate.report_block("xiaohongshu")            # 2nd block same day -> 200s
    d = gate.acquire("xiaohongshu")
    assert d.wait_seconds == pytest.approx(200.0)


def test_jitter_is_applied():
    clock = FakeClock()
    policy = SourcePolicy("weibo", min_interval_seconds=5.0, jitter_seconds=4.0,
                          daily_quota=10)
    gate = SourcingGate({"weibo": policy}, clock=clock, jitter=lambda lo, hi: hi)
    gate.acquire("weibo")
    d = gate.acquire("weibo")
    assert d.wait_seconds == pytest.approx(9.0)  # 5 + full jitter of 4


def test_unknown_source_raises():
    clock = FakeClock()
    gate = make_gate(clock)
    with pytest.raises(KeyError):
        gate.acquire("douyin")


def test_snapshot_reports_state():
    clock = FakeClock()
    gate = make_gate(clock)
    gate.acquire("xiaohongshu")
    snap = gate.snapshot("xiaohongshu")
    assert snap["used_today"] == 1
    assert snap["daily_quota"] == 3
    assert snap["cooling_down"] is False


def test_invalid_policy_rejected():
    with pytest.raises(ValueError):
        SourcePolicy("x", min_interval_seconds=-1.0)
    with pytest.raises(ValueError):
        SourcePolicy("x", daily_quota=-5)
    with pytest.raises(ValueError):
        SourcePolicy("x", max_accounts=0)


def test_from_yaml(tmp_path):
    cfg = tmp_path / "gate.yaml"
    cfg.write_text(
        "sources:\n"
        "  weibo:\n"
        "    min_interval_seconds: 5\n"
        "    jitter_seconds: 0\n"
        "    daily_quota: 2\n"
        "    block_cooldown_seconds: 30\n"
        "    max_accounts: 1\n",
        encoding="utf-8",
    )
    clock = FakeClock()
    gate = SourcingGate.from_yaml(cfg, clock=clock, jitter=no_jitter)
    assert gate.acquire("weibo").allowed is True
    clock.advance(5.0)
    assert gate.acquire("weibo").allowed is True
    clock.advance(5.0)
    assert gate.acquire("weibo").allowed is False  # quota = 2 exhausted
