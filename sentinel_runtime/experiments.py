"""Repeatable synthetic tests for quote quality, signal rate limits, and stop-limit offsets."""
from __future__ import annotations
import csv, json, random, statistics, time
from pathlib import Path
from typing import Iterator
from .engine import DynamicDebouncer, ExecutionEngine, OCOStopLimit, PassthroughDebouncer, Tick
BASE_TS_NS = 1_700_000_000_000_000_000
TICK_STEP_NS = 10_000

def iter_stream(count: int = 100_000, seed: int = 20261011) -> Iterator[Tick]:
    """Stream deterministic test data without storing millions of events."""
    if count < 1: raise ValueError("count must be positive")
    rng = random.Random(seed)
    crash_at = max(1, int(count * 0.55))
    for i in range(count):
        # Bounded price noise prevents a random walk from hitting the stop before the intended crash.
        regime_price = 98.2 if i >= crash_at else 100.0
        price = regime_price * (1.0 + rng.uniform(-0.000025, 0.000025))
        ts = BASE_TS_NS + i * TICK_STEP_NS
        if i % 211 == 0 and i > 0: ts -= 5 * TICK_STEP_NS
        tick = Tick("SIM-USD", i, ts, price - 0.005, price + 0.005)
        yield tick
        if i > 0 and i % 97 == 0: yield tick

def make_stream(count: int = 100_000, seed: int = 20261011) -> list[Tick]:
    return list(iter_stream(count, seed))

def _percentile(values: list[int], p: float) -> float:
    if not values: return 0.0
    ordered = sorted(values)
    return float(ordered[min(len(ordered)-1, int((len(ordered)-1)*p))])

