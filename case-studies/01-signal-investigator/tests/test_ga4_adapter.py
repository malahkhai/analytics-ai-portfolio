
"""Unit tests for the Signal Investigator GA4 adapter."""

import unittest
from datetime import date

from src.ga4_adapter import adapt_ga4_records


class TestGA4Adapter(unittest.TestCase):

    def setUp(self):
        self.valid_record = {
            "event_day": "2020-12-01",
            "sessions": 5000,
            "purchase_events": 107,
            "purchasing_sessions": 100,
            "session_purchase_rate_pct": 2.0,
        }

    def test_valid_record(self):
        result = adapt_ga4_records([self.valid_record])

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["date"], date(2020, 12, 1))
        self.assertEqual(result[0]["sessions"], 5000)
        self.assertEqual(result[0]["purchasing_sessions"], 100)

    def test_duplicate_date_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            adapt_ga4_records([
                self.valid_record,
                self.valid_record.copy(),
            ])

    def test_zero_sessions_rejected(self):
        record = self.valid_record.copy()
        record["sessions"] = 0

        with self.assertRaises(ValueError):
            adapt_ga4_records([record])

    def test_negative_sessions_rejected(self):
        record = self.valid_record.copy()
        record["sessions"] = -100

        with self.assertRaises(ValueError):
            adapt_ga4_records([record])

    def test_purchasing_sessions_cannot_exceed_sessions(self):
        record = self.valid_record.copy()
        record["purchasing_sessions"] = 6000

        with self.assertRaises(ValueError):
            adapt_ga4_records([record])

    def test_purchase_events_cannot_be_less_than_purchasing_sessions(self):
        record = self.valid_record.copy()
        record["purchase_events"] = 50

        with self.assertRaises(ValueError):
            adapt_ga4_records([record])

    def test_incorrect_conversion_rate_rejected(self):
        record = self.valid_record.copy()
        record["session_purchase_rate_pct"] = 8.0

        with self.assertRaises(ValueError):
            adapt_ga4_records([record])


if __name__ == "__main__":
    unittest.main()
