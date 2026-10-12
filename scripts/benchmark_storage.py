#!/usr/bin/env python3
"""Stress the async DuckDB writer with warm-up and measured runs."""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sentinel_runtime.duckdb_logger import AsyncDuckDBTickLogger
from sentinel_runtime.engine import Tick


def make_batch(start: int, stop: int, seed: int) -> list[Tick]:
    rng = random.Random(seed + start)
    price = 100.0 + (start % 100000) * 0.00001
    rows = []
    for sequence in range(start, stop):
        price *= 1.0 + rng.uniform(-0.000001, 0.000001)
        rows.append(Tick("STRESS-USD", sequence, 1700000000000000000 + sequence * 10000,
                         price - 0.005, price + 0.005))
    return rows


async def write_run(path: Path, count: int, batch_size: int, phase: str) -> dict:
    for stale in (path, Path(str(path) + ".wal")):
        if stale.exists():
            stale.unlink()

    logger = AsyncDuckDBTickLogger(path, batch_size=batch_size, queue_size=64)
    await logger.start()
    start_ns = time.perf_counter_ns()
    progress_step = max(batch_size, count // 10)
    next_progress = progress_step
    try:
        for offset in range(0, count, batch_size):
            stop = min(count, offset + batch_size)
            await logger.log_many(make_batch(offset, stop, 20261011))
            if stop >= next_progress or stop == count:
                print(f"[{phase}] queued {stop:,}/{count:,} ticks", flush=True)
                next_progress = stop + progress_step
        await logger.close()
    except BaseException:
        try:
            await logger.close()
        except BaseException:
            pass
        raise

    elapsed_ns = time.perf_counter_ns() - start_ns
    print(f"[{phase}] writer closed; checking the database", flush=True)
    import duckdb

    connection = duckdb.connect(str(path), read_only=True)
    try:
        rows = int(connection.execute("SELECT COUNT(*) FROM ticks").fetchone()[0])
        distinct_sequences = int(connection.execute(
            "SELECT COUNT(DISTINCT sequence) FROM ticks").fetchone()[0])
        bad_quotes = int(connection.execute(
            "SELECT COUNT(*) FROM ticks "
            "WHERE bid IS NULL OR ask IS NULL OR bid<=0 OR ask<=0 OR bid>ask"
        ).fetchone()[0])
        first, last = connection.execute(
            "SELECT MIN(sequence),MAX(sequence) FROM ticks").fetchone()
    finally:
        connection.close()

    if (rows != count or logger.rows_written != count or distinct_sequences != count
            or first != 0 or last != count - 1 or bad_quotes != 0):
        raise RuntimeError(
            f"storage check failed: expected {count} unique rows 0..{count - 1} "
            f"with valid bid/ask; logger={logger.rows_written}, read_back={rows}, "
            f"unique={distinct_sequences}, bad_quotes={bad_quotes}, range={first}..{last}"
        )

    print(f"[{phase}] PASS: {rows:,} unique rows; sequence range {first}..{last}; "
          "no invalid quotes", flush=True)
    return {
        "rows_requested": count,
        "rows_written_by_logger": logger.rows_written,
        "rows_read_back": rows,
        "distinct_sequences": distinct_sequences,
        "bad_quotes": bad_quotes,
        "first_sequence": first,
        "last_sequence": last,
        "elapsed_ms": elapsed_ns / 1e6,
        "rows_per_second": count / (elapsed_ns / 1e9),
        "batch_size": batch_size,
        "database_bytes": path.stat().st_size,
    }


async def run(count: int, batch_size: int, output: Path) -> dict:
    output.parent.mkdir(parents=True, exist_ok=True)
    warmup_path = output.with_name(output.stem + ".warmup.duckdb")
    print(f"Starting full warm-up run: {count:,} ticks", flush=True)
    try:
        await write_run(warmup_path, count, batch_size, "warm-up")
    finally:
        for stale in (warmup_path, Path(str(warmup_path) + ".wal")):
            if stale.exists():
                stale.unlink()

    print(f"Starting separate measured run: {count:,} ticks", flush=True)
    measured = await write_run(output, count, batch_size, "measured")
    report = {
        "benchmark": "async_duckdb_tick_logging",
        "warmup_runs": 1,
        "measured_runs": 1,
        "warmup_row_count": count,
        **measured,
    }
    report_path = output.with_name("storage_benchmark.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Verified storage report written to {report_path}", flush=True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticks", type=int, default=10_100_000)
    parser.add_argument("--batch-size", type=int, default=10_000)
    parser.add_argument("--out", type=Path, default=ROOT / "artifacts" / "stress_ticks.duckdb")
    args = parser.parse_args()
    if args.ticks < 1 or args.batch_size < 1:
        parser.error("--ticks and --batch-size must be positive")
    try:
        import duckdb  # noqa: F401
        import pandas  # noqa: F401
    except ImportError as exc:
        print("DuckDB storage dependencies are missing. Run: python -m pip install -e '.[storage]'",
              file=sys.stderr)
        print(exc, file=sys.stderr)
        return 2
    print(json.dumps(asyncio.run(run(args.ticks, args.batch_size, args.out)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
