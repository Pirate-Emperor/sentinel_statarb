"""Sentinel StatArb: a small market-event and risk simulation core."""
from .engine import DynamicDebouncer, ExecutionEngine, OCOStopLimit, Tick
__all__ = ["DynamicDebouncer", "ExecutionEngine", "OCOStopLimit", "Tick"]
