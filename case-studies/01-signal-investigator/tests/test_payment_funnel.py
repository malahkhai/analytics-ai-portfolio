
"""Automated test for our payment funnel investigation."""

import subprocess
import sys
import unittest
from pathlib import Path

# Locate our main project folder
ROOT = Path(__file__).resolve().parents[1]


class TestPaymentFunnel(unittest.TestCase):

    def test_payment_investigation(self):

        # STEP 1: Run our existing investigation script
        result = subprocess.run(
            [sys.executable, "-m", "src.investigate_funnel"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True
        )

        # STEP 2: Verify the biggest deterioration
        self.assertIn(
            "Biggest deterioration: Orders / payment-attempt sessions",
            result.stdout
        )

        # STEP 3: Verify the conversion rate change
        self.assertIn(
            "Change: -47.87 percentage points",
            result.stdout
        )

        # STEP 4: Verify failed-payment share
        self.assertIn(
            "Failed-payment share: 3.46% -> 59.04%",
            result.stdout
        )

        # STEP 5: Verify the report was created
        report = ROOT / "outputs" / "funnel_investigation.md"

        self.assertTrue(report.exists())

        # STEP 6: Verify our conclusion is evidence-aware
        content = report.read_text(encoding="utf-8")

        self.assertIn(
            "Root cause remains unverified",
            content
        )


if __name__ == "__main__":
    unittest.main()
