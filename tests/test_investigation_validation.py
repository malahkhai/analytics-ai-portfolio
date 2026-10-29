
"""Verify invalid data blocks the investigation pipeline."""

import csv
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "data" / "daily_paid_search_funnel.csv"


class TestInvestigationValidation(unittest.TestCase):

    def test_invalid_data_blocks_investigation(self):

        # Step 1: Load the original dataset
        with ORIGINAL.open(
            newline="", encoding="utf-8"
        ) as file:
            reader = csv.DictReader(file)
            columns = reader.fieldnames
            rows = list(reader)

        # Step 2: Create a copy in memory
        bad_rows = [row.copy() for row in rows]

        # Deliberately introduce invalid checkout data
        bad_rows[-1]["begin_checkout_sessions"] = "350"

        # Step 3: Create temporary test files
        with tempfile.TemporaryDirectory() as folder:
            test_data = Path(folder) / "invalid_funnel.csv"
            test_report = Path(folder) / "investigation.md"

            with test_data.open(
                "w", newline="", encoding="utf-8"
            ) as file:
                writer = csv.DictWriter(
                    file, fieldnames=columns
                )
                writer.writeheader()
                writer.writerows(bad_rows)

            # Step 4: Run investigator with invalid data
            environment = os.environ.copy()
            environment["SIGNAL_FUNNEL_DATA"] = str(
                test_data
            )
            environment["SIGNAL_FUNNEL_OUTPUT"] = str(
                test_report
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "src.investigate_funnel",
                ],
                cwd=ROOT,
                env=environment,
                capture_output=True,
                text=True,
            )

            # Step 5: Verify the investigation stopped
            self.assertNotEqual(result.returncode, 0)

            self.assertIn(
                "DATA QUALITY CHECK FAILED",
                result.stdout
            )

            self.assertIn(
                "begin_checkout_sessions (350) exceeds",
                result.stdout
            )

            # Step 6: Invalid data must not create a report
            self.assertFalse(test_report.exists())


if __name__ == "__main__":
    unittest.main()
