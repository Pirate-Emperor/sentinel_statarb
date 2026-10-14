# Experiment notes

These numbers are saved reference results from synthetic data. They help compare code changes, but they are not live-market measurements. CPU, operating system, compiler, system load, and the selected tick count affect the results. Run the commands below again to measure a new machine.

![HPC #9 performance, IPC, and storage snapshot](assets/performance-comparison.svg)


## Python quote-policy test

**Setup:** 100,000 base ticks, 101,030 input events after deliberate duplicate insertion, a 180 bps price gap at 55% of the stream, one warm-up per policy, and three measured runs. Timing columns show the median of the measured runs.

| Policy | Events per second | Accepted signals | Held-back signals | Signal reduction | Sampled p95 | Sampled p99 |
|---|---:|---:|---:|---:|---:|---:|
| No debounce | 334,637 | 99,427 | 0 | 0.00% | 1.421 μs | 1.946 μs |
| Fixed debounce | 279,817 | 9,953 | 89,474 | 89.99% | 1.828 μs | 3.069 μs |
| Dynamic debounce | 293,107 | 9,934 | 89,493 | 90.01% | 1.820 μs | 2.756 μs |

Each policy saw the same seeded input stream. The dynamic policy held back about 90% of valid strategy signals in this test, while running risk checks independently of signal debouncing. The throughput figure includes quote generation and Python engine checks; it should not be compared directly with the native C++ benchmark.

### Quote-quality and risk results

The input stream deliberately includes **1,030 repeated sequence numbers**, **473 older timestamps**, and **100 stale quotes**. It includes no future-timestamp examples in this saved run. Each policy counted one stop trigger at the injected crash, and the 5 bps stop-limit sell price was not marketable at the observed crash price.

![Synthetic crash replay and stop-limit boundaries](assets/flash-crash-analysis.svg)


The following checks matter:

- A repeated sequence, older timestamp, stale quote, or excessive future timestamp is rejected before it can create a strategy signal.
- A valid quote can trigger a protective order even when the debouncer holds back a signal.
- An OCO order is one-shot: after the stop or take-profit fires, later quotes cannot trigger the other side.
- A 5 bps offset is a limit-price rule, not a promise that a buyer or seller will be available at that price.





## Native C++ queue and execution simulation

The checked-in 10M reference report records:

| Metric | Saved result |
|---|---:|
| Total ticks | 10,000,000 |
| Warm-up ticks excluded from timing | 10,000 |
| Timed ticks | 9,990,000 |
| Measured throughput | 34,553,787 events/s |
| Sampled processing p50 | 0.030 μs |
| Sampled processing p95 | 0.035 μs |
| Sampled processing p99 | 0.043 μs |
| Invalid synthetic ticks | 0 |

The latency values are sampled around native order/debouncer processing. They are **not** full market-to-order latency, network latency, or a guarantee for another machine. The queue benchmark also checks message order across producer and consumer threads.


## Paired native C++ vs CPython-threaded pipeline

This benchmark directly tests whether the native pipeline outperforms a comparable Python-threaded pipeline on a given machine. It runs the same deterministic unsigned-64-bit LCG quote stream through two producer/consumer implementations:

- **Native:** C++ producer, bounded SPSC ring, C++ debouncer, and stop-limit logic.
- **Python baseline:** CPython producer thread, bounded `queue.Queue`, and the project's Python debouncer/stop-limit logic.

Both use a 65,536-entry queue, identical timestamp progression and generated price path, a 100 μs base / 2 ms maximum debounce cooldown, a 5 bps stress threshold, a 25 bps stop, a 5 bps stop-limit offset, and one injected 180 bps price gap. Before reporting throughput, the script asserts parity for total ticks, accepted/debounced signals, stop count, stop-limit marketability at the gap, and invalid ticks. It discards a full warm-up invocation for each implementation, then reports medians across measured repeats and records the host and Python GIL build status.

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
python scripts/benchmark_gil_pipeline.py --ticks 1000000 --repeats 3 --out artifacts/gil_comparison_benchmark.json
python scripts/validate_reports.py
```

Throughput includes producer/consumer pipeline wait; sampled processing latency covers only the order/debouncer work. It is synthetic same-host CPU evidence, not end-to-end market latency. A GitHub-hosted run describes that runner only; use the same script on `integrator-1` before stating a benchmark result as HPC performance.

## ZeroMQ IPC round trip

The saved ZeroMQ report uses 2,000 warm-up messages followed by 20,000 measured process-to-process round trips.

| Metric | Saved result |
|---|---:|
| p50 round trip | 96.914 μs |
| p95 round trip | 294.409 μs |
| p99 round trip | 700.425 μs |
| Maximum round trip | 4,953.460 μs |
| Round trips per second | 7,559 |

The payload integrity check passed. The timing includes Python, process scheduling, and operating-system overhead. It is a **round-trip** measurement, not one-way latency.

The current saved result does not support a sub-10 μs ZeroMQ claim. The lock-free component is the native in-process SPSC ring when the platform reports its atomics as lock-free; ZeroMQ transport is a separate path and is not described as lock-free.


## Native C++ ZeroMQ IPC

The native C++ benchmark uses two separate processes and a Unix-domain `ipc://` socket. The one-way test embeds a timestamp from the host's monotonic clock in each message and measures it at the receiver. It drops 2,000 warm-up messages from the reported sample set, then checks sequence numbers and reports p50, p95, p99, maximum latency, and throughput.

```bash
sudo apt-get install libzmq3-dev pkg-config
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
./build/cpp/sentinel_zmq_ipc_oneway_benchmark --messages 20000 --warmup 2000 --out artifacts/cpp_zmq_ipc_oneway_benchmark.json
./build/cpp/sentinel_zmq_ipc_benchmark --messages 20000 --warmup 2000 --out artifacts/cpp_zmq_ipc_benchmark.json
python scripts/make_artifacts.py
python scripts/validate_reports.py
```

The one-way chart is replaced using the measured JSON file. Treat a p50 below 10 μs as met only when that measured report shows it. The benchmark is machine-dependent and is not used to claim that the ZeroMQ transport itself is lock-free. The native SPSC ring's lock-free atomics are checked separately.


The existing Python benchmark remains useful for a process-to-process request/reply path, but Python and scheduling add overhead. Its round-trip values must not be compared directly with one-way C++ latency.

The latest paced native C++ reference run measured **56.513 μs p50 one-way**, **63.731 μs p95**, and **67.720 μs p99** (20,000 messages after 2,000 warm-up messages). It did not meet the 10 μs target. The acknowledgement round trip had a p50 of 111.148 μs. Keep these measurements separate from the lock-free shared-memory ring below.

## Lock-free shared-memory SPSC IPC

The separate `sentinel_shm_spsc_ipc_benchmark` passes ticks through a single-producer/single-consumer ring in one `MAP_SHARED` memory mapping, with the producer and consumer in different processes. It checks the shared head/tail atomics with `is_lock_free()`, verifies every sequence and timestamp, excludes warm-up messages, and records p50/p95/p99 one-way handoff time. This is a different path from ZeroMQ: it does not use a ZeroMQ socket.

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
./build/cpp/sentinel_shm_spsc_ipc_benchmark --messages 200000 --warmup 20000 --capacity 64 --out artifacts/shm_spsc_ipc_benchmark.json
python scripts/run_shm_spsc_capacity_sweep.py --messages 200000 --warmup 20000 --out-dir artifacts
python scripts/make_artifacts.py
python scripts/validate_reports.py
```

The report checks and states whether the shared-memory atomics are lock-free on that host. It also sets `sub_10_us_p50` from the actual p50 result. Only use a sub-10 μs claim if that flag is true for the measured run; never infer it from the C++ processing benchmark or from ZeroMQ socket latency.


## Shared-memory queue capacity sweep

Queue size is a latency/throughput choice. A large queue can stay full while a fast producer runs ahead of the consumer, so a message may wait in the ring even when the atomic handoff itself is fast. The capacity sweep tests **16, 64, 256, and 1,024 slots**. Each setting starts a fresh producer/consumer process pair, discards a warm-up, measures 200,000 messages, and checks lock-free atomics, all sequence numbers, and all timestamps.

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
python scripts/run_shm_spsc_capacity_sweep.py --messages 200000 --warmup 20000 --out-dir artifacts
python scripts/make_artifacts.py
python scripts/validate_reports.py
```

The script saves one JSON report per capacity, plus `shm_spsc_capacity_sweep.json` and `shm_spsc_capacity_sweep.csv`. The SVG compares p50 and p99 latency with throughput. Use the smallest p50 only after checking p99, throughput, and sequence validation; do not choose a capacity from latency alone.


## DuckDB batch-size comparison

The quick CI job also runs 100,000 synthetic ticks with batch sizes of 1,000, 10,000, and 50,000 rows. Each batch-size setting gets its own warm-up database and separate measured database. The measured database is checked for the requested row count, unique sequence range, and valid bid/ask values before its throughput is compared. The sweep saves `storage_batch_sweep.json` and `storage_batch_sweep.csv`, then creates the chart below.

```bash
python scripts/run_storage_batch_sweep.py --ticks 100000 --out-dir artifacts
python scripts/make_artifacts.py
python scripts/validate_reports.py
```


## DuckDB storage stress test

Run the test with the storage extra installed:

```bash
python -m pip install -e ".[storage]"
python scripts/benchmark_storage.py --ticks 10100000 --batch-size 10000 --out artifacts/stress_ticks.duckdb
```

The CI storage job writes and verifies 10.1 million rows in a separate 120-minute job. The last completed full-scale reference measured 10,100,000 rows in 36,306 ms (about 278,190 rows/s), with 10,100,000 unique sequences from 0 through 10,099,999 and no invalid quotes. Timing depends on the runner. The script prints queued progress for both passes, performs a full warm-up write and a separate measured write. It then opens the measured database and verifies that the logger's written-row counter and the database's row count both equal the requested count, all sequence numbers are unique, and the sequence range is exactly `0` through `count - 1`. It saves timing and row checks in `artifacts/storage_benchmark.json`. The local database is ignored by Git.

A cancelled or interrupted run is not a successful result. Only report a throughput number once the read-back checks finish.

## Re-running the full test set

```bash
python -m compileall -q sentinel_runtime scripts tests
python -m unittest discover -s tests -v
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python scripts/run_experiments.py --ticks 100000 --repeats 3 --out artifacts
bash scripts/run_cpp_benchmark.sh 10000000 artifacts/cpp_benchmark_10m.json
python scripts/benchmark_zmq_ipc.py --ticks 20000 --warmup 2000 --out artifacts/zmq_ipc_benchmark.json
python scripts/make_artifacts.py
python scripts/validate_reports.py
```

GitHub Actions also runs the 10-million-row DuckDB test and uploads JSON, CSV, and SVG results as a workflow artifact.
