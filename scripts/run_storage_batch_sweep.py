#!/usr/bin/env python3
"""Compare DuckDB batch sizes using a warm-up plus a checked measured run per size."""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from benchmark_storage import write_run


BATCH_SIZES = (1_000, 10_000, 50_000)


async def run_sweep(count: int, output_dir: Path) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for batch_size in BATCH_SIZES:
        measured_path = output_dir / f"storage_sweep_{batch_size}.duckdb"
        warmup_path = output_dir / f"storage_sweep_{batch_size}.warmup.duckdb"
        print(f"\n=== Batch-size experiment: {batch_size:,} rows per batch ===", flush=True)
        try:
            await write_run(warmup_path, count, batch_size, f"warm-up b{batch_size}")
        finally:
            for path in (warmup_path, Path(str(warmup_path) + ".wal")):
                if path.exists():
                    path.unlink()
        measured = await write_run(measured_path, count, batch_size, f"measured b{batch_size}")
        results.append({
            "batch_size": batch_size,
            "warmup_runs": 1,
            "warmup_row_count": count,
            "measured_runs": 1,
            **measured,
        })
        for path in (measured_path, Path(str(measured_path) + ".wal")):
            if path.exists():
                path.unlink()
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticks", type=int, default=100_000)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()
    if args.ticks < 1:
        parser.error("--ticks must be positive")
    try:
        import duckdb  # noqa: F401
        import pandas  # noqa: F401
    except ImportError as exc:
        print("Install storage dependencies with: python -m pip install -e '.[storage]'", file=sys.stderr)
        print(exc, file=sys.stderr)
        return 2

    rows = asyncio.run(run_sweep(args.ticks, args.out_dir))
    json_path = args.out_dir / "storage_batch_sweep.json"
    csv_path = args.out_dir / "storage_batch_sweep.csv"
    json_path.write_text(json.dumps({
        "benchmark": "duckdb_batch_size_sweep",
        "ticks_per_run": args.ticks,
        "batch_sizes": list(BATCH_SIZES),
        "warmup_runs_per_batch": 1,
        "measured_runs_per_batch": 1,
        "results": rows,
        "note": "Synthetic ticks. Timing includes tick generation and asynchronous logging; machine-dependent.",
    }, indent=2) + "\n", encoding="utf-8")
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved batch-size comparison to {json_path} and {csv_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
