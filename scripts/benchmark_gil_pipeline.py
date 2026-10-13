#!/usr/bin/env python3
"""Paired native-C++ vs CPython-threaded execution-pipeline benchmark.

Both implementations generate the same deterministic LCG price stream, feed a
bounded producer/consumer queue of 65,536 entries, apply the same dynamic
debounce configuration and a 25 bps stop with a 5 bps limit offset, and check
the same counters. This is a CPU benchmark, not a market-latency measurement.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import queue
import statistics
import subprocess
import sys
import sysconfig
import threading
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sentinel_runtime.engine import DynamicDebouncer, OCOStopLimit

QUEUE_CAPACITY = 1 << 16
MASK64 = (1 << 64) - 1
LCG_MULTIPLIER = 6364136223846793005
LCG_INCREMENT = 1442695040888963407
LCG_INITIAL = 0x9E3779B97F4A7C15
TICK_STEP_NS = 10_000
BASE_COOLDOWN_NS = 100_000
MAX_COOLDOWN_NS = 2_000_000
STRESS_BPS = 5.0
STOP_BPS = 25.0
LIMIT_OFFSET_BPS = 5.0


def percentile(values: list[int], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    return float(ordered[min(len(ordered) - 1, int((len(ordered) - 1) * p))])


def run_python_pipeline(tick_count: int) -> dict[str, Any]:
    """Measure a bounded Python producer/consumer queue and project risk logic."""
    if tick_count < 1:
        raise ValueError("tick_count must be positive")

    warmup_ticks = min(tick_count // 10, 10_000)
    stride = max(1, tick_count // 20_000)
    ticks: queue.Queue[tuple[int, int, float, float]] = queue.Queue(maxsize=QUEUE_CAPACITY)
    gate = DynamicDebouncer(BASE_COOLDOWN_NS, MAX_COOLDOWN_NS, STRESS_BPS)
    order = OCOStopLimit(100.0, "long", STOP_BPS, 50.0, LIMIT_OFFSET_BPS)
    state: dict[str, Any] = {
        "accepted": 0,
        "debounced": 0,
        "stop_triggers": 0,
        "invalid_ticks": 0,
        "stop_marketable_at_gap": False,
    }
    samples_ns: list[int] = []
    error: list[BaseException] = []

    def produce() -> None:
        rng = LCG_INITIAL
        try:
            for i in range(tick_count):
                rng = (rng * LCG_MULTIPLIER + LCG_INCREMENT) & MASK64
                noise = (float((rng >> 33) % 2001) - 1000.0) / 100_000_000.0
                base = 98.2 if i >= tick_count // 2 else 100.0
                price = base + noise
                ticks.put((i, i * TICK_STEP_NS, price - 0.005, price + 0.005))
        except BaseException as exc:  # propagate worker errors rather than hanging silently
            error.append(exc)

    producer = threading.Thread(target=produce, name="sentinel-python-producer", daemon=True)
    producer.start()
    consumed = 0
    start_ns = 0
    finish_ns = 0
    while consumed < tick_count:
        sequence, timestamp_ns, bid, ask = ticks.get()
        mid = (bid + ask) * 0.5
        if bid <= 0 or ask < bid or not (mid > 0.0):
            state["invalid_ticks"] += 1
            consumed += 1
            continue

        if consumed == warmup_ticks:
            start_ns = time.perf_counter_ns()
        sampled = consumed >= warmup_ticks and consumed % stride == 0
        sample_start = time.perf_counter_ns() if sampled else 0

        event = order.observe("SIM-USD", mid)
        if event is not None:
            state["stop_triggers"] += 1
            state["stop_marketable_at_gap"] = order.limit_is_marketable(mid)
        if gate.accept("SIM-USD", timestamp_ns, mid):
            state["accepted"] += 1
        else:
            state["debounced"] += 1

        if sampled:
            samples_ns.append(time.perf_counter_ns() - sample_start)
        consumed += 1
        if consumed == tick_count:
            finish_ns = time.perf_counter_ns()

    producer.join()
    if error:
        raise RuntimeError("Python producer failed") from error[0]
    elapsed_ns = max(1, finish_ns - start_ns)
    measured_ticks = tick_count - warmup_ticks

    return {
        "ticks": tick_count,
        "warmup_ticks": warmup_ticks,
        "measured_ticks": measured_ticks,
        "measured_throughput_events_per_second": measured_ticks / (elapsed_ns / 1e9),
        "sampled_processing_p50_us": percentile(samples_ns, 0.50) / 1000.0,
        "sampled_processing_p95_us": percentile(samples_ns, 0.95) / 1000.0,
        "sampled_processing_p99_us": percentile(samples_ns, 0.99) / 1000.0,
        "latency_sample_count": len(samples_ns),
        "signals_accepted": state["accepted"],
        "signals_debounced": state["debounced"],
        "stop_triggers": state["stop_triggers"],
        "stop_limit_marketable_at_gap": state["stop_marketable_at_gap"],
        "invalid_ticks": state["invalid_ticks"],
        "queue_capacity": QUEUE_CAPACITY,
        "queue_lock_free_atomics": False,
    }


def parse_native_stdout(stdout: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for line in stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if value in ("true", "false"):
            result[key] = value == "true"
        else:
            try:
                result[key] = float(value) if "." in value else int(value)
            except ValueError:
                result[key] = value
    return result


def run_native(binary: Path, tick_count: int) -> dict[str, Any]:
    completed = subprocess.run(
        [str(binary), "--ticks", str(tick_count)],
        check=True,
        capture_output=True,
        text=True,
        timeout=300,
    )
    result = parse_native_stdout(completed.stdout)
    required = {
        "ticks", "warmup_ticks", "measured_ticks",
        "measured_throughput_events_per_second",
        "sampled_processing_p50_us", "sampled_processing_p95_us",
        "sampled_processing_p99_us", "latency_sample_count",
        "signals_accepted", "signals_debounced", "stop_triggers",
        "stop_limit_marketable_at_gap", "invalid_ticks",
        "queue_lock_free_atomics",
    }
    missing = required - result.keys()
    if missing:
        raise RuntimeError(f"native C++ benchmark output missing keys: {sorted(missing)}")
    result["queue_capacity"] = QUEUE_CAPACITY
    return result


def median_run_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    numeric = (
        "measured_throughput_events_per_second",
        "sampled_processing_p50_us",
        "sampled_processing_p95_us",
        "sampled_processing_p99_us",
    )
    result: dict[str, Any] = {
        key: statistics.median(float(row[key]) for row in rows) for key in numeric
    }
    result["latency_sample_count"] = int(statistics.median(
        int(row["latency_sample_count"]) for row in rows
    ))
    # Counters are deterministic; fail if any measured repetition diverges.
    for key in (
        "ticks", "warmup_ticks", "measured_ticks", "signals_accepted",
        "signals_debounced", "stop_triggers", "stop_limit_marketable_at_gap",
        "invalid_ticks", "queue_capacity", "queue_lock_free_atomics",
    ):
        values = [row[key] for row in rows]
        if any(value != values[0] for value in values[1:]):
            raise RuntimeError(f"run-to-run mismatch in {key}: {values}")
        result[key] = values[0]
    result["measured_runs"] = len(rows)
    result["raw_measured_runs"] = rows
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticks", type=int, default=1_000_000)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--native-binary", type=Path, default=ROOT / "build" / "cpp" / "sentinel_engine")
    parser.add_argument("--out", type=Path, default=ROOT / "artifacts" / "gil_comparison_benchmark.json")
    args = parser.parse_args()
    if args.ticks < 1 or args.repeats < 1:
        parser.error("--ticks and --repeats must be positive")

    binary = args.native_binary.resolve()
    if not binary.is_file():
        parser.error(f"native binary not found: {binary}; build the project first")

    # Each implementation gets a full discarded warm-up run; measured runs alternate
    # so that one implementation does not always run on a colder/warmer host.
    run_native(binary, args.ticks)
    run_python_pipeline(args.ticks)
    native_rows: list[dict[str, Any]] = []
    python_rows: list[dict[str, Any]] = []
    for _ in range(args.repeats):
        native_rows.append(run_native(binary, args.ticks))
        python_rows.append(run_python_pipeline(args.ticks))

    native = median_run_summary(native_rows)
    python = median_run_summary(python_rows)
    parity_keys = (
        "ticks", "warmup_ticks", "measured_ticks", "signals_accepted",
        "signals_debounced", "stop_triggers", "stop_limit_marketable_at_gap",
        "invalid_ticks", "queue_capacity",
    )
    parity = {
        key: {"native_cpp": native[key], "python_threaded": python[key], "match": native[key] == python[key]}
        for key in parity_keys
    }
    parity_passed = all(item["match"] for item in parity.values())
    if not parity_passed:
        mismatches = {key: item for key, item in parity.items() if not item["match"]}
        raise RuntimeError(f"native/Python semantic parity failed: {mismatches}")

    native_rate = float(native["measured_throughput_events_per_second"])
    python_rate = float(python["measured_throughput_events_per_second"])
    gil_disabled = sysconfig.get_config_var("Py_GIL_DISABLED")
    report = {
        "benchmark": "paired_native_cpp_vs_python_threaded_execution_pipeline",
        "ticks_per_run": args.ticks,
        "warmup_invocations_per_implementation": 1,
        "measured_repeats_per_implementation": args.repeats,
        "workload": {
            "generator": "identical unsigned-64-bit LCG; bounded price noise; one injected 180 bps gap",
            "queue_capacity": QUEUE_CAPACITY,
            "pipeline": "one producer thread and one consumer thread",
            "risk_logic": "same 100 ns base/2,000 ns max-equivalent cooldown scale, 5 bps stress threshold, 25 bps stop, and 5 bps stop-limit offset",
            "scope": "same-host synthetic CPU pipeline; excludes network, broker, and real market-data latency",
        },
        "host": {
            "platform": platform.platform(),
            "python_implementation": sys.implementation.name,
            "python_version": platform.python_version(),
            "python_gil_enabled": (not bool(gil_disabled)) if sys.implementation.name == "cpython" else None,
            "logical_cpu_count": os.cpu_count(),
            "native_binary": str(binary),
        },
        "native_cpp": native,
        "python_threaded": python,
        "native_cpp_speedup_over_python_threaded": native_rate / python_rate if python_rate > 0 else None,
        "semantic_parity": {"passed": parity_passed, "checks": parity},
        "notes": [
            "Throughput is a measured producer/consumer pipeline result, not end-to-end trading latency.",
            "Sampled processing latency times only the order/debounce work; queue wait is included in throughput, not those samples.",
            "The Python variant uses CPython threads and queue.Queue; when the host build has the GIL enabled, CPU-bound Python bytecode cannot execute in parallel across those threads.",
            "Benchmark values depend on CPU, scheduler, compiler, and host load. Run this on the intended HPC host before making an HPC-specific claim.",
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "report": str(args.out),
        "native_cpp_events_per_second_median": native_rate,
        "python_threaded_events_per_second_median": python_rate,
        "native_cpp_speedup_over_python_threaded": report["native_cpp_speedup_over_python_threaded"],
        "semantic_parity": parity_passed,
        "python_gil_enabled": report["host"]["python_gil_enabled"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