def _run_once(ticks: Iterator[Tick], policy: str, event_count: int, base_tick_count: int) -> dict[str, float | int | str | bool]:
    if policy == "no debounce": gate = PassthroughDebouncer()
    elif policy == "fixed debounce": gate = DynamicDebouncer(100_000, 100_000, 1_000_000_000.0)
    elif policy == "dynamic debounce": gate = DynamicDebouncer(100_000, 2_000_000, 5.0)
    else: raise ValueError(f"unknown policy: {policy}")
    engine = ExecutionEngine(gate, max_quote_age_ns=5_000_000, max_future_skew_ns=1_000_000)
    order = OCOStopLimit(100.0, "long", 25.0, 50.0, 5.0)
    engine.add_order("SIM-USD", order)
    duplicates = out_of_order = stale = future = accepted = debounced = stop_count = 0
    crash_at_sequence = max(1, int(base_tick_count * 0.55))
    post_crash_window_ticks = min(200, max(0, base_tick_count - crash_at_sequence))
    post_crash_window_end = crash_at_sequence + post_crash_window_ticks
    post_crash_window_valid_quotes = post_crash_window_accepted = post_crash_window_debounced = 0
    samples: list[int] = []
    sample_stride = max(1, event_count // 20_000)
    start = time.perf_counter_ns()
    for idx, tick in enumerate(ticks):
        receive_ns = tick.timestamp_ns + (10_000_000 if idx % 997 == 0 else 1_000)
        one_start = time.perf_counter_ns() if idx % sample_stride == 0 else 0
        result = engine.process(tick, receive_time_ns=receive_ns)
        if one_start: samples.append(time.perf_counter_ns() - one_start)
        if result.reason == "duplicate_sequence": duplicates += 1
        elif result.reason == "out_of_order_timestamp": out_of_order += 1
        elif result.reason == "stale_quote": stale += 1
        elif result.reason == "future_quote": future += 1
        elif result.accepted_signal: accepted += 1
        else: debounced += 1
        if crash_at_sequence <= tick.sequence < post_crash_window_end:
            if result.reason in ("accepted", "debounced"):
                post_crash_window_valid_quotes += 1
                if result.accepted_signal: post_crash_window_accepted += 1
                else: post_crash_window_debounced += 1
        if result.risk_event and result.risk_event.kind == "stop_triggered": stop_count += 1
    elapsed = time.perf_counter_ns() - start
    valid_signals = accepted + debounced
    return {"policy":policy,"input_events":event_count,"accepted_signals":accepted,"debounced_signals":debounced,
        "signal_reduction_pct":100.0*debounced/valid_signals if valid_signals else 0.0,
        "duplicate_sequences":duplicates,"out_of_order_timestamps":out_of_order,"stale_quotes":stale,"future_quotes":future,
        "stop_triggers":stop_count,"elapsed_ms":elapsed/1_000_000.0,"events_per_second":event_count/(elapsed/1_000_000_000.0),
        "post_crash_window_start_sequence":crash_at_sequence,"post_crash_window_ticks":post_crash_window_ticks,
        "post_crash_window_valid_quotes":post_crash_window_valid_quotes,
        "post_crash_window_accepted_signals":post_crash_window_accepted,
        "post_crash_window_debounced_signals":post_crash_window_debounced,
        "sampled_latency_p50_us":_percentile(samples,0.50)/1000.0,"sampled_latency_p95_us":_percentile(samples,0.95)/1000.0,
        "sampled_latency_p99_us":_percentile(samples,0.99)/1000.0,"stop_limit_marketable_at_crash":bool(order.limit_is_marketable(98.2))}

def oco_gap_sweep() -> list[dict[str, float | bool]]:
    rows=[]; stop_price=100.0*(1.0-25.0/10_000.0)
    for offset in (0.0,5.0,10.0):
        limit=stop_price*(1.0-offset/10_000.0)
        for gap in (0.0,1.0,2.0,5.0,7.5,10.0,25.0,50.0):
            observed=stop_price*(1.0-gap/10_000.0)
            rows.append({"offset_bps":offset,"gap_bps":gap,"limit_price":limit,"observed_price":observed,"marketable":observed>=limit})
    return rows

def run_experiments(count: int = 100_000, repeats: int = 3, seed: int = 20261011) -> dict:
    """Run one warm-up, then report medians of timed repeats."""
    if count < 1: raise ValueError("count must be positive")
    if repeats < 1: raise ValueError("repeats must be at least 1")
    event_count=count+max(0,(count-1)//97)
    policies=("no debounce","fixed debounce","dynamic debounce")
    results=[]
    for policy in policies:
        _run_once(iter_stream(count,seed),policy,event_count,count)
        runs=[_run_once(iter_stream(count,seed),policy,event_count) for _ in range(repeats)]
        chosen=dict(runs[len(runs)//2])
        for key in ("elapsed_ms","events_per_second","sampled_latency_p50_us","sampled_latency_p95_us","sampled_latency_p99_us"):
            chosen[key]=statistics.median(float(run[key]) for run in runs)
        chosen["measured_repeats"]=repeats; chosen["warmup_runs"]=1; results.append(chosen)
    gap_rows=oco_gap_sweep()
    return {"project":"Sentinel StatArb","seed":seed,"base_tick_count":count,"input_event_count_with_duplicates":event_count,
        "timestamp_step_ns":TICK_STEP_NS,"crash_at_fraction":0.55,"crash_gap_bps":180.0,
        "post_crash_signal_window_ticks":min(200,max(0,count-max(1,int(count*0.55))),
        "warmup_runs_per_policy":1,"measured_repeats_per_policy":repeats,"policies":results,"oco_gap_sweep":gap_rows,
        "notes":["Synthetic data only; rates and timings are machine-dependent.","First run is excluded from all reported timing medians.",
        "A 5 bps stop-limit offset can remain unfilled when a price gap exceeds the offset.",
        "Risk checks run for each valid quote; signal debouncing does not disable protective orders."]}

def write_reports(summary: dict, out_dir: str | Path) -> None:
    output=Path(out_dir); output.mkdir(parents=True,exist_ok=True)
    (output/"experiment_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    rows=summary["policies"]
    with (output/"experiment_metrics.csv").open("w",newline="",encoding="utf-8") as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0].keys())); writer.writeheader(); writer.writerows(rows)
    rows=summary["oco_gap_sweep"]
    with (output/"oco_gap_sweep.csv").open("w",newline="",encoding="utf-8") as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0].keys())); writer.writeheader(); writer.writerows(rows)
