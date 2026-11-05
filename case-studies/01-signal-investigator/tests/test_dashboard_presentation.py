"""Offline tests of deterministic executive dashboard status logic."""
import unittest

from src.dashboard_presentation import (
    daily_brief, fallback_spec, format_date, is_alert, is_watch, severity,
    status_label, timeline_icon, timeline_nav_html,
)


class TestDashboardPresentation(unittest.TestCase):
    def setUp(self):
        self.row = {
            "investigation_date": "2020-12-07",
            "scope": "all_channels_aggregated",
            "observed_sessions": 5461,
            "session_change_pct": 42.0,
            "observed_purchase_rate_pct": 1.67,
            "purchase_rate_change_pct": -14.5,
            "estimated_purchase_session_gap": 15.5,
            "alert_status": "no_qualifying_anomaly",
            "alert_types": [],
            "has_ai_investigation": False,
        }

    def test_december_seven_is_yellow_not_red(self):
        self.assertTrue(is_watch(self.row))
        self.assertFalse(is_alert(self.row))
        self.assertEqual(severity(self.row), "yellow")
        self.assertIn("not an alert", status_label(self.row))
        self.assertEqual(timeline_icon(self.row), "🟡")

    def test_normal_day_is_green(self):
        self.row["purchase_rate_change_pct"] = -4.8
        self.row["estimated_purchase_session_gap"] = 2.0
        self.assertEqual(severity(self.row), "green")
        self.assertFalse(is_watch(self.row))

    def test_real_detector_alert_is_red(self):
        self.row["alert_types"] = ["conversion_rate_drop"]
        self.assertTrue(is_alert(self.row))
        self.assertFalse(is_watch(self.row))
        self.assertEqual(severity(self.row), "red")

    def test_unknown_status_is_never_green(self):
        self.row["alert_status"] = "insufficient_history"
        self.assertEqual(severity(self.row), "unknown")
        self.assertEqual(timeline_icon(self.row), "⚪")

    def test_watch_requires_minimum_sessions(self):
        self.row["observed_sessions"] = 149
        self.assertEqual(severity(self.row), "green")

    def test_watch_requires_shortfall(self):
        self.row["estimated_purchase_session_gap"] = 14.9
        self.assertEqual(severity(self.row), "green")

    def test_brief_is_transparent_about_watch(self):
        brief = daily_brief(self.row)
        self.assertIn("5,461 sessions", brief)
        self.assertIn("Watchlist, not a triggered anomaly", brief)
        self.assertNotIn("root cause confirmed", brief)

    def test_no_ai_report_has_no_ai_sections(self):
        self.assertEqual(fallback_spec(self.row)["sections"], [])

    def test_date_format(self):
        self.assertEqual(format_date("2020-12-07"), "07 Dec")

    def test_timeline_navigation_is_accessible_and_selects_day(self):
        html = timeline_nav_html([self.row], "2020-12-07")
        self.assertIn("?date=2020-12-07", html)
        self.assertIn('aria-current="date"', html)
        self.assertIn("si-day--yellow", html)
        self.assertIn(">DEC<", html)
        self.assertIn(">07<", html)
        self.assertIn(">Mon<", html)


if __name__ == "__main__":
    unittest.main()
