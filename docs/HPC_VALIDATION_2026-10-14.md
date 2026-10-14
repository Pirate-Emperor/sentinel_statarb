# Sentinel StatArb — HPC validation report

**Run:** [Sentinel StatArb HPC CPU Validation #8](https://github.com/SpryzenHell/integrator/actions/runs/38569070387)  
**Outcome:** success  
**Sentinel StatArb source commit tested:** `4958b6dde6f8bda5dbbfc4b52b72adb2b64c7d43`  
**Machine-readable reports:** [`integrator/main/artifacts/sentinel-statarb-hpc/`](https://github.com/SpryzenHell/integrator/tree/main/artifacts/sentinel-statarb-hpc)

## Host and test conditions

- Host: `scn11-mn.mgmt.siddhi.param`; Ubuntu 22.04.4; Linux 5.15.
- CPU: dual AMD EPYC 7742 64-Core processors; 128 physical cores / 256 logical CPUs reported by `lscpu`.
- GPU present: 2× NVIDIA A100-SXM4-40GB; Driver 550.90.07 / CUDA 12.4. The measured project workload was CPU-only and did not launch CUDA kernels.
- Toolchain: GCC 11.4.0, CMake 3.22.1, CPython 3.12.15.
- Validation: 24 Python unit/integration tests passed; 4/4 CTest native tests passed; generated reports and SVG checks passed.

## 1. Native C++ engine and CPython/GIL comparison

### 10M-tick native run

| Metric | HPC result |
|---|---:|
| Synthetic ticks | 10,000,000 |
| Warm-up ticks excluded from throughput | 10,000 |
| Measured ticks | 9,990,000 |
| Throughput | 37,767,022 events/s |
| Sampled processing p50 | 0.050 μs |
| Sampled processing p95 | 0.051 μs |
| Sampled processing p99 | 0.051 μs |
| Invalid ticks | 0 |
| Queue atomics lock-free on host | true |

Sampled processing latency surrounds only the native order/debouncer hot path. It is not end-to-end market-to-order latency. Throughput is the full measured producer/consumer simulation rate and is not interchangeable with the sampled hot-path timing.

### Paired native-vs-Python threaded pipeline

The benchmark ran the same seeded one-million-tick price path, timestamp progression, queue capacity, debounce rules, and stop-limit settings in native C++ and in a CPython producer/consumer pipeline. One warm-up invocation per implementation was excluded; five measured runs were recorded. This CPython build reported the GIL enabled.

| Metric | Native C++ | CPython threaded |
|---|---:|---:|
| Median throughput | 48,794,396 events/s | 264,621 events/s |
| Sampled processing p50 | 0.040 μs | 1.333 μs |
| Sampled processing p95 | 0.051 μs | 1.483 μs |
| Sampled processing p99 | 0.051 μs | 1.593 μs |

**Measured throughput ratio: 184.39× in favor of native C++.** Semantic parity passed for all checked fields: tick/warm-up counts, accepted and debounced signal counts, one stop trigger, stop-limit marketability after the crash gap, zero invalid ticks, and queue capacity. Raw throughput repeats are included in the JSON report.

This measures a complete C++ SPSC-vs-CPython `queue.Queue` producer/consumer pipeline, so the ratio includes queue implementation, Python object/interpreter overhead, and the GIL; it must not be described as an isolated measurement of GIL overhead alone. It establishes a machine- and workload-specific HPC comparison, not a universal speedup.

## 2. Dynamic debouncer and 5 bps OCO stop-limit

The 100K seeded synthetic replay injects duplicate sequence numbers, older timestamps, stale quotes, and a 180 bps price gap. The gap is intentionally larger than the stop-limit offset.

| Policy | Accepted signals | Held-back signals | Stop triggers | Stop-limit marketable after gap? |
|---|---:|---:|---:|---|
| No debounce | 99,427 | 0 | 1 | No |
| Fixed debounce | 9,953 | 89,474 | 1 | No |
| Dynamic debounce | 9,934 | 89,493 | 1 | No |

Dynamic debounce accepted **90.01% fewer signals** than the no-debounce policy in this experiment. Each policy's protective-order check still triggered once; after the 180 bps gap, the 5 bps-offset stop-limit was not marketable. Unit tests also verify the exact 5 bps price calculation, one-shot OCO behavior, invalid settings, and order checks even when the signal itself is debounced.

These are synthetic signal-control and order-price tests, not realized P&L, live fills, or proof of a specific reduction in real-market loss. A stop-limit order can trigger yet remain unfilled after a gap.

## 3. Quote integrity, IPC and async DuckDB persistence

### Quote validation

The HPC replay counted 1,030 duplicate-sequence events, 473 older-timestamp events, and 100 stale events; they were rejected before signals were created. Separate tests exercise excessively future-dated quote rejection. The current seeded stress stream has no future-dated samples, so its future count is zero.

### Lock-free shared-memory IPC

The shared-memory SPSC ring uses process-shared `MAP_SHARED` memory and atomics checked with `is_lock_free()`. The queue-capacity sweep used 200,000 measured messages after 20,000 warm-up messages per capacity.

| Capacity | p50 one-way | p95 one-way | p99 one-way | Throughput |
|---:|---:|---:|---:|---:|
| 16 | 3.397 μs | 3.887 μs | 6.102 μs | 2.48M messages/s |
| 64 | 7.434 μs | 10.500 μs | 12.172 μs | 4.75M messages/s |
| 256 | 24.386 μs | 28.254 μs | 30.127 μs | 6.46M messages/s |
| 1,024 | 90.661 μs | 107.935 μs | 112.243 μs | 7.11M messages/s |

**The lowest-latency tested setting was capacity 16: p50 3.397 μs and p99 6.102 μs**, with zero sequence/timestamp errors and lock-free atomics. Its maximum observed latency was 1,428.499 μs, so the result is a percentile claim—not a guarantee that every handoff stays below 10 μs. Capacity 64 showed p99 12.263 μs in the standalone run, demonstrating scheduler/backlog sensitivity.

### ZeroMQ is separate from lock-free IPC

| Native ZeroMQ path | p50 | p95 | p99 |
|---|---:|---:|---:|
| One-way IPC | 25.999 μs | 27.863 μs | 31.009 μs |
| Request/reply round trip | 51.398 μs | 56.848 μs | 61.456 μs |

Payload and sequence checks passed, but **ZeroMQ is not lock-free and did not meet the sub-10 μs target**. The low-latency lock-free result comes from the separate shared-memory SPSC transport. Do not describe it as “lock-free ZeroMQ IPC.”

### DuckDB stress test

| Metric | HPC result |
|---|---:|
| Warm-up rows | 10,100,000 |
| Measured rows requested | 10,100,000 |
| Rows written | 10,100,000 |
| Rows read back | 10,100,000 |
| Distinct sequence IDs | 10,100,000 |
| Sequence range | 0–10,099,999 |
| Invalid bid/ask rows | 0 |
| Measured elapsed time | 41.789 s |
| Throughput | 241,690 rows/s |
| Database size | 136,065,024 bytes |

The async writer completed both the warm-up and measured pass; every requested row was present on read-back, all sequences were unique, and all bid/ask values passed validation.

## Resume-bullet assessment after the HPC run

1. **Native C++ / GIL:** verified on the named HPC host for the specific synthetic pipeline. A paired run showed 184.39× throughput versus the GIL-enabled CPython-threaded baseline with semantic parity. The 10M-tick native simulation measured 37.77M events/s and 0.051 μs sampled p99 hot-path processing.
2. **Debouncer / OCO:** verified as synthetic backtest behavior: about 90.01% fewer accepted signals than no debouncing, with 5 bps OCO stop-limit checks and an exercised gap-through case. This does not prove improved live P&L or guaranteed fills.
3. **Quote integrity / IPC / storage:** stale, duplicate, out-of-order, and future timestamp guards are tested. The capacity-16 shared-memory SPSC path achieved p99 6.102 μs with lock-free atomics; ZeroMQ's separate latency was above 10 μs and is not lock-free. Async DuckDB write/read-back verified 10.1M rows with zero invalid quotes.

## Artifacts and reproducibility

- [HPC workflow run #8 (success)](https://github.com/SpryzenHell/integrator/actions/runs/38569070387)
- [Persisted HPC JSON/CSV reports and machine information on `integrator/main`](https://github.com/SpryzenHell/integrator/tree/main/artifacts/sentinel-statarb-hpc)
- [Paired benchmark source](https://github.com/SpryzenHell/sentinel_statarb/blob/main/scripts/benchmark_gil_pipeline.py)
- [Report validator](https://github.com/SpryzenHell/sentinel_statarb/blob/main/scripts/validate_reports.py)

All inputs in the benchmark remain synthetic. The run validates code paths and measurements on the HPC machine; it is not a live trading deployment or a claim of market profitability.
