
"""Offline tests for Gemini's GA4 diagnostic tool."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import ai_tool_agent


class TestGA4DiagnosticTool(unittest.TestCase):

    def setUp(self):
        # Create a temporary evidence file.
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.path = Path(self.temp_dir.name) / "diagnostics.json"

        self.report = {
            "source": "GA4 test fixture",
            "evaluations": [
                {
                    "date": "2020-12-07",
                    "scope": "all_channels_aggregated",
                    "observed_sessions": 5461,
                    "purchase_rate_change_pct": -14.5,
                    "estimated_purchase_session_gap": 15.5,
                    "status": "no_qualifying_anomaly",
                    "alert_types": [],
                }
            ],
        }

        self.save_fixture()

        # Make the tool read our test data.
        patcher = patch.object(
            ai_tool_agent,
            "DIAGNOSTICS",
            self.path,
        )

        patcher.start()
        self.addCleanup(patcher.stop)

        ai_tool_agent.TOOL_CALLS.clear()

    def save_fixture(self):
        self.path.write_text(
            json.dumps(self.report),
            encoding="utf-8",
        )

    def test_valid_date_returns_evidence(self):
        result = ai_tool_agent.get_ga4_diagnostic(
            "2020-12-07"
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(
            result["evidence"]["observed_sessions"],
            5461,
        )
        self.assertEqual(
            ai_tool_agent.TOOL_CALLS,
            ["2020-12-07"],
        )

    def test_alert_conditions_are_correct(self):
        result = ai_tool_agent.get_ga4_diagnostic(
            "2020-12-07"
        )

        rule = result["conversion_alert_rule"]

        self.assertTrue(
            rule["conditions"]["sessions_met"]
        )
        self.assertTrue(
            rule["conditions"]["shortfall_met"]
        )
        self.assertFalse(
            rule["conditions"]["rate_drop_met"]
        )
        self.assertFalse(rule["alert_triggered"])

    def test_invalid_date_format(self):
        result = ai_tool_agent.get_ga4_diagnostic(
            "December 7, 2020"
        )

        self.assertEqual(
            result["status"],
            "invalid_date",
        )

    def test_unavailable_date(self):
        result = ai_tool_agent.get_ga4_diagnostic(
            "2020-12-06"
        )

        self.assertEqual(
            result["status"],
            "not_found",
        )

    def test_all_conditions_trigger_alert(self):
        # Change the temporary fixture to a known
        # qualifying conversion-rate decline.
        evidence = self.report["evaluations"][0]

        evidence["observed_sessions"] = 1000
        evidence["purchase_rate_change_pct"] = -50.0
        evidence["estimated_purchase_session_gap"] = 30.0

        self.save_fixture()

        result = ai_tool_agent.get_ga4_diagnostic(
            "2020-12-07"
        )

        self.assertTrue(
            result["conversion_alert_rule"]["alert_triggered"]
        )


if __name__ == "__main__":
    unittest.main()
