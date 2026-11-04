
"""Offline tests for the GA4 performance comparison tool."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import ga4_comparison_tool


class TestGA4ComparisonTool(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.path = (
            Path(self.temp_dir.name) / "diagnostics.json"
        )

        # Controlled test data: three evaluated dates.
        self.report = {
            "evaluations": [
                {
                    "date": "2020-12-05",
                    "session_change_pct": 10.0,
                    "purchase_rate_change_pct": 20.0,
                },
                {
                    "date": "2020-12-06",
                    "session_change_pct": -10.0,
                    "purchase_rate_change_pct": -4.8,
                },
                {
                    "date": "2020-12-07",
                    "session_change_pct": 42.0,
                    "purchase_rate_change_pct": -14.5,
                },
            ]
        }

        self.path.write_text(
            json.dumps(self.report),
            encoding="utf-8",
        )

        patcher = patch.object(
            ga4_comparison_tool,
            "DIAGNOSTICS",
            self.path,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_december_7_rankings(self):
        result = ga4_comparison_tool.compare_ga4_performance(
            "2020-12-07"
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["dates_compared"], 3)
        self.assertEqual(
            result["purchase_rate_decline_rank"], 1
        )
        self.assertEqual(
            result["session_growth_rank"], 1
        )

    def test_other_date_rankings(self):
        result = ga4_comparison_tool.compare_ga4_performance(
            "2020-12-06"
        )

        self.assertEqual(
            result["purchase_rate_decline_rank"], 2
        )
        self.assertEqual(
            result["session_growth_rank"], 3
        )

    def test_invalid_date_format(self):
        result = ga4_comparison_tool.compare_ga4_performance(
            "December 7, 2020"
        )

        self.assertEqual(result["status"], "invalid_date")

    def test_impossible_calendar_date(self):
        result = ga4_comparison_tool.compare_ga4_performance(
            "2020-02-30"
        )

        self.assertEqual(result["status"], "invalid_date")

    def test_unavailable_date(self):
        result = ga4_comparison_tool.compare_ga4_performance(
            "2020-12-08"
        )

        self.assertEqual(result["status"], "not_found")

    def test_missing_evidence_file(self):
        self.path.unlink()

        result = ga4_comparison_tool.compare_ga4_performance(
            "2020-12-07"
        )

        self.assertEqual(
            result["status"], "missing_evidence"
        )


if __name__ == "__main__":
    unittest.main()
