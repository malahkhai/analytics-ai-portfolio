"""Offline verification of evidence-only executive report and its PDF export."""
import unittest

from src.dashboard_presentation import severity
from src.executive_report import (
    alert_reason, decision, email_brief, kpi_definitions, report_window,
    severity_counts, short_summary, suggested_owner_role,
)
from src.executive_pdf import generate_pdf


def example_row():
    return {
        "investigation_date": "2020-12-07",
        "scope": "all_channels_aggregated",
        "observed_sessions": 5461,
        "baseline_sessions": 3846.0,
        "session_change_pct": 42.0,
        "observed_purchase_rate_pct": 1.67,
        "baseline_purchase_rate_pct": 1.95,
        "purchase_rate_change_pct": -14.5,
        "estimated_purchase_session_gap": 15.5,
        "alert_status": "no_qualifying_anomaly",
        "alert_types": [],
        "has_ai_investigation": True,
        "executive_summary": "Sessions increased while purchase rate declined. No proven cause.",
        "why_no_alert": "The 35 percent conversion threshold was not met.",
        "hypotheses_json": '[{"title":"Traffic quality","data_needed":["channels"],"explanation":"Possible change in mix","validation_check":"Compare source/medium"}]',
        "recommended_checks_json": '[{"action":"Inspect channel distribution","purpose":"Check traffic mix","inputs_needed":["channel", "sessions"]}]',
        "factual_review_status": "pending",
    }


class TestExecutiveReport(unittest.TestCase):
    def setUp(self):
        self.row = example_row()

    def test_yellow_is_watch_not_official_anomaly(self):
        self.assertEqual(severity(self.row), "yellow")
        self.assertIn("rate", alert_reason(self.row))

    def test_no_false_business_impact_or_due_date(self):
        action = decision(self.row)
        self.assertEqual(action["impact"], "Not estimated")
        self.assertEqual(action["owner"], "Acquisition Manager")
        self.assertTrue(action["owner_is_illustrative"])
        self.assertEqual(action["deadline"], "Not set")

    def test_email_is_explicit_about_source_and_review(self):
        email = email_brief(self.row, [self.row])
        self.assertIn("2020-12-07", email)
        self.assertIn("pending review", email)
        self.assertIn("5461", email.replace(",", ""))
        self.assertNotIn("$50K", email)

    def test_kpis_use_only_reportable_fields(self):
        cards = kpi_definitions(self.row)
        self.assertEqual(len(cards), 6)
        self.assertEqual(cards[0]["value"], "5,461")
        self.assertFalse(any("revenue" in c["title"].lower() for c in cards))

    def test_window_uses_evidence_dates(self):
        self.assertEqual(report_window([self.row]), "07 Dec – 07 Dec 2020")
        self.assertEqual(severity_counts([self.row])["yellow"], 1)

    def test_pdf_export_is_two_page_pdf_without_copying_reference_metrics(self):
        try:
            import pypdf
        except ImportError:
            pypdf = None
        blob = generate_pdf(self.row, [self.row])
        self.assertTrue(blob.startswith(b"%PDF"))
        self.assertGreater(len(blob), 3000)
        if pypdf:
            from io import BytesIO
            pdf = pypdf.PdfReader(BytesIO(blob))
            self.assertEqual(len(pdf.pages), 2)
            extracted = " ".join(p.extract_text() or "" for p in pdf.pages)
            self.assertIn("Signal Investigator", extracted)
            self.assertNotIn("$50K", extracted)


if __name__ == "__main__":
    unittest.main()
