#!/usr/bin/env python3
"""Compare shared-memory SPSC queue capacities with per-run warm-up and validation."""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPACITIES = (16, 64, 256, 1024)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--messages", type=int, default=200_000)
    parser.add_argument("--warmup", type=int, default=20_000)
    parser.add_argument("--binary", type=Path, default=ROOT / "build" / "cpp" / "sentinel_shm_spsc_ipc_benchmark")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "artifacts")
    args = parser.parse_args()
    if args.messages < 1 or args.warmup < 0:
        parser.error("--messages must be positive and --warmup must be non-negative")
    if not args.binary.is_file():
        print(f"Shared-memory benchmark not found: {args.binary}", file=sys.stderr)
        print("Build it with: cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel",
              file=sys.stderr)
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for capacity in CAPACITIES:
        report_path = args.out_dir / f"shm_spsc_capacity_{capacity}.json"
        command = [
            str(args.binary), "--messages", str(args.messages), "--warmup", str(args.warmup),
            "--capacity", str(capacity), "--out", str(report_path),
        ]
        print(f"\n=== Shared-memory capacity experiment: {capacity} slots ===", flush=True)
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        if completed.stdout:
            print(completed.stdout.rstrip(), flush=True)
        if completed.returncode != 0:
            if completed.stderr:
                print(completed.stderr.rstrip(), file=sys.stderr, flush=True)
            print(f"capacity {capacity} failed with exit code {completed.returncode}", file=sys.stderr)
            return completed.returncode or 1
        report = json.loads(report_path.read_text(encoding="utf-8"))
        if (int(report["queue_capacity"]) != capacity
                or int(report["timed_sample_count"]) != args.messages
                or report.get("payload_check") != "passed"
                or not bool(report.get("shared_memory_is_lock_free"))
                or int(report.get("bad_sequences", -1)) != 0
                or int(report.get("invalid_timestamps", -1)) != 0):
            raise RuntimeError(f"capacity {capacity} did not pass the sequence, timestamp, and atomic checks")
        results.append(report)
        print(f"PASS: p50={float(report['p50_one_way_us']):.3f} us, "
              f"p99={float(report['p99_one_way_us']):.3f} us, "
              f"{float(report['throughput_messages_per_second']):,.0f} messages/s", flush=True)

    summary = {
        "benchmark": "process_shared_spsc_capacity_sweep",
        "warmup_messages_per_capacity": args.warmup,
        "measured_messages_per_capacity": args.messages,
        "capacities": list(CAPACITIES),
        "results": results,
        "best_p50_capacity": min(results, key=lambda row: float(row["p50_one_way_us"]))["queue_capacity"],
        "note": "Same-host process-shared memory. Every capacity gets a fresh process, warm-up, and validated measured run.",
    }
    json_path = args.out_dir / "shm_spsc_capacity_sweep.json"
    csv_path = args.out_dir / "shm_spsc_capacity_sweep.csv"
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    columns = [
        "queue_capacity", "warmup_messages", "measured_messages", "shared_memory_is_lock_free",
        "p50_one_way_us", "p95_one_way_us", "p99_one_way_us", "max_one_way_us",
        "throughput_messages_per_second", "timed_sample_count", "bad_sequences", "invalid_timestamps",
        "sub_10_us_p50",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for report in results:
            writer.writerow({
                "queue_capacity": report["queue_capacity"],
                "warmup_messages": report["warmup_messages"],
                "measured_messages": report["measured_messages"],
                "shared_memory_is_lock_free": report["shared_memory_is_lock_free"],
                **{column: report.get(column, "") for column in columns if column not in {
                    "queue_capacity", "warmup_messages", "measured_messages", "shared_memory_is_lock_free"
                }},
            })
    print(f"Saved capacity sweep: {json_path} and {csv_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
