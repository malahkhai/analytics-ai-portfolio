"""Offline regression tests for the clearly labeled synthetic red-alert replay."""
import unittest
from copy import deepcopy
from io import BytesIO

from src.dashboard_presentation import severity
from src.executive_pdf import generate_pdf
from src.email_delivery import compose_sample
from src.executive_report import alert_reason, decision, short_summary
from src.interview_demo import (
    DEMO_DATE, DEMO_PURCHASING_SESSIONS, evaluate_conversion_rule,
    is_synthetic, make_synthetic_red_alert, scenario_rows,
    validate_simulated_row,
)
from src.report_filters import selectable_investigations


class TestInterviewRedAlert(unittest.TestCase):
    def setUp(self):
        self.authentic = {
            'investigation_date': DEMO_DATE,
            'scope': 'all_channels_aggregated',
            'source': 'GA4 public ecommerce sample',
            'observed_sessions': 5461,
            'baseline_sessions': 3846.0,
            'session_change_pct': 42.0,
            'observed_purchase_rate_pct': 1.67,
            'baseline_purchase_rate_pct': 1.95,
            'purchase_rate_change_pct': -14.5,
            'estimated_purchase_session_gap': 15.5,
            'alert_status': 'no_qualifying_anomaly',
            'alert_types': [],
            'has_ai_investigation': True,
            'factual_review_status': 'pending',
            'executive_summary': 'Original historical analysis: 14.5% rate decline',
            'why_no_alert': 'Did not meet the 35 percent rate-decline threshold',
            'hypotheses_json': '[]',
            'recommended_checks_json': '[]',
            'baseline_dates': ['2020-11-09','2020-11-16','2020-11-23','2020-11-30'],
        }

    def test_original_historical_data_never_mutated(self):
        original = deepcopy(self.authentic)
        demo = make_synthetic_red_alert(self.authentic)
        self.assertEqual(self.authentic, original)
        self.assertEqual(severity(self.authentic), 'yellow')
        self.assertEqual(severity(demo), 'red')
        self.assertFalse(is_synthetic(self.authentic))
        self.assertTrue(is_synthetic(demo))

    def test_synthetic_rate_and_gap_recalculate_from_purchase_sessions(self):
        row = make_synthetic_red_alert(self.authentic)
        validate_simulated_row(row)
        self.assertEqual(row['demo_purchasing_sessions'], DEMO_PURCHASING_SESSIONS)
        self.assertAlmostEqual(row['observed_purchase_rate_pct'], 1.0255, places=4)
        self.assertAlmostEqual(row['purchase_rate_change_pct'], -47.4, places=1)
        self.assertAlmostEqual(row['estimated_purchase_session_gap'], 50.5, places=1)
        self.assertEqual(row['observed_sessions'], self.authentic['observed_sessions'])
        self.assertEqual(row['baseline_sessions'], self.authentic['baseline_sessions'])

    def test_all_three_thresholds_trigger_synthetic_red_alert(self):
        checks = evaluate_conversion_rule(make_synthetic_red_alert(self.authentic))
        self.assertEqual(checks, {
            'sessions_met': True, 'rate_drop_met': True,
            'shortfall_met': True, 'alert_triggered': True,
        })

    def test_toggle_is_reversible_and_selector_keeps_one_date(self):
        green_day = dict(self.authentic)
        green_day['investigation_date'] = '2020-12-06'
        green_day['purchase_rate_change_pct'] = -4.8
        green_day['estimated_purchase_session_gap'] = 2.0
        original = [green_day, self.authentic]
        synthetic = scenario_rows(original, simulate=True)
        restored = scenario_rows(original, simulate=False)
        self.assertEqual(restored, original)
        self.assertEqual(len(selectable_investigations(synthetic)), 1)
        self.assertEqual(selectable_investigations(synthetic)[0]['investigation_date'], DEMO_DATE)
        self.assertEqual(severity(restored[1]), 'yellow')
        self.assertEqual(severity(synthetic[1]), 'red')

    def test_synthetic_summary_is_not_a_claim_of_gemini_investigation(self):
        row = make_synthetic_red_alert(self.authentic)
        summary = short_summary(row)
        self.assertIn('SIMULATION ONLY', summary)
        self.assertNotIn('14.5%', summary)
        self.assertEqual(row['analysis_origin'], 'deterministic_simulation_fixture_not_gemini')
        self.assertIn('SIMULATED alert only', alert_reason(row))
        self.assertEqual(decision(row)['owner'], 'Acquisition Manager')

    def test_email_is_marked_synthetic_and_revenue_is_not_reused(self):
        row = make_synthetic_red_alert(self.authentic)
        subject, body = compose_sample(row, short_summary(row), {
            'purchase_revenue_usd': 8472.0,
            'revenue_difference_usd': 1000.0,
        })
        self.assertIn('SYNTHETIC INTERVIEW ALERT', subject)
        self.assertIn('NOT A REAL HISTORICAL INCIDENT', body)
        self.assertIn('Gemini did not generate a new investigation', body)
        self.assertNotIn('8,472', body)
        self.assertNotIn('1,000', body)

    def test_pdf_is_marked_synthetic_and_does_not_reuse_revenue(self):
        row = make_synthetic_red_alert(self.authentic)
        document = generate_pdf(row, [row], {'purchase_revenue_usd': 8472.0})
        self.assertTrue(document.startswith(b'%PDF'))
        self.assertGreater(len(document), 3000)
        try:
            from pypdf import PdfReader
        except ImportError:
            return
        reader = PdfReader(BytesIO(document))
        self.assertGreaterEqual(len(reader.pages), 3)
        extracted = ' '.join(page.extract_text() or '' for page in reader.pages)
        self.assertIn('SYNTHETIC', extracted)
        self.assertNotIn('8,472', extracted)

    def test_guard_against_other_dates_or_unqualified_reference(self):
        wrong_day = dict(self.authentic, investigation_date='2020-12-06')
        with self.assertRaises(ValueError):
            make_synthetic_red_alert(wrong_day)
        red_day = dict(self.authentic, alert_types=['conversion_rate_drop'])
        with self.assertRaises(ValueError):
            make_synthetic_red_alert(red_day)


if __name__ == '__main__':
    unittest.main()
