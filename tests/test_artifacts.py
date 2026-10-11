from __future__ import annotations

import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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

    def test_all_committed_svgs_are_well_formed(self) -> None:
        svgs = sorted((ROOT / "docs" / "assets").glob("*.svg"))
        self.assertGreaterEqual(len(svgs), 10)
        for path in svgs:
            with self.subTest(path=path.name):
                root = ET.parse(path).getroot()
                self.assertTrue(root.tag.endswith("svg"))
                self.assertIsNotNone(root.get("viewBox"))

    def test_main_png_and_duplicate_project_licenses_are_absent(self) -> None:
        self.assertFalse((ROOT / "main.png").exists())
        self.assertEqual([p.name for p in ROOT.glob("LICENSE*")], ["LICENSE"])


if __name__ == "__main__":
    unittest.main()
