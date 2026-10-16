from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
EXPECTED_PLOTS = {
    "policy-throughput.svg",
    "policy-latency-percentiles.svg",
    "signal-gating-counts.svg",
    "quote-quality-faults.svg",
    "stop-limit-gap-boundary.svg",
    "cpp-throughput.svg",
    "cpp-latency-percentiles.svg",
    "zmq-round-trip-latency.svg",
}
EXPECTED_FIGURES = {"architecture.svg", *EXPECTED_PLOTS}


class SavedArtifactTests(unittest.TestCase):
    def svg_text(self, name: str) -> str:
        return " ".join(ET.parse(ASSETS / name).getroot().itertext())

    def test_experiment_counts_are_consistent(self) -> None:
        summary = json.loads(
            (ROOT / "artifacts" / "experiment_summary.json").read_text(encoding="utf-8")
        )
        total = int(summary["input_event_count_with_duplicates"])
        self.assertEqual(len(summary["policies"]), 3)
        for row in summary["policies"]:
            counted = sum(int(row[name]) for name in (
                "accepted_signals", "debounced_signals", "duplicate_sequences",
                "out_of_order_timestamps", "stale_quotes", "future_quotes",
            ))
            self.assertEqual(counted, total)

    def test_nine_committed_figures_are_well_formed(self) -> None:
        paths = sorted(ASSETS.glob("*.svg"))
        self.assertEqual({path.name for path in paths}, EXPECTED_FIGURES)
        for path in paths:
            with self.subTest(path=path.name):
                root = ET.parse(path).getroot()
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                view = root.get("viewBox")
                self.assertIsNotNone(view)
                self.assertEqual(len(view.split()), 4)

    def test_eight_matplotlib_plots_have_titles_without_footer_text(self) -> None:
        expected_titles = {
            "policy-throughput.svg": "Quote-policy throughput",
            "policy-latency-percentiles.svg": "Quote-policy latency percentiles",
            "signal-gating-counts.svg": "Signal gating by policy",
            "quote-quality-faults.svg": "Quote-quality fault counts",
            "stop-limit-gap-boundary.svg": "Stop-limit marketability boundary",
            "cpp-throughput.svg": "Native C++ event throughput",
            "cpp-latency-percentiles.svg": "Native C++ sampled latency",
            "zmq-round-trip-latency.svg": "ZeroMQ IPC round-trip latency",
        }
        for name, title in expected_titles.items():
            with self.subTest(plot=name):
                text = self.svg_text(name)
                self.assertIn(title, text)
                self.assertNotIn("Synthetic experiment", text)
                self.assertNotIn("Machine-dependent measurements", text)
                self.assertNotIn("Source: artifacts/", text)

    def test_plot_units_and_interpretation_are_explicit(self) -> None:
        throughput = self.svg_text("cpp-throughput.svg")
        self.assertIn("million events/s", throughput)
        self.assertIn("9,990,000 measured", throughput)
        self.assertIn("10,000 warm-up", throughput)

        latency = self.svg_text("cpp-latency-percentiles.svg")
        self.assertIn("Sampled processing latency (μs)", latency)
        self.assertIn("hot path only", latency)

        zmq = self.svg_text("zmq-round-trip-latency.svg")
        self.assertIn("Process-to-process round-trip (μs)", zmq)
        self.assertIn("Max observed:", zmq)

        gap = self.svg_text("stop-limit-gap-boundary.svg")
        self.assertIn("Injected price gap (bps)", gap)
        self.assertIn("7.5", gap)
        self.assertIn("Yes", gap)
        self.assertIn("No", gap)

        signal = self.svg_text("signal-gating-counts.svg")
        self.assertIn("Blue = accepted", signal)
        self.assertIn("Orange = debounced", signal)

    def test_main_png_and_duplicate_project_licenses_are_absent(self) -> None:
        self.assertFalse((ROOT / "main.png").exists())
        self.assertEqual([p.name for p in ROOT.glob("LICENSE*")], ["LICENSE"])


if __name__ == "__main__":
    unittest.main()
