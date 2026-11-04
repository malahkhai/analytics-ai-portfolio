
"""Tests for the structured Gemini investigation output."""

import json
import unittest
from pathlib import Path

from src.ai_investigation_structured import AIInterpretation


ROOT = Path(__file__).resolve().parents[1]


FIXTURES = ROOT / "tests" / "fixtures"

AI_OUTPUT = (
    FIXTURES / "ga4_ai_structured_2020-12-07.json"
)

SOURCE_DATA = (
    FIXTURES / "ga4_diagnostics.json"
)



class TestStructuredAIInvestigation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.result = json.loads(
            AI_OUTPUT.read_text(encoding="utf-8")
        )

        cls.diagnostics = json.loads(
            SOURCE_DATA.read_text(encoding="utf-8")
        )

        cls.interpretation = AIInterpretation.model_validate(
            cls.result["ai_interpretation"]
        )

    def test_original_evidence_preserved(self):
        """AI report must retain the original metrics."""

        source_evidence = next(
            row for row in self.diagnostics["evaluations"]
            if row["date"] == "2020-12-07"
        )

        saved_evidence = self.result[
            "source_evidence"
        ]["evidence"]

        self.assertEqual(
            saved_evidence,
            source_evidence,
        )

    def test_alert_conditions_are_correct(self):
        """Check alert conditions using original numbers."""

        evidence = self.result[
            "source_evidence"
        ]["evidence"]

        conditions = self.result[
            "source_evidence"
        ]["alert_condition_results"]

        self.assertEqual(
            conditions["minimum_sessions_met"],
            evidence["observed_sessions"] >= 150,
        )

        self.assertEqual(
            conditions["purchase_shortfall_met"],
            evidence["estimated_purchase_session_gap"] >= 15,
        )

        self.assertEqual(
            conditions["rate_drop_threshold_met"],
            evidence["purchase_rate_change_pct"] <= -35,
        )

        self.assertFalse(
            conditions["rate_drop_threshold_met"]
        )

    def test_three_complete_hypotheses(self):
        """Each hypothesis must be usable for investigation."""

        hypotheses = self.interpretation.hypotheses

        self.assertEqual(len(hypotheses), 3)

        for hypothesis in hypotheses:
            self.assertTrue(hypothesis.title.strip())
            self.assertTrue(hypothesis.explanation.strip())
            self.assertTrue(hypothesis.data_needed)
            self.assertTrue(hypothesis.validation_check.strip())

    def test_three_actionable_checks(self):
        """Next checks must specify their required inputs."""

        checks = self.interpretation.recommended_checks

        self.assertEqual(len(checks), 3)

        for check in checks:
            self.assertTrue(check.action.strip())
            self.assertTrue(check.purpose.strip())
            self.assertTrue(check.inputs_needed)

    def test_factual_review_is_pending(self):
        """Schema validation must not imply factual approval."""

        self.assertEqual(
            self.result["validation"]["factual_review_status"],
            "pending",
        )


if __name__ == "__main__":
    unittest.main()
