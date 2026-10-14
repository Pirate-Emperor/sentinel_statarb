# Sentinel StatArb

**A small market-event test system using C++17, Python, ZeroMQ, and DuckDB.**

Sentinel StatArb tests how fast quote streams behave when they contain repeated messages, old timestamps, stale quotes, and a sudden price gap. It combines a native C++ queue simulation with Python checks for signal control, protective stop-limit orders, message transport, and batch storage.

All examples use synthetic data. The project does not connect to a broker or place live orders.

## At a glance

- **Native C++ engine:** SPSC ring buffer and an event-processing benchmark. The benchmark reports whether its atomics are lock-free on the current machine.
- **Paired GIL comparison:** Runs the same deterministic synthetic quote stream through native C++ and a CPython producer/consumer pipeline, enforces output parity, and measures the throughput ratio after warm-up. The host is recorded; an HPC claim requires a report produced on the HPC machine.
- **Quote checks:** Reject repeated sequence numbers, out-of-order timestamps, stale quotes, and timestamps too far in the future.
- **Dynamic debouncer:** Holds back repeated strategy signals for longer after a sharp price move. Protective order checks still run for every quote that passes the quality checks.
- **OCO stop-limit model:** Tests stop/target behavior and a 5 bps stop-limit offset. A triggered stop-limit order can remain unfilled after a large gap.
- **ZeroMQ bridge:** Sends validated tick messages over IPC or TCP. Native C++ tests measure one-way and round-trip latency separately. ZeroMQ itself is not lock-free, and the saved run did not meet the 10 μs one-way target.
- **Lock-free shared-memory IPC:** A native SPSC ring passes messages between two processes using shared memory. The benchmark checks whether the atomic counters are actually lock-free on the host, verifies sequence order, and measures one-way handoff time.
- **DuckDB writer:** Uses a bounded queue and a separate writer thread. Pandas DataFrame batches reduce per-row insert overhead; read-back checks verify every sequence and quote.
- **Repeatable experiments:** Save CSV/JSON measurements and SVG diagrams for the quote policies, crash scenario, and timing results.

## System view

![Sentinel StatArb architecture](docs/assets/architecture.svg)

![Quote validation and risk flow](docs/assets/execution-flow.svg)

## Quick start

Requirements: Python 3.10+, a C++17 compiler, and CMake 3.16+. The native ZeroMQ benchmark is optional and needs the libzmq development package plus pkg-config (for Ubuntu: `sudo apt-get install libzmq3-dev pkg-config`).

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e ".[ipc,storage,dev]"
```

Build and test the C++ code:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Run Python tests and validate the saved reports:

```bash
python -m unittest discover -s tests -v
python scripts/validate_reports.py
```

Run the combined local checks:

```bash
bash scripts/run_checks.sh
```

The combined script runs smaller storage checks by default. Set `SENTINEL_STORAGE_TICKS=10100000` to verify more than 10 million rows locally.

## Repeatable experiments

The experiment script runs one warm-up for each policy, then measures repeated runs and reports the median timing. The timing excludes that policy's warm-up run.

```bash
# Python quote and risk experiment
python scripts/run_experiments.py --ticks 100000 --repeats 3
python scripts/run_experiments.py --ticks 1000000 --repeats 3

# Native C++ benchmark: warm-up run, then measured run
bash scripts/run_cpp_benchmark.sh 1000000 artifacts/cpp_benchmark.json
bash scripts/run_cpp_benchmark.sh 10000000 artifacts/cpp_benchmark_10m.json

# Paired native C++ vs CPython-threaded execution pipeline
python scripts/benchmark_gil_pipeline.py --ticks 1000000 --repeats 3 --out artifacts/gil_comparison_benchmark.json

# Python ZeroMQ process-to-process round trip
python scripts/benchmark_zmq_ipc.py --ticks 20000 --warmup 2000 --out artifacts/zmq_ipc_benchmark.json

