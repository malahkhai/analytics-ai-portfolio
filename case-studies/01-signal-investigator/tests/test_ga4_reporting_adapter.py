
"""Tests for the executive reporting adapter."""

import json
import unittest
from pathlib import Path

from src.ga4_reporting_adapter import build_reporting_rows


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class TestGA4ReportingAdapter(unittest.TestCase):

    def setUp(self):
        # Load fresh fixture data for every test.
        self.diagnostics = json.loads(
            (FIXTURES / "ga4_diagnostics.json")
            .read_text(encoding="utf-8")
        )

        self.ai_report = json.loads(
            (
                FIXTURES /
                "ga4_ai_structured_2020-12-07.json"
            ).read_text(encoding="utf-8")
        )

    def build_rows(self):
        return build_reporting_rows(
            self.diagnostics,
            self.ai_report,
        )

    def test_nine_reporting_rows(self):
        rows = self.build_rows()

        self.assertEqual(len(rows), 9)

    def test_only_one_ai_investigation(self):
        rows = self.build_rows()

        ai_rows = [
            row for row in rows
            if row["has_ai_investigation"]
        ]

        self.assertEqual(len(ai_rows), 1)
        self.assertEqual(
            ai_rows[0]["investigation_date"],
            "2020-12-07",
        )

    def test_december_7_metrics_preserved(self):
        rows = self.build_rows()

        target = next(
            row for row in rows
            if row["investigation_date"] == "2020-12-07"
        )

        self.assertEqual(
            target["observed_sessions"], 5461
        )
        self.assertEqual(
            target["session_change_pct"], 42.0
        )
        self.assertEqual(
            target["purchase_rate_change_pct"], -14.5
        )
        self.assertEqual(
            target["factual_review_status"], "pending"
        )
        self.assertTrue(target["executive_summary"])

    def test_other_dates_have_no_ai_summary(self):
        rows = self.build_rows()

        others = [
            row for row in rows
            if row["investigation_date"] != "2020-12-07"
        ]

        for row in others:
            self.assertFalse(
                row["has_ai_investigation"]
            )
            self.assertIsNone(
                row["executive_summary"]
            )
            self.assertEqual(
                row["factual_review_status"],
                "not_generated",
            )

    def test_mismatched_metrics_rejected(self):
        self.ai_report["source_evidence"]["evidence"][
            "observed_sessions"
        ] = 9999

        with self.assertRaises(ValueError):
            self.build_rows()

    def test_unmatched_ai_date_rejected(self):
        self.ai_report["source_evidence"]["evidence"][
            "date"
        ] = "2020-12-31"

        with self.assertRaises(ValueError):
            self.build_rows()

    def test_empty_evaluations_rejected(self):
        self.diagnostics["evaluations"] = []

        with self.assertRaises(ValueError):
            self.build_rows()


if __name__ == "__main__":
    unittest.main()
