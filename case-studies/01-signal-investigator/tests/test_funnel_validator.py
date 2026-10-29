
"""Test our reusable funnel data validator."""

import csv
import unittest
from pathlib import Path

from src.validate_funnel import validate_dataset

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "daily_paid_search_funnel.csv"


class TestFunnelValidator(unittest.TestCase):

    def setUp(self):
        # Load the original data for each test
        with DATA.open(newline="", encoding="utf-8") as file:
            self.rows = list(csv.DictReader(file))

    def test_valid_data_passes(self):
        # Our original dataset should be valid
        errors = validate_dataset(self.rows)
        self.assertEqual(errors, [])

    def test_invalid_checkout_count_is_rejected(self):
        # Create an in-memory copy, not a CSV modification
        bad_rows = [row.copy() for row in self.rows]

        # Deliberately introduce impossible funnel data
        bad_rows[-1]["begin_checkout_sessions"] = "350"

        errors = validate_dataset(bad_rows)

        # Verify the validator detected the problem
        self.assertTrue(
            any("begin_checkout_sessions (350) exceeds"
                in error for error in errors),
            errors
        )

    def test_duplicate_record_is_rejected(self):
        # Create a duplicate of the first row
        bad_rows = self.rows + [self.rows[0].copy()]

        errors = validate_dataset(bad_rows)

        self.assertTrue(
            any("Duplicate date/channel" in error
                for error in errors),
            errors
        )


if __name__ == "__main__":
    unittest.main()
