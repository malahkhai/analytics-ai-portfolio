import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from src.detect import investigate, load_metrics
from src.generate_data import create_sample_data


class TestInvestigation(unittest.TestCase):
    def test_injected_anomalies_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "sample.csv"
            self.assertEqual(210, create_sample_data(file))
            alerts = investigate(load_metrics(file))
            types = {(a["date"], a["channel"], a["anomaly_type"]) for a in alerts}
            self.assertIn(("2026-10-13", "paid_search", "conversion_rate_drop"), types)
            self.assertIn(("2026-10-14", "paid_search", "conversion_rate_drop"), types)
            self.assertIn(("2026-10-20", "email", "sessions_drop"), types)

    def test_constant_series_has_no_alerts(self):
        start = date(2026, 8, 1)
        rows = [{"date": start + timedelta(days=i), "channel": "test",
                 "sessions": 1000, "orders": 50, "revenue_eur": 7500}
                for i in range(70)]
        self.assertEqual([], investigate(rows))

    def test_revenue_estimate_is_only_on_conversion_incidents(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory) / "sample.csv"
            create_sample_data(file)
            alerts = investigate(load_metrics(file))
            for alert in alerts:
                if alert["anomaly_type"] == "conversion_rate_drop":
                    self.assertGreater(alert["estimated_order_shortfall"], 0)
                    self.assertIn("caution", alert)
                else:
                    self.assertNotIn("estimated_revenue_gap_eur", alert)


if __name__ == "__main__":
    unittest.main()
