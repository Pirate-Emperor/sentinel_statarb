#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
TICKS="${SENTINEL_TEST_TICKS:-100000}"
CPP_TICKS="${SENTINEL_CPP_TICKS:-100000}"
STORAGE_TICKS="${SENTINEL_STORAGE_TICKS:-100000}"

python -m compileall -q sentinel_runtime scripts tests
python -m unittest discover -s tests -v
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python scripts/run_experiments.py --ticks "$TICKS" --repeats 3 --out artifacts
bash scripts/run_cpp_benchmark.sh "$CPP_TICKS" "$ROOT/artifacts/cpp_benchmark.json"
python scripts/benchmark_zmq_ipc.py --ticks 3000 --warmup 500 --out artifacts/zmq_ipc_benchmark.json

if [ -x "$ROOT/build/cpp/sentinel_shm_spsc_ipc_benchmark" ]; then
  "$ROOT/build/cpp/sentinel_shm_spsc_ipc_benchmark" --messages 200000 --warmup 20000 --out artifacts/shm_spsc_ipc_benchmark.json
fi
if [ -x "$ROOT/build/cpp/sentinel_zmq_ipc_oneway_benchmark" ]; then
  "$ROOT/build/cpp/sentinel_zmq_ipc_oneway_benchmark" --messages 5000 --warmup 500 --out artifacts/cpp_zmq_ipc_oneway_benchmark.json
else
  echo "Native C++ ZeroMQ benchmark skipped; install libzmq development headers and pkg-config."
fi
if [ -x "$ROOT/build/cpp/sentinel_zmq_ipc_benchmark" ]; then
  "$ROOT/build/cpp/sentinel_zmq_ipc_benchmark" --messages 5000 --warmup 500 --out artifacts/cpp_zmq_ipc_benchmark.json
fi

if python -c "import duckdb, pandas" >/dev/null 2>&1; then
  python scripts/benchmark_storage.py --ticks "$STORAGE_TICKS" --batch-size 10000 --out "$ROOT/artifacts/stress_ticks.duckdb"
else
  echo "DuckDB storage smoke test skipped; install the storage extra to enable it."
fi

python scripts/run_storage_batch_sweep.py --ticks 100000 --out-dir artifacts
python scripts/make_artifacts.py
python scripts/validate_reports.py
test ! -e "$ROOT/main.png"
echo "All enabled local checks completed. Timing results depend on the machine."
