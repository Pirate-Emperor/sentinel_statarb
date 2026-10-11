"""Market-event validation, adaptive signal debouncing, and OCO stop-limit logic."""
from __future__ import annotations
from dataclasses import dataclass
import math
import time
from typing import Literal

@dataclass(frozen=True, slots=True)
class Tick:
    symbol: str
    sequence: int
    timestamp_ns: int
    bid: float
    ask: float
    def __post_init__(self) -> None:
        if not self.symbol.strip(): raise ValueError("symbol must not be empty")
        if self.sequence < 0 or self.timestamp_ns < 0: raise ValueError("sequence and timestamp_ns must be non-negative")
        if not (math.isfinite(self.bid) and math.isfinite(self.ask)): raise ValueError("bid and ask must be finite")
        if self.bid <= 0 or self.ask <= 0: raise ValueError("bid and ask must be positive")
        if self.bid > self.ask: raise ValueError("bid must be less than or equal to ask")
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0

@dataclass(frozen=True, slots=True)
class RiskEvent:
    kind: Literal["stop_triggered", "take_profit_triggered"]
    symbol: str
    trigger_price: float
    limit_price: float | None
    offset_bps: float

class DynamicDebouncer:
    """Rate-limit signals and extend the quiet period after sharp moves."""
    def __init__(self, base_cooldown_ns: int = 100_000, max_cooldown_ns: int = 2_000_000, stress_bps: float = 10.0) -> None:
        if base_cooldown_ns < 0: raise ValueError("base cooldown must be non-negative")
        if max_cooldown_ns < base_cooldown_ns: raise ValueError("max cooldown must be >= base cooldown")
        if not math.isfinite(stress_bps) or stress_bps <= 0: raise ValueError("stress bps must be finite and positive")
        self.base_cooldown_ns = base_cooldown_ns
        self.max_cooldown_ns = max_cooldown_ns
        self.stress_bps = stress_bps
        self._last_signal_ns: dict[str, int] = {}
        self._last_mid: dict[str, float] = {}
        self._last_timestamp_ns: dict[str, int] = {}
        self._blocked_until_ns: dict[str, int] = {}
    def cooldown_for(self, symbol: str, mid: float) -> int:
        previous = self._last_mid.get(symbol)
        if previous is None: return self.base_cooldown_ns
        move_bps = abs(mid - previous) / previous * 10_000.0
        return min(self.max_cooldown_ns, int(self.base_cooldown_ns * (1.0 + move_bps / self.stress_bps)))
    def accept(self, symbol: str, timestamp_ns: int, mid: float) -> bool:
        if timestamp_ns < 0 or not math.isfinite(mid) or mid <= 0:
            raise ValueError("timestamp must be non-negative and mid must be positive")
        previous_timestamp = self._last_timestamp_ns.get(symbol)
        if previous_timestamp is not None and timestamp_ns < previous_timestamp:
            raise ValueError("timestamps must be monotonic for each symbol")
        self._last_timestamp_ns[symbol] = timestamp_ns
        previous_mid = self._last_mid.get(symbol)
        cooldown = self.cooldown_for(symbol, mid)
        if previous_mid is not None:
            move_bps = abs(mid - previous_mid) / previous_mid * 10_000.0
            if move_bps >= self.stress_bps:
                self._blocked_until_ns[symbol] = max(self._blocked_until_ns.get(symbol, 0), timestamp_ns + cooldown)
        self._last_mid[symbol] = mid
        previous_signal = self._last_signal_ns.get(symbol)
        if timestamp_ns < self._blocked_until_ns.get(symbol, 0): return False
        if previous_signal is not None and timestamp_ns - previous_signal < self.base_cooldown_ns: return False
        self._last_signal_ns[symbol] = timestamp_ns
        return True

class PassthroughDebouncer:
    def accept(self, symbol: str, timestamp_ns: int, mid: float) -> bool:
        del symbol, timestamp_ns, mid
        return True

