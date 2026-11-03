
"""Unit tests for GA4 anomaly detection."""

import unittest
from datetime import date, timedelta

from src.detect_ga4 import detect_ga4_anomalies


class TestGA4Detection(unittest.TestCase):

    def setUp(self):
        self.target_day = date(2020, 12, 1)

    def make_rows(
        self,
        current_sessions=1000,
        current_purchases=50,
    ):
        """Create four matching weekday baselines and one target day."""

        rows = []

        # Historical baseline: 1,000 sessions and
        # 50 purchasing sessions (5% purchase rate).
        for week in (1, 2, 3, 4):
            rows.append({
                "date": self.target_day - timedelta(weeks=week),
                "scope": "all_channels_aggregated",
                "sessions": 1000,
                "purchasing_sessions": 50,
            })

        rows.append({
            "date": self.target_day,
            "scope": "all_channels_aggregated",
            "sessions": current_sessions,
            "purchasing_sessions": current_purchases,
        })

        return rows

    def test_normal_performance_no_alert(self):
        rows = self.make_rows()

        alerts = detect_ga4_anomalies(rows)

        self.assertEqual(len(alerts), 0)

    def test_conversion_rate_drop_detected(self):
        # Purchase rate drops from 5% to 1%.
        rows = self.make_rows(
            current_sessions=1000,
            current_purchases=10,
        )

        alerts = detect_ga4_anomalies(rows)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(
            alerts[0]["anomaly_type"],
            "session_purchase_rate_drop",
        )
        self.assertEqual(alerts[0]["severity"], "high")
        self.assertEqual(
            alerts[0]["estimated_purchase_session_shortfall"],
            40.0,
        )

    def test_traffic_drop_detected(self):
        # Sessions drop by 60%, but purchase rate
        # remains at 5%.
        rows = self.make_rows(
            current_sessions=400,
            current_purchases=20,
        )

        alerts = detect_ga4_anomalies(rows)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(
            alerts[0]["anomaly_type"],
            "sessions_drop",
        )
        self.assertEqual(alerts[0]["severity"], "high")

    def test_insufficient_history_no_alert(self):
        rows = self.make_rows()

        # Remove one required historical weekday.
        rows.pop(0)

        alerts = detect_ga4_anomalies(rows)

        self.assertEqual(len(alerts), 0)

    def test_both_anomalies_detected(self):
        # Traffic drops by 60% and purchase rate
        # drops from 5% to 1.25%.
        rows = self.make_rows(
            current_sessions=400,
            current_purchases=5,
        )

        alerts = detect_ga4_anomalies(rows)

        anomaly_types = {
            alert["anomaly_type"] for alert in alerts
        }

        self.assertEqual(len(alerts), 2)
        self.assertEqual(anomaly_types, {
            "sessions_drop",
            "session_purchase_rate_drop",
        })


if __name__ == "__main__":
    unittest.main()
