
"""Tests for GA4 performance diagnostic reporting."""

import unittest
from datetime import date, timedelta

from src.ga4_diagnostics import build_diagnostic_report


class TestGA4Diagnostics(unittest.TestCase):

    def make_rows(
        self,
        current_sessions=1000,
        current_purchases=50,
        history_weeks=(1, 2, 3, 4),
    ):
        """Build controlled historical GA4 records."""

        target_day = date(2020, 12, 7)
        rows = []

        # Baseline: 1,000 sessions and 50 purchasing
        # sessions on each previous matching weekday.
        for week in history_weeks:
            rows.append({
                "date": target_day - timedelta(weeks=week),
                "scope": "all_channels_aggregated",
                "sessions": 1000,
                "purchasing_sessions": 50,
            })

        rows.append({
            "date": target_day,
            "scope": "all_channels_aggregated",
            "sessions": current_sessions,
            "purchasing_sessions": current_purchases,
        })

        return rows

    def test_normal_performance(self):
        report = build_diagnostic_report(self.make_rows())

        self.assertEqual(report["dates_evaluated"], 1)
        self.assertEqual(report["qualifying_alerts"], 0)

        result = report["evaluations"][0]

        self.assertEqual(result["session_change_pct"], 0)
        self.assertEqual(result["purchase_rate_change_pct"], 0)
        self.assertEqual(
            result["status"],
            "no_qualifying_anomaly",
        )

    def test_performance_observation_without_alert(self):
        # Traffic increases, conversion rate declines 20%,
        # and expected purchasing-session gap is 20.
        rows = self.make_rows(
            current_sessions=2000,
            current_purchases=80,
        )

        report = build_diagnostic_report(rows)
        result = report["evaluations"][0]

        self.assertEqual(result["session_change_pct"], 100)
        self.assertEqual(result["purchase_rate_change_pct"], -20)
        self.assertEqual(
            result["estimated_purchase_session_gap"],
            20,
        )
        self.assertEqual(report["qualifying_alerts"], 0)

    def test_conversion_alert_in_report(self):
        rows = self.make_rows(
            current_sessions=1000,
            current_purchases=10,
        )

        report = build_diagnostic_report(rows)
        result = report["evaluations"][0]

        self.assertEqual(report["qualifying_alerts"], 1)
        self.assertEqual(result["status"], "alert")
        self.assertIn(
            "session_purchase_rate_drop",
            result["alert_types"],
        )

    def test_traffic_alert_in_report(self):
        rows = self.make_rows(
            current_sessions=400,
            current_purchases=20,
        )

        report = build_diagnostic_report(rows)
        result = report["evaluations"][0]

        self.assertEqual(result["session_change_pct"], -60)
        self.assertEqual(report["qualifying_alerts"], 1)
        self.assertIn("sessions_drop", result["alert_types"])

    def test_insufficient_history(self):
        rows = self.make_rows(
            history_weeks=(1, 2, 3),
        )

        report = build_diagnostic_report(rows)

        self.assertEqual(report["dates_evaluated"], 0)
        self.assertEqual(report["qualifying_alerts"], 0)
        self.assertEqual(report["evaluations"], [])


if __name__ == "__main__":
    unittest.main()
