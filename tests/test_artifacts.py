from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_FIGURES = {
    "architecture.svg",
    "performance-comparison.svg",
    "flash-crash-analysis.svg",
}


class SavedArtifactTests(unittest.TestCase):
    def test_experiment_counts_are_consistent(self) -> None:
        summary = json.loads((ROOT / "artifacts" / "experiment_summary.json").read_text(encoding="utf-8"))
        total = int(summary["input_event_count_with_duplicates"])
        self.assertEqual(len(summary["policies"]), 3)
        for row in summary["policies"]:
            counted = sum(int(row[name]) for name in (
                "accepted_signals", "debounced_signals", "duplicate_sequences",
                "out_of_order_timestamps", "stale_quotes", "future_quotes",
            ))
            self.assertEqual(counted, total)

    def test_exactly_three_committed_figures_are_well_formed(self) -> None:
        paths = sorted((ROOT / "docs" / "assets").glob("*.svg"))
        self.assertEqual({path.name for path in paths}, EXPECTED_FIGURES)
        for path in paths:
            with self.subTest(path=path.name):
                root = ET.parse(path).getroot()
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                self.assertIsNotNone(root.get("viewBox"))

    def test_benchmark_figure_keeps_current_hpc_measurements(self) -> None:
        path = ROOT / "docs" / "assets" / "performance-comparison.svg"
        text = " ".join(ET.parse(path).getroot().itertext())
        for value in ("38.68M/s", "168.46×", "3.546 / 6.452",
                      "26.249 / 33.012", "10.10M", "136,065,024 bytes"):
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_crash_figure_keeps_local_window_and_gap_boundaries(self) -> None:
        path = ROOT / "docs" / "assets" / "flash-crash-analysis.svg"
        text = " ".join(ET.parse(path).getroot().itertext())
        for value in ("180 bps", "199 / 199", "20 / 199", "0 / 199",
                      "90.00875%", "7.5 bps", "not marketable"):
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_main_png_and_duplicate_project_licenses_are_absent(self) -> None:
        self.assertFalse((ROOT / "main.png").exists())
        self.assertEqual([p.name for p in ROOT.glob("LICENSE*")], ["LICENSE"])


if __name__ == "__main__":
    unittest.main()
