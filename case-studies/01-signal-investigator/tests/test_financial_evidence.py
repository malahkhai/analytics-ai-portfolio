import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.financial_evidence import validate_financial_record, load_financial_evidence, build_financial_record


class FinanceEvidenceTests(unittest.TestCase):
    def test_existing_verified_snapshot(self):
        r = load_financial_evidence(
            "2020-12-07",
            outputs=Path(__file__).resolve().parent / "fixtures",
        )
        self.assertEqual(r["purchase_revenue_usd"], 8472)
        self.assertIsNone(r["baseline_revenue_usd"])

    def test_no_other_day_revenue_invented(self):
        self.assertIsNone(load_financial_evidence("2020-12-06"))

    def test_mismatched_date_rejected(self):
        r = load_financial_evidence("2020-12-07")
        with self.assertRaises(ValueError):
            validate_financial_record(r, "2020-12-06")

    def test_historical_baseline(self):
        baseline = ["2020-11-09", "2020-11-16", "2020-11-23", "2020-11-30"]
        day = "2020-12-07"
        daily = {d: {"purchase_revenue_usd": 5000, "purchase_events": 100, "purchases_with_revenue": 100, "positive_revenue_events": 99, "distinct_transaction_ids": 99} for d in baseline}
        daily[day] = {"purchase_revenue_usd": 8472, "purchase_events": 110, "purchases_with_revenue": 110, "positive_revenue_events": 106, "distinct_transaction_ids": 105}
        r = build_financial_record(day, baseline, daily)
        self.assertEqual(r["baseline_revenue_usd"], 5000)
        self.assertEqual(r["revenue_difference_usd"], 3472)
        self.assertEqual(r["relative_revenue_change_pct"], 69.4)

    def test_financial_pdf_can_render(self):
        from src.executive_pdf import generate_pdf
        from tests.test_executive_report import example_row
        row = example_row()
        pdf = generate_pdf(row, [row], load_financial_evidence("2020-12-07"))
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 5000)

    def test_unavailable_baseline_rejected(self):
        with self.assertRaises(ValueError):
            build_financial_record("2020-12-07", ["2020-11-09", "2020-11-16", "2020-11-23", "2020-11-30"], {})


if __name__ == "__main__":
    unittest.main()