class OCOStopLimit:
    """One-cancels-the-other stop/target model; a stop-limit is not a fill guarantee."""
    def __init__(self, entry_price: float, side: Literal["long", "short"] = "long", stop_bps: float = 25.0,
                 take_profit_bps: float = 50.0, limit_offset_bps: float = 5.0) -> None:
        values = (entry_price, stop_bps, take_profit_bps, limit_offset_bps)
        if not all(math.isfinite(v) for v in values): raise ValueError("order parameters must be finite")
        if entry_price <= 0 or stop_bps <= 0 or take_profit_bps <= 0: raise ValueError("entry and distances must be positive")
        if limit_offset_bps < 0 or limit_offset_bps >= 10_000 or stop_bps >= 10_000 or side not in ("long", "short"):
            raise ValueError("stop distance must be below 10000 bps and offset must be in [0, 10000) bps")
        self.entry_price, self.side = entry_price, side
        self.stop_bps, self.take_profit_bps, self.limit_offset_bps = stop_bps, take_profit_bps, limit_offset_bps
        if side == "long":
            self.stop_price = entry_price * (1.0 - stop_bps / 10_000.0)
            self.target_price = entry_price * (1.0 + take_profit_bps / 10_000.0)
        else:
            self.stop_price = entry_price * (1.0 + stop_bps / 10_000.0)
            self.target_price = entry_price * (1.0 - take_profit_bps / 10_000.0)
        self.triggered: RiskEvent | None = None
    def observe(self, symbol: str, mid: float) -> RiskEvent | None:
        if self.triggered is not None: return None
        if not math.isfinite(mid) or mid <= 0: raise ValueError("mid must be finite and positive")
        stop_hit = mid <= self.stop_price if self.side == "long" else mid >= self.stop_price
        target_hit = mid >= self.target_price if self.side == "long" else mid <= self.target_price
        if stop_hit:
            factor = 1.0 - self.limit_offset_bps / 10_000.0 if self.side == "long" else 1.0 + self.limit_offset_bps / 10_000.0
            self.triggered = RiskEvent("stop_triggered", symbol, self.stop_price, self.stop_price * factor, self.limit_offset_bps)
        elif target_hit:
            self.triggered = RiskEvent("take_profit_triggered", symbol, self.target_price, None, 0.0)
        return self.triggered
    def limit_is_marketable(self, observed_mid: float) -> bool:
        if self.triggered is None or self.triggered.kind != "stop_triggered": return False
        assert self.triggered.limit_price is not None
        return observed_mid >= self.triggered.limit_price if self.side == "long" else observed_mid <= self.triggered.limit_price

@dataclass(frozen=True, slots=True)
class ProcessResult:
    accepted_signal: bool
    reason: str
    risk_event: RiskEvent | None

class ExecutionEngine:
    """Reject invalid quote flow before signalling; keep protective checks active."""
    def __init__(self, debouncer: DynamicDebouncer | PassthroughDebouncer | None = None,
                 max_quote_age_ns: int = 5_000_000, max_future_skew_ns: int = 1_000_000) -> None:
        if max_quote_age_ns < 0 or max_future_skew_ns < 0: raise ValueError("time bounds must be non-negative")
        self.debouncer = debouncer or DynamicDebouncer()
        self.max_quote_age_ns, self.max_future_skew_ns = max_quote_age_ns, max_future_skew_ns
        self._last_sequence: dict[str, int] = {}
        self._last_timestamp: dict[str, int] = {}
        self.orders: dict[str, OCOStopLimit] = {}
    def add_order(self, symbol: str, order: OCOStopLimit) -> None:
        self.orders[symbol] = order
    def process(self, tick: Tick, receive_time_ns: int | None = None) -> ProcessResult:
        last_sequence = self._last_sequence.get(tick.symbol, -1)
        if tick.sequence <= last_sequence: return ProcessResult(False, "duplicate_sequence", None)
        self._last_sequence[tick.symbol] = tick.sequence
        previous_timestamp = self._last_timestamp.get(tick.symbol, -1)
        if tick.timestamp_ns < previous_timestamp: return ProcessResult(False, "out_of_order_timestamp", None)
        if receive_time_ns is not None:
            age = receive_time_ns - tick.timestamp_ns
            if age > self.max_quote_age_ns: return ProcessResult(False, "stale_quote", None)
            if age < -self.max_future_skew_ns: return ProcessResult(False, "future_quote", None)
        self._last_timestamp[tick.symbol] = tick.timestamp_ns
        order = self.orders.get(tick.symbol)
        risk_event = order.observe(tick.symbol, tick.mid) if order else None
        accepted = self.debouncer.accept(tick.symbol, tick.timestamp_ns, tick.mid)
        return ProcessResult(accepted, "accepted" if accepted else "debounced", risk_event)

def demo_tick(index: int, price: float, symbol: str = "DEMO") -> Tick:
    return Tick(symbol, index, time.monotonic_ns() + index * 10_000, price - 0.005, price + 0.005)
