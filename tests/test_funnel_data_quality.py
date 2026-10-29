
"""Data-quality tests for our ecommerce funnel dataset."""

import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "daily_paid_search_funnel.csv"

# These stages should not increase as users progress.
STAGES = [
    "sessions",
    "view_item_sessions",
    "add_to_cart_sessions",
    "begin_checkout_sessions",
    "payment_attempt_sessions",
    "orders",
]

COUNT_COLUMNS = STAGES + ["payment_failed_sessions"]


class TestFunnelDataQuality(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Load the dataset once for all our tests.
        with DATA.open(newline="", encoding="utf-8") as file:
            cls.rows = list(csv.DictReader(file))

    def test_no_negative_or_missing_counts(self):
        for row in self.rows:
            for column in COUNT_COLUMNS:
                with self.subTest(date=row["date"], column=column):
                    value = int(row[column])
                    self.assertGreaterEqual(value, 0)

    def test_funnel_stage_order(self):
        for row in self.rows:
            for i in range(1, len(STAGES)):
                previous = int(row[STAGES[i - 1]])
                current = int(row[STAGES[i]])

                with self.subTest(
                    date=row["date"],
                    stage=STAGES[i]
                ):
                    self.assertLessEqual(current, previous)

    def test_payment_failures_do_not_exceed_attempts(self):
        for row in self.rows:
            failures = int(row["payment_failed_sessions"])
            attempts = int(row["payment_attempt_sessions"])

            with self.subTest(date=row["date"]):
                self.assertLessEqual(failures, attempts)

    def test_unique_date_and_channel(self):
        keys = [
            (row["date"], row["channel"])
            for row in self.rows
        ]

        self.assertEqual(len(keys), len(set(keys)))


if __name__ == "__main__":
    unittest.main()
