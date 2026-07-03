"""Anti-ban gate for the《大厂茶水间》sourcing pipeline.

信源工具（搜狗微信 / 小红书 / 微博 / 微信读书系）均无官方授权，账号与 IP 极易被风控。
本模块提供一个**主动门控**：在每次对外请求前调用 ``acquire()``，由网关根据
"最小间隔 + 每日配额 + 熔断冷却"三道闸门决定是否放行，而不是等被封了才后悔。

设计原则（见 docs/anti-ban-gate.md）：
- 门控只做决策，不负责 sleep —— ``acquire()`` 返回等待秒数，由调用方决定如何等待，便于测试。
- 时间与抖动可注入（``clock`` / ``jitter``），单测无需真实等待。
- 出现封控信号（验证码 / 403 / 302 跳验证 / 小黑屋）时调用 ``report_block()``，
  立即进入冷却期并轮换账号，**禁止立刻重试**。
- 仅依赖标准库；配置可由 YAML 加载（PyYAML）。
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable, Optional

SECONDS_PER_DAY = 86_400


@dataclass(frozen=True)
class SourcePolicy:
    """单个信源的门控策略。所有阈值默认偏保守，宁缺毋滥。"""

    name: str
    min_interval_seconds: float = 8.0          # 两次请求最小间隔
    jitter_seconds: float = 4.0                # 在最小间隔上叠加 [0, jitter] 随机抖动
    daily_quota: int = 60                      # 每自然日请求上限
    block_cooldown_seconds: float = 3_600.0    # 命中封控信号后的冷却时长
    max_accounts: int = 1                      # 可轮换的账号数（小号池大小）

    def __post_init__(self) -> None:
        if self.min_interval_seconds < 0 or self.jitter_seconds < 0:
            raise ValueError(f"{self.name}: 间隔与抖动不能为负")
        if self.daily_quota < 0:
            raise ValueError(f"{self.name}: daily_quota 不能为负")
        if self.max_accounts < 1:
            raise ValueError(f"{self.name}: max_accounts 至少为 1")


@dataclass
class SourceState:
    """运行期状态，逐个信源维护。"""

    day_index: int = -1                # 当前统计所属的自然日（epoch // 86400）
    used_today: int = 0                # 今日已用配额
    next_allowed_at: float = 0.0       # 最早可再次请求的时间戳
    cooldown_until: float = 0.0        # 熔断冷却截止时间戳
    account_index: int = 0             # 当前使用的账号下标
    blocks_today: int = 0              # 今日累计封控次数（用于观测/升级冷却）


@dataclass(frozen=True)
class Decision:
    """一次 ``acquire()`` 的结果。"""

    allowed: bool
    wait_seconds: float
    reason: str
    account_index: int


class SourcingGate:
    """信源请求网关：调用 ``acquire(source)`` 判断能否放行。

    典型用法::

        gate = SourcingGate.from_yaml("examples/sourcing/anti_ban_gate.yaml")
        d = gate.acquire("xiaohongshu")
        if not d.allowed:
            # 冷却中或配额用尽 —— 直接跳过该信源，按栏目规则降级（板块可删）
            log(d.reason)
        else:
            if d.wait_seconds:
                time.sleep(d.wait_seconds)          # 满足最小间隔
            try:
                do_request(account=d.account_index)
                gate.report_success("xiaohongshu")
            except Blocked:
                gate.report_block("xiaohongshu")    # 进入冷却 + 轮换账号，禁止立刻重试
    """

    def __init__(
        self,
        policies: dict[str, SourcePolicy],
        clock: Callable[[], float] = time.time,
        jitter: Callable[[float], float] = random.uniform,
    ) -> None:
        self._policies = dict(policies)
        self._clock = clock
        self._jitter = jitter
        self._states: dict[str, SourceState] = {name: SourceState() for name in policies}

    # ---- 构造 -------------------------------------------------------------
    @classmethod
    def from_yaml(cls, path: str | Path, **kwargs) -> "SourcingGate":
        """从 YAML 加载策略。格式见 examples/sourcing/anti_ban_gate.yaml。"""
        import yaml  # 惰性导入，保持与项目"仅 PyYAML"的依赖约定一致

        raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        sources = raw.get("sources", {})
        policies: dict[str, SourcePolicy] = {}
        for name, cfg in sources.items():
            cfg = cfg or {}
            policies[name] = SourcePolicy(
                name=name,
                min_interval_seconds=float(cfg.get("min_interval_seconds", 8.0)),
                jitter_seconds=float(cfg.get("jitter_seconds", 4.0)),
                daily_quota=int(cfg.get("daily_quota", 60)),
                block_cooldown_seconds=float(cfg.get("block_cooldown_seconds", 3_600.0)),
                max_accounts=int(cfg.get("max_accounts", 1)),
            )
        return cls(policies, **kwargs)

    # ---- 内部 -------------------------------------------------------------
    def _state(self, source: str) -> SourceState:
        if source not in self._policies:
            raise KeyError(f"未配置的信源: {source!r}（已配置: {sorted(self._policies)}）")
        return self._states[source]

    def _roll_day(self, state: SourceState, now: float) -> None:
        """跨自然日则重置每日计数。"""
        today = int(now // SECONDS_PER_DAY)
        if today != state.day_index:
            state.day_index = today
            state.used_today = 0
            state.blocks_today = 0

    # ---- 决策 -------------------------------------------------------------
    def acquire(self, source: str) -> Decision:
        """判断当前是否可对 ``source`` 发起一次请求。

        不会 sleep、不改变"已用配额"以外的放行计数 —— 放行即视为将要发出一次请求，
        因此会占用一个配额名额并推进最小间隔时钟。若返回 ``allowed=False``，调用方应
        **跳过**该信源（冷却/配额），或 ``allowed=True`` 但 ``wait_seconds>0`` 时先等待。
        """
        policy = self._policies[source]
        state = self._state(source)
        now = self._clock()
        self._roll_day(state, now)

        # 闸门一：熔断冷却
        if now < state.cooldown_until:
            return Decision(False, state.cooldown_until - now,
                            f"{source} 冷却中（封控后回避），剩余 "
                            f"{int(state.cooldown_until - now)}s", state.account_index)

        # 闸门二：每日配额
        if state.used_today >= policy.daily_quota:
            return Decision(False, 0.0,
                            f"{source} 今日配额已用尽（{policy.daily_quota}），"
                            f"明日再来或降级该板块", state.account_index)

        # 闸门三：最小间隔（放行，但可能需要等待）
        wait = max(0.0, state.next_allowed_at - now)

        # 放行：占用配额并推进节流时钟（含随机抖动，规避规律性特征）
        interval = policy.min_interval_seconds + self._jitter(0.0, policy.jitter_seconds)
        state.next_allowed_at = now + wait + interval
        state.used_today += 1
        return Decision(True, wait,
                        f"{source} 放行（今日 {state.used_today}/{policy.daily_quota}）",
                        state.account_index)

    def report_success(self, source: str) -> None:
        """请求成功：目前无需额外处理，保留为对称接口/未来扩展点。"""
        self._state(source)  # 校验 source 合法

    def report_block(self, source: str) -> None:
        """请求命中封控信号（验证码 / 403 / 302 跳验证 / 小黑屋）。

        立即进入冷却期并轮换到下一个账号。**禁止立刻重试** —— 冷却结束前
        ``acquire()`` 都会拒绝该信源。
        """
        policy = self._policies[source]
        state = self._state(source)
        now = self._clock()
        self._roll_day(state, now)
        state.blocks_today += 1
        # 同日多次被封 → 冷却时长线性加倍，越撞越退避
        cooldown = policy.block_cooldown_seconds * state.blocks_today
        state.cooldown_until = now + cooldown
        state.next_allowed_at = state.cooldown_until
        if policy.max_accounts > 1:
            state.account_index = (state.account_index + 1) % policy.max_accounts

    # ---- 观测 -------------------------------------------------------------
    def snapshot(self, source: Optional[str] = None) -> dict:
        """返回当前门控状态，便于日志/巡检。"""
        names = [source] if source else list(self._policies)
        now = self._clock()
        out: dict[str, dict] = {}
        for name in names:
            st = self._state(name)
            pol = self._policies[name]
            out[name] = {
                "used_today": st.used_today,
                "daily_quota": pol.daily_quota,
                "cooling_down": now < st.cooldown_until,
                "cooldown_remaining_s": max(0, int(st.cooldown_until - now)),
                "blocks_today": st.blocks_today,
                "account_index": st.account_index,
            }
        return out if source is None else out[source]

    def policy(self, source: str) -> SourcePolicy:
        """返回某信源的策略副本（只读）。"""
        return replace(self._policies[source])
