#!/usr/bin/env python3
"""Check saved experiment values, benchmark reports, and SVG files for consistency."""
from __future__ import annotations

import csv
import json
import math
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


def check_storage_if_present() -> None:
    path = ARTIFACTS / "storage_benchmark.json"
    if not path.exists():
        print("SKIP DuckDB report invariants (run benchmark_storage.py to create a report)")
        return
    row = load_json(path)
    count = int(row["rows_requested"])
    if count < 1 or any(int(row[key]) != count for key in
                        ("rows_written_by_logger", "rows_read_back", "distinct_sequences")):
        fail("DuckDB requested, written, read-back, and unique row counts differ")
    if int(row["first_sequence"]) != 0 or int(row["last_sequence"]) != count - 1:
        fail("DuckDB sequence range is incomplete")
    if int(row["warmup_row_count"]) != count or int(row["warmup_runs"]) != 1:
        fail("DuckDB warm-up metadata is inconsistent")
    if number(row["rows_per_second"], "DuckDB throughput") <= 0 or int(row["database_bytes"]) < 1:
        fail("DuckDB throughput or database size is invalid")
    print(f"PASS DuckDB report: {count:,} unique rows verified")


def check_svgs_and_readme() -> None:
    svg_paths = sorted(ASSETS.glob("*.svg"))
    if not svg_paths:
        fail("no SVG assets found")
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
    for rel in re.findall(r"!\[[^\]]*\]\(([^)]+\.svg)\)", readme):
        if not (ROOT / rel).is_file():
            fail(f"README refers to a missing SVG: {rel}")
    if (ROOT / "main.png").exists() or any(p.name.lower() == "main.png" for p in ROOT.rglob("*")):
        fail("main.png must not be present")
    licenses = list(ROOT.glob("LICENSE*"))
    if [p.name for p in licenses] != ["LICENSE"]:
        fail("keep one project LICENSE file; separate, unused license copies should not remain")
    print(f"PASS SVG layout and README links: {len(svg_paths)} images")


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
        check_storage_if_present()
        check_svgs_and_readme()
    except (KeyError, TypeError, ValueError, OSError) as exc:
        fail(str(exc))
    print("All report checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
