"""Regression tests for the existing dashboard cleanup and financial guard."""
from io import BytesIO
from pathlib import Path
import unittest

from src.executive_report import display_action_title, executive_headline
from src.executive_pdf import generate_pdf
from src.email_delivery import compose_sample
from src.financial_evidence import matching_financial_evidence, load_financial_evidence
from tests.test_executive_report import example_row


def red_case():
    row = example_row()
    row.update({
        "observed_purchase_rate_pct": 1.03,
        "purchase_rate_change_pct": -47.4,
        "estimated_purchase_session_gap": 50.5,
        "alert_status": "qualifying_anomaly",
        "alert_types": ["session_purchase_rate_drop"],
        "executive_summary": "Sessions increased while the purchase-session rate fell. Cause unverified.",
    })
    return row


class DashboardCleanupTests(unittest.TestCase):
    def test_dynamic_headline_uses_selected_report_values(self):
        self.assertEqual(executive_headline(red_case()),
                         "Purchase rate fell 47.4% as traffic rose 42.0%")
        self.assertEqual(executive_headline(example_row()),
                         "Purchase rate fell 14.5% as traffic rose 42.0%")

    def test_business_language_without_changing_evidence(self):
        self.assertEqual(display_action_title("Dimension and channel decomposition"),
                         "Break down performance by traffic channel and device")
        self.assertEqual(display_action_title("Inspect inventory availability"),
                         "Inspect inventory availability")

    def test_revenue_for_original_only(self):
        self.assertEqual(matching_financial_evidence(example_row())["purchase_revenue_usd"], 8472)
        self.assertIsNone(matching_financial_evidence(red_case()))
        self.assertIsNone(matching_financial_evidence(dict(red_case(), investigation_date="2020-12-06")))

    def test_pdf_and_email_do_not_reuse_historical_revenue_for_red(self):
        red = red_case()
        historical_revenue = load_financial_evidence("2020-12-07")
        subject, body = compose_sample(red, red["executive_summary"], historical_revenue)
        self.assertIn("Purchase rate fell 47.4%", subject)
        self.assertNotIn("8,472", body)
        self.assertIn("not available", body)
        blob = generate_pdf(red, [red], historical_revenue)
        self.assertTrue(blob.startswith(b"%PDF"))
        from pypdf import PdfReader
        extracted = " ".join(page.extract_text() or "" for page in PdfReader(BytesIO(blob)).pages)
        self.assertNotIn("8,472", extracted)
        self.assertIn("Purchase rate fell 47.4%", extracted)

    def test_report_row_modeled_finance_reaches_email_and_pdf(self):
        from src.financial_evidence import reporting_financial_evidence
        from pypdf import PdfReader
        from io import BytesIO
        red = red_case()
        red.update({
            "purchase_revenue_usd": 5213.54,
            "baseline_revenue_usd": 6918.0,
            "revenue_difference_usd": -1704.46,
            "revenue_change_pct": -24.6,
            "revenue_evidence_type": "modeled",
            "purchase_events_with_revenue": 60,
        })
        finance = reporting_financial_evidence(red)
        self.assertEqual(finance["purchase_revenue_usd"], 5213.54)
        self.assertEqual(finance["revenue_evidence_type"], "modeled")
        _, body = compose_sample(red, red["executive_summary"])
        self.assertIn("Modeled purchase revenue: $5,213.54", body)
        self.assertIn("-1,704.46", body)
        self.assertNotIn("8,472", body)
        blob = generate_pdf(red, [red])
        extracted = " ".join(page.extract_text() or "" for page in PdfReader(BytesIO(blob)).pages)
        self.assertIn("Modeled revenue", extracted)
        self.assertNotIn("8,472", extracted)

    def test_incomplete_report_finance_does_not_fallback_to_historical(self):
        from src.financial_evidence import reporting_financial_evidence
        red = red_case()
        red["purchase_revenue_usd"] = 5213.54
        self.assertIsNone(reporting_financial_evidence(red))
        self.assertIsNone(reporting_financial_evidence(red, load_financial_evidence("2020-12-07")))

    def test_dashboard_no_longer_uses_hardcoded_red_replay(self):
        source = (Path(__file__).resolve().parents[1] / "streamlit_app.py").read_text()
        self.assertNotIn("scenario_rows", source)
        self.assertNotIn("maxim_interview_demo_toggle", source)
        self.assertNotIn("Simulate red alert", source)
        self.assertIn('reporting_financial_evidence(selected)', source)


if __name__ == '__main__':
    unittest.main()
