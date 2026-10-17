#!/usr/bin/env python3
"""Check saved experiment values, benchmark reports, and SVG files for consistency."""
from __future__ import annotations

import csv
import json
import math
import os
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
ASSETS = ROOT / "docs" / "assets"


def fail(message: str) -> None:
    raise SystemExit(f"REPORT CHECK FAILED: {message}")


def number(value: object, label: str) -> float:
    try:
        result = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        fail(f"{label} is not numeric: {value!r}")
        raise AssertionError from exc
    if not math.isfinite(result):
        fail(f"{label} is not finite")
    return result


def load_json(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing report: {path.relative_to(ROOT)}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        fail(f"invalid JSON in {path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"expected an object in {path.relative_to(ROOT)}")
    return value


def check_experiment() -> None:
    summary = load_json(ARTIFACTS / "experiment_summary.json")
    base_count = int(summary["base_tick_count"])
    input_count = int(summary["input_event_count_with_duplicates"])
    expected_events = base_count + max(0, (base_count - 1) // 97)
    if base_count < 1 or input_count != expected_events:
        fail("base tick count and duplicate-injection count do not match")
    rows = summary.get("policies", [])
    names = {row.get("policy") for row in rows}
    if names != {"no debounce", "fixed debounce", "dynamic debounce"}:
        fail("expected the three documented signal policies")
    for row in rows:
        label = str(row["policy"])
        if int(row["input_events"]) != input_count:
            fail(f"{label}: input count differs from summary")
        counts = [
            int(row["accepted_signals"]), int(row["debounced_signals"]),
            int(row["duplicate_sequences"]), int(row["out_of_order_timestamps"]),
            int(row["stale_quotes"]), int(row["future_quotes"]),
        ]
        if sum(counts) != input_count:
            fail(f"{label}: accepted, held, and rejected event counts do not add up")
        accepted, held = counts[:2]
        expected_reduction = 100.0 * held / (accepted + held) if accepted + held else 0.0
        if abs(number(row["signal_reduction_pct"], label) - expected_reduction) > 1e-6:
            fail(f"{label}: signal reduction percentage is inconsistent")
        timings = [number(row[key], f"{label}.{key}") for key in
                   ("events_per_second", "sampled_latency_p50_us",
                    "sampled_latency_p95_us", "sampled_latency_p99_us")]
        if timings[0] <= 0 or not (0 <= timings[1] <= timings[2] <= timings[3]):
            fail(f"{label}: throughput or latency quantiles are invalid")
        if int(row["stop_triggers"]) != 1 or bool(row["stop_limit_marketable_at_crash"]):
            fail(f"{label}: injected crash stop-limit result is unexpected")
        post_ticks = int(row["post_crash_window_ticks"])
        post_valid = int(row["post_crash_window_valid_quotes"])
        post_accepted = int(row["post_crash_window_accepted_signals"])
        post_debounced = int(row["post_crash_window_debounced_signals"])
        if post_ticks != int(summary["post_crash_signal_window_ticks"]):
            fail(f"{label}: post-crash observation window differs from summary")
        if post_valid != post_accepted + post_debounced or post_valid > post_ticks:
            fail(f"{label}: post-crash window quote/signal counts do not add up")
    post_rows = {str(row["policy"]): row for row in rows}
    no_debounce_entries = int(post_rows["no debounce"]["post_crash_window_accepted_signals"])
    fixed_entries = int(post_rows["fixed debounce"]["post_crash_window_accepted_signals"])
    dynamic_entries = int(post_rows["dynamic debounce"]["post_crash_window_accepted_signals"])
    if int(summary["post_crash_signal_window_ticks"]) > 0 and not (
            no_debounce_entries > fixed_entries > dynamic_entries):
        fail("post-crash entry-signal window does not demonstrate dynamic debounce suppression")
    with (ARTIFACTS / "experiment_metrics.csv").open(newline="", encoding="utf-8") as f:
        csv_rows = list(csv.DictReader(f))
    if [row.get("policy") for row in csv_rows] != [row.get("policy") for row in rows]:
        fail("experiment_metrics.csv policy rows differ from experiment_summary.json")
    for row, json_row in zip(csv_rows, rows):
        if int(row["input_events"]) != int(json_row["input_events"]):
            fail(f"CSV input count differs for {row['policy']}")
    gap_rows = summary.get("oco_gap_sweep", [])
    if len(gap_rows) != 24:
        fail("expected 24 stop-limit gap-sweep combinations")
    offsets = sorted({float(row["offset_bps"]) for row in gap_rows})
    gaps = sorted({float(row["gap_bps"]) for row in gap_rows})
    if len(offsets) != 3 or len(gaps) != 8:
        fail("stop-limit gap sweep does not cover all configured offsets and gaps")
    for offset in offsets:
        one_offset = sorted((row for row in gap_rows if float(row["offset_bps"]) == offset),
                            key=lambda row: float(row["gap_bps"]))
        seen_unmarketable = False
        for row in one_offset:
            expected = float(row["observed_price"]) >= float(row["limit_price"]) - 1e-10
            if bool(row["marketable"]) != expected:
                fail(f"gap sweep marketability is wrong at offset={offset}, gap={row['gap_bps']}")
            if not expected:
                seen_unmarketable = True
            elif seen_unmarketable:
                fail(f"marketability becomes true again for offset={offset}")
    print("PASS experiment JSON/CSV counts and stop-limit grid")


def check_cpp() -> None:
    reports = [ARTIFACTS / "cpp_benchmark.json", ARTIFACTS / "cpp_benchmark_10m.json"]
    present = [path for path in reports if path.exists()]
    if not present:
        fail("no C++ benchmark JSON report found")
    for path in present:
        row = load_json(path)
        ticks = int(row["ticks"])
        warmup = int(row["warmup_ticks"])
        measured = int(row["measured_ticks"])
        if ticks < 1 or warmup < 0 or measured != ticks - warmup:
            fail(f"{path.name}: measured/warm-up tick counts are inconsistent")
        if number(row["measured_throughput_events_per_second"], "C++ throughput") <= 0:
            fail(f"{path.name}: throughput must be positive")
        pcts = [number(row[f"sampled_processing_{q}_us"], q) for q in ("p50", "p95", "p99")]
        if not (0 <= pcts[0] <= pcts[1] <= pcts[2]):
            fail(f"{path.name}: latency quantiles are not ordered")
        if int(row["latency_sample_count"]) < 1 or int(row["invalid_ticks"]) != 0:
            fail(f"{path.name}: missing timing samples or invalid synthetic ticks")
    print(f"PASS C++ benchmark report(s): {len(present)}")


def check_zmq() -> None:
    row = load_json(ARTIFACTS / "zmq_ipc_benchmark.json")
    measured = int(row["measured_messages"])
    if measured < 1 or int(row["timed_sample_count"]) != measured:
        fail("ZeroMQ sample count differs from measured message count")
    if row.get("payload_check") != "passed":
        fail("ZeroMQ payload integrity check did not pass")
    values = [number(row[key], key) for key in
              ("p50_round_trip_us", "p95_round_trip_us", "p99_round_trip_us", "max_round_trip_us")]
    if not (0 <= values[0] <= values[1] <= values[2] <= values[3]):
        fail("ZeroMQ round-trip quantiles are invalid")
    if number(row["throughput_round_trips_per_second"], "ZeroMQ throughput") <= 0:
        fail("ZeroMQ throughput must be positive")
    print("PASS ZeroMQ report counts, payload status, and quantiles")


def check_native_zmq_if_present() -> None:
    specs = (
        ("cpp_zmq_ipc_oneway_benchmark.json", "p50_one_way_us", "p95_one_way_us", "p99_one_way_us", "max_one_way_us"),
        ("cpp_zmq_ipc_benchmark.json", "p50_round_trip_us", "p95_round_trip_us", "p99_round_trip_us", "max_round_trip_us"),
    )
    for filename, p50, p95, p99, maximum in specs:
        path = ARTIFACTS / filename
        if not path.exists():
            print(f"SKIP {filename} (native libzmq benchmark has not been run)")
            continue
        row = load_json(path)
        measured = int(row["measured_messages"])
        if measured < 1 or int(row["timed_sample_count"]) != measured:
            fail(f"{filename}: timed sample count differs from measured messages")
        if row.get("payload_check") != "passed" or int(row.get("bad_payloads", 0)) != 0:
            fail(f"{filename}: IPC payload validation failed")
        if bool(row.get("transport_is_lock_free", False)):
            fail(f"{filename}: do not label ZeroMQ transport as lock-free")
        values = [number(row[key], key) for key in (p50, p95, p99, maximum)]
        if not (0 <= values[0] <= values[1] <= values[2] <= values[3]):
            fail(f"{filename}: latency quantiles are not ordered")
        throughput_key = "serial_round_trips_per_second" if "oneway" in filename else "throughput_round_trips_per_second"
        if number(row[throughput_key], throughput_key) <= 0:
            fail(f"{filename}: throughput must be positive")
        if "oneway" in filename and "sub_10_us_p50" in row:
            if bool(row["sub_10_us_p50"]) != (values[0] < 10.0):
                fail(f"{filename}: sub-10 us target flag does not match the measured p50")
        unit = "one-way" if "oneway" in filename else "round-trip"
        target = "MET" if "oneway" in filename and values[0] < 10.0 else "NOT MET" if "oneway" in filename else "measured"
        print(f"PASS {filename}: {unit} p50={values[0]:.3f} us; sub-10 us p50 target {target}")


def check_shared_memory_if_present() -> None:
    path = ARTIFACTS / "shm_spsc_ipc_benchmark.json"
    if not path.exists():
        print("SKIP shared-memory SPSC benchmark (report not generated)")
        return
    row = load_json(path)
    messages = int(row["measured_messages"])
    capacity = int(row["queue_capacity"])
    if capacity < 2 or capacity > 4096 or capacity & (capacity - 1):
        fail("shared-memory queue capacity must be a power of two from 2 through 4096")
    if messages < 1 or int(row["timed_sample_count"]) != messages:
        fail("shared-memory IPC sample count differs from measured messages")
    if row.get("payload_check") != "passed":
        fail("shared-memory IPC payload check did not pass")
    if not bool(row.get("shared_memory_is_lock_free", False)):
        fail("shared-memory SPSC benchmark reports non-lock-free atomics")
    if int(row.get("bad_sequences", -1)) != 0 or int(row.get("invalid_timestamps", -1)) != 0:
        fail("shared-memory SPSC benchmark found sequence or timestamp errors")
    pcts = [number(row[key], key) for key in
            ("p50_one_way_us", "p95_one_way_us", "p99_one_way_us", "max_one_way_us")]
    if not (0 <= pcts[0] <= pcts[1] <= pcts[2] <= pcts[3]):
        fail("shared-memory one-way latency quantiles are invalid")
    if number(row["throughput_messages_per_second"], "shared-memory throughput") <= 0:
        fail("shared-memory throughput must be positive")
    if bool(row.get("sub_10_us_p50", False)) != (pcts[0] < 10.0):
        fail("shared-memory sub-10 us flag does not match measured p50")
    target = "MET" if pcts[0] < 10.0 else "NOT MET"
    print(f"PASS shared-memory SPSC: p50={pcts[0]:.3f} us; sub-10 us p50 target {target}")


def check_shared_memory_sweep_if_present() -> None:
    path = ARTIFACTS / "shm_spsc_capacity_sweep.json"
    csv_path = ARTIFACTS / "shm_spsc_capacity_sweep.csv"
    if not path.exists():
        print("SKIP shared-memory capacity sweep (report not generated)")
        return
    row = load_json(path)
    expected = {16, 64, 256, 1024}
    results = row.get("results", [])
    capacities = {int(item["queue_capacity"]) for item in results}
    if capacities != expected or len(results) != len(expected):
        fail("shared-memory sweep must contain capacity settings 16, 64, 256, and 1024")
    messages = int(row["measured_messages_per_capacity"])
    warmup = int(row["warmup_messages_per_capacity"])
    p50_by_capacity = {}
    for item in results:
        capacity = int(item["queue_capacity"])
        if int(item["measured_messages"]) != messages or int(item["warmup_messages"]) != warmup:
            fail(f"shared-memory capacity {capacity}: message counts differ from sweep settings")
        if item.get("payload_check") != "passed" or not bool(item.get("shared_memory_is_lock_free", False)):
            fail(f"shared-memory capacity {capacity}: payload or lock-free check failed")
        if int(item.get("bad_sequences", -1)) != 0 or int(item.get("invalid_timestamps", -1)) != 0:
            fail(f"shared-memory capacity {capacity}: sequence or timestamp errors")
        pcts = [number(item[key], key) for key in
                ("p50_one_way_us", "p95_one_way_us", "p99_one_way_us", "max_one_way_us")]
        if not (0 <= pcts[0] <= pcts[1] <= pcts[2] <= pcts[3]):
            fail(f"shared-memory capacity {capacity}: invalid latency quantiles")
        if number(item["throughput_messages_per_second"], "shared-memory throughput") <= 0:
            fail(f"shared-memory capacity {capacity}: throughput must be positive")
        if bool(item.get("sub_10_us_p50", False)) != (pcts[0] < 10.0):
            fail(f"shared-memory capacity {capacity}: sub-10 us flag does not match p50")
        p50_by_capacity[capacity] = pcts[0]
    best = min(p50_by_capacity, key=p50_by_capacity.get)
    if int(row["best_p50_capacity"]) != best:
        fail("shared-memory sweep best_p50_capacity does not match the measured results")
    if not csv_path.is_file():
        fail("shared-memory capacity sweep CSV is missing")
    with csv_path.open(newline="", encoding="utf-8") as stream:
        csv_rows = list(csv.DictReader(stream))
    if {int(item["queue_capacity"]) for item in csv_rows} != expected or len(csv_rows) != len(expected):
        fail("shared-memory capacity sweep CSV rows do not match JSON")
    print(f"PASS shared-memory sweep: {len(results)} lock-free capacities; best p50 at capacity {best}")


def check_storage_if_present() -> None:
    path = ARTIFACTS / "storage_benchmark.json"
    if not path.exists():
        print("SKIP DuckDB report invariants (run benchmark_storage.py to create a report)")
        return
    row = load_json(path)
    count = int(row["rows_requested"])
    minimum_rows = int(os.environ.get("SENTINEL_MIN_STORAGE_ROWS", "1"))
    if count < minimum_rows:
        fail(f"DuckDB report has {count:,} rows; this run requires at least {minimum_rows:,}")
    if count < 1 or any(int(row[key]) != count for key in
                        ("rows_written_by_logger", "rows_read_back", "distinct_sequences")):
        fail("DuckDB requested, written, read-back, and unique row counts differ")
    if int(row["first_sequence"]) != 0 or int(row["last_sequence"]) != count - 1:
        fail("DuckDB sequence range is incomplete")
    if int(row["warmup_row_count"]) != count or int(row["warmup_runs"]) != 1:
        fail("DuckDB warm-up metadata is inconsistent")
    if number(row["rows_per_second"], "DuckDB throughput") <= 0 or int(row["database_bytes"]) < 1:
        fail("DuckDB throughput or database size is invalid")
    if int(row.get("bad_quotes", 0)) != 0:
        fail("DuckDB stored rows contain invalid bid/ask quotes")
    print(f"PASS DuckDB report: {count:,} unique rows verified")


def check_storage_sweep_if_present() -> None:
    path = ARTIFACTS / "storage_batch_sweep.json"
    csv_path = ARTIFACTS / "storage_batch_sweep.csv"
    if not path.exists():
        print("SKIP DuckDB batch-size sweep (run run_storage_batch_sweep.py to create a report)")
        return
    row = load_json(path)
    count = int(row["ticks_per_run"])
    results = row.get("results", [])
    sizes = {int(item["batch_size"]) for item in results}
    if sizes != {1000, 10000, 50000} or len(results) != 3:
        fail("DuckDB batch sweep must contain 1K, 10K, and 50K row batches")
    for item in results:
        size = int(item["batch_size"])
        if int(item["warmup_runs"]) != 1 or int(item["measured_runs"]) != 1:
            fail(f"batch {size}: expected one warm-up and one measured run")
        if int(item["warmup_row_count"]) != count:
            fail(f"batch {size}: warm-up tick count differs from experiment setting")
        if any(int(item[key]) != count for key in
               ("rows_requested", "rows_written_by_logger", "rows_read_back", "distinct_sequences")):
            fail(f"batch {size}: stored row counts do not match")
        if int(item["first_sequence"]) != 0 or int(item["last_sequence"]) != count - 1:
            fail(f"batch {size}: stored sequence range is incomplete")
        if int(item.get("bad_quotes", 0)) != 0:
            fail(f"batch {size}: invalid bid/ask quote found in stored rows")
        if number(item["rows_per_second"], f"batch {size} throughput") <= 0:
            fail(f"batch {size}: throughput must be positive")
    if not csv_path.is_file():
        fail("storage_batch_sweep.csv is missing")
    with csv_path.open(newline="", encoding="utf-8") as stream:
        csv_rows = list(csv.DictReader(stream))
    if {int(item["batch_size"]) for item in csv_rows} != sizes or len(csv_rows) != len(results):
        fail("DuckDB batch sweep CSV does not match JSON results")
    print("PASS DuckDB batch-size sweep: 3 verified settings")


def check_gil_comparison_if_present() -> None:
    path = ARTIFACTS / "gil_comparison_benchmark.json"
    if not path.exists():
        print("SKIP paired Python/C++ pipeline benchmark (report not generated)")
        return
    row = load_json(path)
    ticks = int(row["ticks_per_run"])
    repeats = int(row["measured_repeats_per_implementation"])
    if ticks < 1 or repeats < 1 or int(row["warmup_invocations_per_implementation"]) != 1:
        fail("paired pipeline benchmark tick/repeat/warm-up metadata is invalid")
    native = row["native_cpp"]
    python = row["python_threaded"]
    host = row.get("host", {})
    if host.get("python_implementation") != "cpython":
        fail("paired comparison baseline must be CPython")
    if host.get("python_gil_enabled") is not True:
        fail("paired comparison must verify that the Python baseline uses an enabled GIL")
    parity = row.get("semantic_parity", {})
    if parity.get("passed") is not True:
        fail("paired pipeline benchmark did not establish semantic parity")
    for key, detail in parity.get("checks", {}).items():
        if detail.get("match") is not True or detail.get("native_cpp") != detail.get("python_threaded"):
            fail(f"paired pipeline semantic mismatch: {key}")
    required_parity = {
        "ticks", "warmup_ticks", "measured_ticks", "signals_accepted",
        "signals_debounced", "stop_triggers", "stop_limit_marketable_at_gap",
        "invalid_ticks", "queue_capacity",
    }
    if set(parity.get("checks", {})) != required_parity:
        fail("paired pipeline semantic parity checks are incomplete")
    for label, result in (("native C++", native), ("Python threaded", python)):
        if int(result["ticks"]) != ticks:
            fail(f"{label}: tick count does not match the requested workload")
        if int(result["measured_runs"]) != repeats:
            fail(f"{label}: measured repeat count does not match settings")
        if int(result["warmup_ticks"]) != min(ticks // 10, 10_000):
            fail(f"{label}: per-run warm-up count is inconsistent")
        if int(result["measured_ticks"]) != ticks - int(result["warmup_ticks"]):
            fail(f"{label}: measured tick count is inconsistent")
        if int(result["signals_accepted"]) + int(result["signals_debounced"]) != ticks:
            fail(f"{label}: accepted + debounced counts do not cover all ticks")
        if int(result["stop_triggers"]) != 1 or bool(result["stop_limit_marketable_at_gap"]):
            fail(f"{label}: injected crash stop-limit outcome is unexpected")
        if int(result["invalid_ticks"]) != 0:
            fail(f"{label}: generated workload contained invalid ticks")
        if int(result["queue_capacity"]) != 65_536:
            fail(f"{label}: queue capacity does not match the paired benchmark")
        rates = number(result["measured_throughput_events_per_second"], f"{label} throughput")
        if rates <= 0:
            fail(f"{label}: throughput must be positive")
        latencies = [number(result[f"sampled_processing_{q}_us"], f"{label} {q}")
                     for q in ("p50", "p95", "p99")]
        if not (0 <= latencies[0] <= latencies[1] <= latencies[2]):
            fail(f"{label}: sampled processing latency quantiles are invalid")
        raw = result.get("raw_measured_runs", [])
        if len(raw) != repeats:
            fail(f"{label}: raw measured-run records are missing")
        if any(int(item["ticks"]) != ticks or int(item["invalid_ticks"]) != 0 for item in raw):
            fail(f"{label}: a raw measured run failed workload checks")
    if native.get("queue_lock_free_atomics") is not True:
        fail("native C++ SPSC queue atomics did not report lock-free on this host")
    if python.get("queue_lock_free_atomics") is not False:
        fail("Python queue baseline metadata is incorrect")
    speedup = number(row["native_cpp_speedup_over_python_threaded"], "native/Python speedup")
    expected = number(native["measured_throughput_events_per_second"], "native throughput") / number(
        python["measured_throughput_events_per_second"], "Python throughput")
    if speedup <= 0 or abs(speedup - expected) > max(1e-6, expected * 1e-6):
        fail("native/Python speedup does not match the measured throughput ratio")
    print(f"PASS paired native/Python pipeline benchmark: semantic parity; {speedup:.2f}x throughput ratio")


def check_svgs_and_readme() -> None:
    svg_paths = sorted(ASSETS.glob("*.svg"))
    plot_names = {
        "policy-throughput.svg", "policy-latency-percentiles.svg",
        "signal-gating-counts.svg", "quote-quality-faults.svg",
        "stop-limit-gap-boundary.svg", "cpp-throughput.svg",
        "cpp-latency-percentiles.svg", "zmq-round-trip-latency.svg",
    }
    expected_assets = plot_names
    actual_assets = {path.name for path in svg_paths}
    if actual_assets != expected_assets:
        fail(f"expected exactly eight Matplotlib plots and no architecture diagram; found {sorted(actual_assets)}")
    ns = "{http://www.w3.org/2000/svg}"
    for path in svg_paths:
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as exc:
            fail(f"invalid SVG {path.relative_to(ROOT)}: {exc}")
        if root.tag != ns + "svg" or not root.get("viewBox"):
            fail(f"{path.name}: expected SVG root and viewBox")
        view = [float(part) for part in root.get("viewBox", "").split()]
        if len(view) != 4 or view[2] <= 0 or view[3] <= 0:
            fail(f"{path.name}: invalid SVG viewBox")
        for node in root.iter(ns + "text"):
            for axis, max_value in (("x", view[2]), ("y", view[3])):
                if axis not in node.attrib:
                    continue
                try:
                    coords = [float(part) for part in re.split(r"[ ,]+", node.attrib[axis].strip()) if part]
                except ValueError:
                    fail(f"{path.name}: non-numeric text {axis} coordinate")
                if any(value < 0 or value > max_value for value in coords):
                    fail(f"{path.name}: text coordinate falls outside the viewBox")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    refs = re.findall(r"src=[\"']([^\"']+\.svg)[\"']", readme)
    for rel in refs:
        if not (ROOT / rel).is_file():
            fail(f"README refers to a missing SVG: {rel}")
    if not plot_names.issubset({Path(rel).name for rel in refs}):
        fail("README must display all eight generated Matplotlib plots")
    if (ROOT / "main.png").exists() or any(p.name.lower() == "main.png" for p in ROOT.rglob("*")):
        fail("main.png must not be present")
    licenses = list(ROOT.glob("LICENSE*"))
    if [p.name for p in licenses] != ["LICENSE"]:
        fail("keep one project LICENSE file; separate, unused license copies should not remain")
    print(f"PASS SVG layout and README links: {len(svg_paths)} plot files")


def check_author() -> None:
    package = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    authors = (ROOT / "AUTHORS.md").read_text(encoding="utf-8").strip()
    citation = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    if 'authors = [{ name = "Pirate-Emperor" }]' not in package:
        fail("pyproject.toml author must be Pirate-Emperor")
    if authors != "# Author\n\n**Pirate-Emperor**":
        fail("AUTHORS.md should list only Pirate-Emperor")
    if 'name: "Pirate-Emperor"' not in citation:
        fail("CITATION.cff author must be Pirate-Emperor")
    print("PASS project author metadata")


def main() -> int:
    try:
        check_author()
        check_experiment()
        check_cpp()
        check_zmq()
        check_native_zmq_if_present()
        check_shared_memory_if_present()
        check_shared_memory_sweep_if_present()
        check_gil_comparison_if_present()
        check_storage_if_present()
        check_storage_sweep_if_present()
        check_svgs_and_readme()
    except (KeyError, TypeError, ValueError, OSError) as exc:
        fail(str(exc))
    print("All report checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
