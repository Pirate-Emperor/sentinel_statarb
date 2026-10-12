# Experiment notes

These numbers are saved reference results from synthetic data. They help compare code changes, but they are not live-market measurements. CPU, operating system, compiler, system load, and the selected tick count affect the results. Run the commands below again to measure a new machine.

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

The following checks matter:

- A repeated sequence, older timestamp, stale quote, or excessive future timestamp is rejected before it can create a strategy signal.
- A valid quote can trigger a protective order even when the debouncer holds back a signal.
- An OCO order is one-shot: after the stop or take-profit fires, later quotes cannot trigger the other side.
- A 5 bps offset is a limit-price rule, not a promise that a buyer or seller will be available at that price.

![Quote data-quality counts](assets/data-quality.svg)

![Signal policy performance comparison](assets/performance-comparison.svg)

![Stop-limit price gap sweep](assets/oco-gap-sweep.svg)

![Synthetic crash scenario](assets/flash-crash-analysis.svg)

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

![Native C++ benchmark](assets/cpp-benchmark.svg)

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

![ZeroMQ IPC round-trip benchmark](assets/zmq-ipc-latency.svg)

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

![Native C++ one-way IPC latency](assets/zmq-ipc-oneway-latency.svg)

The existing Python benchmark remains useful for a process-to-process request/reply path, but Python and scheduling add overhead. Its round-trip values must not be compared directly with one-way C++ latency.

## DuckDB batch-size comparison

The quick CI job also runs 100,000 synthetic ticks with batch sizes of 1,000, 10,000, and 50,000 rows. Each batch-size setting gets its own warm-up database and separate measured database. The measured database is checked for the requested row count, unique sequence range, and valid bid/ask values before its throughput is compared. The sweep saves `storage_batch_sweep.json` and `storage_batch_sweep.csv`, then creates the chart below.

```bash
python scripts/run_storage_batch_sweep.py --ticks 100000 --out-dir artifacts
python scripts/make_artifacts.py
python scripts/validate_reports.py
```

![DuckDB batch-size comparison](assets/storage-batch-sweep.svg)

## DuckDB storage stress test

Run the test with the storage extra installed:

```bash
python -m pip install -e ".[storage]"
python scripts/benchmark_storage.py --ticks 10100000 --batch-size 10000 --out artifacts/stress_ticks.duckdb
```

The CI storage job writes and verifies 10.1 million rows. It has a 120-minute limit, separate from the 30-minute unit-test job. The script prints queued progress for both passes, performs a full warm-up write and a separate measured write. It then opens the measured database and verifies that the logger's written-row counter and the database's row count both equal the requested count, all sequence numbers are unique, and the sequence range is exactly `0` through `count - 1`. It saves timing and row checks in `artifacts/storage_benchmark.json`. The local database is ignored by Git.

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
