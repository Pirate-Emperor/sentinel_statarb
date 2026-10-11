#!/usr/bin/env bash
set -eo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
TICKS=100000
CPP_TICKS=100000
if [ -n "$SENTINEL_TEST_TICKS" ]; then TICKS="$SENTINEL_TEST_TICKS"; fi
if [ -n "$SENTINEL_CPP_TICKS" ]; then CPP_TICKS="$SENTINEL_CPP_TICKS"; fi
python -m unittest discover -s tests -v
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
ctest --test-dir build --output-on-failure
python scripts/run_experiments.py --ticks "$TICKS" --repeats 3 --out artifacts
bash scripts/run_cpp_benchmark.sh "$CPP_TICKS" "$ROOT/artifacts/cpp_benchmark.json"
python scripts/benchmark_zmq_ipc.py --ticks 3000 --warmup 500 --out artifacts/zmq_ipc_benchmark.json
python scripts/make_artifacts.py
test ! -e "$ROOT/main.png"
echo "All enabled local checks completed. DuckDB stress requires the storage extra."
