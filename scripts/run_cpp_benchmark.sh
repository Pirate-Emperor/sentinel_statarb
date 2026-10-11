#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TICKS=1000000
OUT="$ROOT/artifacts/cpp_benchmark.json"
if [ "$#" -ge 1 ]; then TICKS="$1"; fi
if [ "$#" -ge 2 ]; then OUT="$2"; fi
mkdir -p "$(dirname "$OUT")"
cmake -S "$ROOT" -B "$ROOT/build" -DCMAKE_BUILD_TYPE=Release
cmake --build "$ROOT/build" --parallel
"$ROOT/build/cpp/sentinel_engine" --ticks "$TICKS" >/dev/null
"$ROOT/build/cpp/sentinel_engine" --ticks "$TICKS" > "$OUT"
python - "$OUT" <<'PY'
import json,pathlib,sys
path=pathlib.Path(sys.argv[1]);report={}
for line in path.read_text().splitlines():
    if "=" in line:
        key,value=line.split("=",1);report[key]=value
path.write_text(json.dumps(report,indent=2)+"\n")
print(f"Saved measured C++ run to {path}")
PY