# Native C++ ZeroMQ IPC benchmarks (after installing libzmq3-dev and pkg-config)
./build/cpp/sentinel_shm_spsc_ipc_benchmark --messages 200000 --warmup 20000 --capacity 64 --out artifacts/shm_spsc_ipc_benchmark.json
python scripts/run_shm_spsc_capacity_sweep.py --messages 200000 --warmup 20000 --out-dir artifacts
./build/cpp/sentinel_zmq_ipc_oneway_benchmark --messages 20000 --warmup 2000 --out artifacts/cpp_zmq_ipc_oneway_benchmark.json
./build/cpp/sentinel_zmq_ipc_benchmark --messages 20000 --warmup 2000 --out artifacts/cpp_zmq_ipc_benchmark.json

# Separate warm-up and measured DuckDB writes, then verify every row and sequence
python scripts/benchmark_storage.py --ticks 10100000 --batch-size 10000 --out artifacts/stress_ticks.duckdb

# Compare batch sizes using 100K ticks per run
python scripts/run_storage_batch_sweep.py --ticks 100000 --out-dir artifacts

# Refresh the diagrams from the saved JSON reports
python scripts/make_artifacts.py
python scripts/validate_reports.py
```

The DuckDB command writes a separate warm-up database and measured database. It reads the measured database back and checks the row count, distinct sequence count, sequence range, and bid/ask values. It prints progress during both passes. Database files are local test outputs and are not meant to be committed.

GitHub Actions runs the unit tests, native C++ queue tests, 100K quote experiments, 1M and 10M C++ processing benchmarks, native shared-memory and ZeroMQ tests, and real DuckDB write/read-back tests in the regular job. A separate 120-minute job runs the 10M-row DuckDB warm-up and measured passes so the normal 30-minute test limit cannot cancel it. A run is successful only when the report and data checks finish. See [the workflow](.github/workflows/ci.yml).

## Analysis and experiment images

![Experiment pipeline](docs/assets/experiment-pipeline.svg)

![Quote data-quality counts](docs/assets/data-quality.svg)

![Signal policy performance comparison](docs/assets/performance-comparison.svg)

![Synthetic flash-crash scenario](docs/assets/flash-crash-analysis.svg)

![Stop-limit gap sweep](docs/assets/oco-gap-sweep.svg)

![Native C++ benchmark](docs/assets/cpp-benchmark.svg)

![Python ZeroMQ IPC round-trip benchmark](docs/assets/zmq-ipc-latency.svg)

![Native C++ ZeroMQ one-way IPC latency](docs/assets/zmq-ipc-oneway-latency.svg)

![Lock-free shared-memory SPSC IPC latency](docs/assets/shm-spsc-ipc-latency.svg)

![Shared-memory queue-capacity sweep](docs/assets/shm-spsc-capacity-sweep.svg)

![DuckDB batch-size comparison](docs/assets/storage-batch-sweep.svg)

See the [experiment notes](docs/EXPERIMENTS.md) and [reports and diagrams index](docs/README.md) for the saved results and how to reproduce them.

## Reading the numbers correctly

The checked-in JSON/CSV files and diagrams are reference runs from synthetic data. Throughput and latency change with the CPU, operating system, compiler, process scheduling, and test settings. Re-run the commands above to produce results for your machine.

### Verification status — HPC run completed successfully

**[integrator-1 HPC CPU Validation #8 passed](https://github.com/SpryzenHell/integrator/actions/runs/38569070387)** on `scn11-mn.mgmt.siddhi.param` (dual AMD EPYC 7742 CPUs; 2× A100 GPUs present but not used by this CPU benchmark; Ubuntu 22.04, GCC 11.4, CPython 3.12.15). The tested Sentinel StatArb source was `4958b6dde6f8bda5dbbfc4b52b72adb2b64c7d43`. Python tests passed 24/24, native CTest passed 4/4, and all generated-report validation checks passed.

| Claim area | Measured HPC evidence | Important boundary |
|---|---|---|
| Native C++ execution engine | 10M synthetic ticks: **37.77M events/s**, 0.050 μs sampled p50 and **0.051 μs sampled p99** processing latency; zero invalid ticks. | Sampled timing wraps order/debouncer processing, not end-to-end market-to-order latency. |
| Python GIL comparison | On the paired 1M-tick workload: native C++ **48.79M events/s** vs GIL-enabled CPython producer/consumer **264.6K events/s**; **184.39×** measured pipeline throughput ratio. Signal counts, stop outcome and invalid-tick checks matched. | This compares the full native SPSC pipeline with Python `queue.Queue`, including object/queue overhead—not isolated GIL overhead alone. Host/workload-specific. |
| Dynamic debouncer + 5 bps OCO | Accepted signals fell from **99,427** without debounce to **9,934** with dynamic debounce (**90.01% fewer**). The 180 bps crash gap triggered the stop, but the 5 bps-offset stop-limit was not marketable afterward. | Synthetic backtest only; this does not establish live P&L, actual slippage reduction, or guaranteed fills. |
| Quote integrity + lock-free IPC | Duplicate/out-of-order/stale quote rejection verified; shared-memory SPSC capacity 16 delivered **3.397 μs p50 / 6.102 μs p99** with lock-free atomics and zero sequence/timestamp errors. | The low-latency path is **shared-memory SPSC, not ZeroMQ**. ZeroMQ one-way p50/p99 were 25.999/31.009 μs and its transport is not lock-free. The shared-memory maximum also had scheduler outliers, so quote percentiles rather than an absolute bound. |
| Async DuckDB logging | **10.1M rows** written and read back; 10.1M distinct sequences spanning 0–10,099,999; zero invalid quotes; **241.7K rows/s** in the measured pass (41.79 s). | Synthetic data and host-specific disk/CPU throughput. |

Full host details, raw metrics, IPC capacity sweep, OCO gap test, and caveats are recorded in [the HPC validation report](docs/HPC_VALIDATION_2026-10-14.md). Machine-readable results are persisted under [`integrator/main/artifacts/sentinel-statarb-hpc/`](https://github.com/SpryzenHell/integrator/tree/main/artifacts/sentinel-statarb-hpc).

### Resume wording supported by current evidence

- **Native engine:** Built a native C++17 execution simulator; on an AMD EPYC HPC node it processed 10M synthetic ticks at 37.77M events/s (0.051 μs sampled p99 hot-path processing). A paired GIL-enabled CPython pipeline benchmark showed 184.39× higher measured throughput with execution/risk parity.
- **Crash controls:** Implemented dynamic signal debouncing and 5 bps OCO stop-limit protection; in a seeded 180 bps crash-gap replay, dynamic debounce accepted 90.01% fewer signals than no debounce, and the test confirmed that a gap-through stop-limit can remain unfilled.
- **Quote integrity / persistence:** Rejected duplicate, out-of-order and stale quotes; benchmarked lock-free process-shared SPSC IPC at 3.397 μs p50 / 6.102 μs p99 and asynchronously wrote/read-validated 10.1M DuckDB rows with zero invalid quotes.

Do not label the low-latency shared-memory IPC result as “lock-free ZeroMQ,” and do not claim live-market profitability based on these synthetic tests.

## Main files

- `sentinel_runtime/`: Python quote validation, debouncing, risk rules, ZeroMQ bridge, and DuckDB writer
- `cpp/`: C++17 event simulation, process-shared lock-free SPSC ring, ZeroMQ benchmarks, and native tests
- `artifacts/`: reports from the shared-memory queue capacity sweep and the storage checks
- `tests/`: Python unit and integration tests
- `scripts/`: benchmarks, report generation, and report validation
- `artifacts/`: synthetic experiment results in CSV/JSON format
- `docs/assets/`: system, execution, data-quality, and benchmark SVGs

## Author and license

Author: **Pirate-Emperor**.

The project uses the MIT License. See [LICENSE](LICENSE).
