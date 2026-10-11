# Sentinel StatArb

**A small market-event test system using C++17, Python, ZeroMQ, and DuckDB.**

Sentinel StatArb tests how fast quote streams behave when they contain repeated messages, old timestamps, stale quotes, and a sudden price gap. It combines a native C++ queue simulation with Python checks for signal control, protective stop-limit orders, message transport, and batch storage.

All examples use synthetic data. The project does not connect to a broker or place live orders.

## At a glance

- **Native C++ engine:** SPSC ring buffer and an event-processing benchmark. The benchmark reports whether its atomics are lock-free on the current machine.
- **Quote checks:** Reject repeated sequence numbers, out-of-order timestamps, stale quotes, and timestamps too far in the future.
- **Dynamic debouncer:** Holds back repeated strategy signals for longer after a sharp price move. Protective order checks still run for every quote that passes the quality checks.
- **OCO stop-limit model:** Tests stop/target behavior and a 5 bps stop-limit offset. A triggered stop-limit order can remain unfilled after a large gap.
- **ZeroMQ bridge:** Sends validated tick messages over an IPC or TCP socket. The benchmark is a process-to-process round trip, not a one-way measurement.
- **DuckDB writer:** Uses a bounded queue and a separate writer thread. Vectorized batch inserts reduce per-row database overhead; read-back checks verify every sequence.
- **Repeatable experiments:** Save CSV/JSON measurements and SVG diagrams for the quote policies, crash scenario, and timing results.

## System view

![Sentinel StatArb architecture](docs/assets/architecture.svg)

![Quote validation and risk flow](docs/assets/execution-flow.svg)

## Quick start

Requirements: Python 3.10+, a C++17 compiler, and CMake 3.16+.

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

The combined script runs smaller storage checks by default. Set `SENTINEL_STORAGE_TICKS=10000000` to run the full storage size locally.

## Repeatable experiments

The experiment script runs one warm-up for each policy, then measures repeated runs and reports the median timing. The timing excludes that policy's warm-up run.

```bash
# Python quote and risk experiment
python scripts/run_experiments.py --ticks 100000 --repeats 3
python scripts/run_experiments.py --ticks 1000000 --repeats 3

# Native C++ benchmark: warm-up run, then measured run
bash scripts/run_cpp_benchmark.sh 1000000 artifacts/cpp_benchmark.json
bash scripts/run_cpp_benchmark.sh 10000000 artifacts/cpp_benchmark_10m.json

# ZeroMQ IPC round-trip benchmark
python scripts/benchmark_zmq_ipc.py --ticks 20000 --warmup 2000 --out artifacts/zmq_ipc_benchmark.json

# Separate warm-up and measured DuckDB writes, then verify every row and sequence
python scripts/benchmark_storage.py --ticks 10000000 --batch-size 10000 --out artifacts/stress_ticks.duckdb

# Refresh the diagrams from the saved JSON reports
python scripts/make_artifacts.py
python scripts/validate_reports.py
```

The DuckDB command writes a separate warm-up database and measured database. It reads the measured database back and checks the row count, distinct sequence count, and sequence range. Database files are local test outputs and are not meant to be committed.

GitHub Actions runs Python tests, C++ tests, the 100K quote experiment, 1M and 10M C++ benchmarks, ZeroMQ IPC tests, and the 10M-row DuckDB check. A run is successful only when the steps complete and their checks pass. See [the workflow](.github/workflows/ci.yml).

## Analysis and experiment images

![Experiment pipeline](docs/assets/experiment-pipeline.svg)

![Quote data-quality counts](docs/assets/data-quality.svg)

![Signal policy performance comparison](docs/assets/performance-comparison.svg)

![Synthetic flash-crash scenario](docs/assets/flash-crash-analysis.svg)

![Stop-limit gap sweep](docs/assets/oco-gap-sweep.svg)

![Native C++ benchmark](docs/assets/cpp-benchmark.svg)

![ZeroMQ IPC round-trip benchmark](docs/assets/zmq-ipc-latency.svg)

See the [experiment notes](docs/EXPERIMENTS.md) and [reports and diagrams index](docs/README.md) for the saved results and how to reproduce them.

## Reading the numbers correctly

The checked-in JSON/CSV files and diagrams are reference runs from synthetic data. Throughput and latency change with the CPU, operating system, compiler, process scheduling, and test settings. Re-run the commands above to produce results for your machine.

The saved 10M C++ report records about **34.55 million events/second** and **0.043 μs sampled p99 processing latency** for that run. That is sampled native event-processing time, not end-to-end market latency.

The saved ZeroMQ report records about **96.9 μs p50** and **700.4 μs p99** round-trip latency. This does **not** show sub-10 μs IPC, and ZeroMQ is not claimed to be lock-free. The in-process C++ SPSC ring and the ZeroMQ process-to-process path are separate measurements.

A 5 bps stop-limit offset sets a price boundary; it does not promise a fill. The gap sweep deliberately includes price moves larger than the offset so this limitation is visible in the tests.

## Main files

- `sentinel_runtime/`: Python quote validation, debouncing, risk rules, ZeroMQ bridge, and DuckDB writer
- `cpp/`: C++17 event simulation, SPSC ring, and native tests
- `tests/`: Python unit and integration tests
- `scripts/`: benchmarks, report generation, and report validation
- `artifacts/`: synthetic experiment results in CSV/JSON format
- `docs/assets/`: system, execution, data-quality, and benchmark SVGs

## Author and license

Author: **Pirate-Emperor**.

The project uses the MIT License. See [LICENSE](LICENSE).
