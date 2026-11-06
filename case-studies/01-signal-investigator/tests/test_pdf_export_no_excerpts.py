"""Keep the paginated PDF complete and readable as Gemini summaries evolve."""
from io import BytesIO
import unittest

from pypdf import PdfReader
from src.executive_pdf import generate_pdf
from tests.test_executive_report import example_row


class PdfBriefNoExcerptTests(unittest.TestCase):
    def report(self, kind):
        row = example_row()
        row['recommended_checks_json'] = ('[{"action":"Segment sessions and purchase rates by acquisition channel",'
            '"purpose":"Determine whether the 42.0% traffic increase and rate dilution stemmed from '
            'a specific channel or reflect a site-wide trend. Compare source, medium and devices carefully.",'
            '"inputs_needed":["sessions","channel","device"]}]')
        row['executive_summary'] = (
            'On 2020-12-07, observed sessions rose 42.0% to 5,461 relative to the baseline of 3,846. '
            'Purchase conversion declined against historical behavior. '
            'The financial comparison is crucial for assessing business relevance. '
            'Investigate channels, devices, funnel health, and inventory before drawing conclusions. '
        ) * 5
        row.update({
            'purchase_revenue_usd': 8472.0, 'baseline_revenue_usd': 6918.0,
            'revenue_difference_usd': 1554.0, 'revenue_change_pct': 22.5,
            'revenue_evidence_type': 'recorded', 'purchase_events_with_revenue': 110,
        })
        if kind == 'red':
            row.update({
                'observed_purchase_rate_pct': 1.03, 'purchase_rate_change_pct': -47.4,
                'estimated_purchase_session_gap': 50.5, 'alert_status': 'alert',
                'alert_types': ['session_purchase_rate_drop'],
                'purchase_revenue_usd': 5213.54, 'revenue_difference_usd': -1704.46,
                'revenue_change_pct': -24.6, 'revenue_evidence_type': 'modeled',
                'purchase_events_with_revenue': 60,
            })
        pdf = PdfReader(BytesIO(generate_pdf(row, [row])))
        return pdf, ' '.join(' '.join(page.extract_text() or '' for page in pdf.pages).split())

    def test_historical_yellow_summary_is_complete_no_excerpt(self):
        pdf, text = self.report('yellow')
        self.assertGreaterEqual(len(pdf.pages), 3)
        self.assertNotIn('[excerpt]', text.lower())
        self.assertIn('Recorded revenue was $8,472.00', text)
        self.assertIn('$+1,554.00', text)
        self.assertIn('recommended next step', text.lower())
        self.assertEqual(text.count('Investigate channels, devices, funnel health, and inventory before drawing conclusions.'), 5)
        self.assertIn('Page 1 /', text)

    def test_modeled_red_is_not_reported_as_observed_revenue(self):
        pdf, text = self.report('red')
        self.assertGreaterEqual(len(pdf.pages), 3)
        self.assertNotIn('[excerpt]', text.lower())
        self.assertIn('Modeled revenue was $5,213.54', text)
        self.assertIn('$-1,704.46', text)
        self.assertIn('not verified lost revenue', text)


if __name__ == '__main__':
    unittest.main()
