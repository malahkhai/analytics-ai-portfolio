"""Offline guardrails: AI may only select supported verified components."""
import unittest

from src.dashboard_presentation import validate_dashboard_spec


class TestDashboardSpecContract(unittest.TestCase):
    def setUp(self):
        self.row = {
            "observed_sessions": 5461,
            "session_change_pct": 42.0,
            "observed_purchase_rate_pct": 1.67,
            "baseline_purchase_rate_pct": 1.95,
            "baseline_sessions": 3846.0,
            "purchase_rate_change_pct": -14.5,
            "estimated_purchase_session_gap": 15.5,
            "has_ai_investigation": True,
            "executive_summary": "An evidence-grounded analysis",
            "why_no_alert": "Decline below the threshold",
            "hypotheses_json": "[]",
            "recommended_checks_json": "[]",
        }
        self.spec = {
            "headline": "Traffic up and purchase rate down",
            "kpis": ["observed_sessions", "observed_purchase_rate_pct"],
            "charts": ["sessions_vs_baseline", "purchase_rate_vs_baseline"],
            "sections": ["executive_summary"],
        }

    def validate(self):
        return validate_dashboard_spec(self.spec, [self.row], self.row)

    def test_valid_spec(self):
        self.assertIs(self.validate(), self.spec)

    def test_made_up_kpi_rejected(self):
        self.spec["kpis"] = ["observed_sessions", "revenue_eur"]
        with self.assertRaises(ValueError): self.validate()

    def test_unavailable_chart_rejected(self):
        del self.row["baseline_sessions"]
        with self.assertRaises(ValueError): self.validate()

    def test_duplicate_component_rejected(self):
        self.spec["charts"] = ["sessions_vs_baseline"] * 2
        with self.assertRaises(ValueError): self.validate()

    def test_ai_section_not_available_rejected(self):
        self.row["has_ai_investigation"] = False
        with self.assertRaises(ValueError): self.validate()

    def test_arbitrary_code_field_rejected(self):
        self.spec["python_code"] = "import os"
        with self.assertRaises(ValueError): self.validate()


if __name__ == "__main__":
    unittest.main()
