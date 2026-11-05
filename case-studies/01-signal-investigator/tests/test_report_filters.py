"""Investigations dropdown contains only true watchlist or detector alerts."""
import unittest

from src.report_filters import (
    reporting_windows, rows_for_window, selectable_investigations,
    investigation_option,
)


def row(day, status='no_qualifying_anomaly', rate=0, gap=0, alerts=None):
    return {
        'investigation_date': day,
        'alert_status': status,
        'alert_types': alerts or [],
        'observed_sessions': 500,
        'purchase_rate_change_pct': rate,
        'estimated_purchase_session_gap': gap,
    }


class TestReportFilters(unittest.TestCase):
    def setUp(self):
        self.rows = [
            row('2020-12-05'),
            row('2020-12-06'),
            row('2020-12-07', rate=-14.5, gap=15.5),
        ]

    def test_only_december_seven_selectable(self):
        available = selectable_investigations(self.rows)
        self.assertEqual([r['investigation_date'] for r in available], ['2020-12-07'])
        self.assertIn('Watch', investigation_option(available[0]))

    def test_true_alert_selected_and_labeled(self):
        incident = row('2020-12-04', status='qualifying_anomaly', alerts=['conversion_rate_drop'])
        choices = selectable_investigations([*self.rows, incident])
        self.assertEqual(len(choices), 2)
        self.assertIn('Alert', investigation_option(incident))

    def test_never_label_normal_as_event(self):
        self.assertEqual(selectable_investigations([row('2020-12-03')]), [])

    def test_week_window_with_no_incident(self):
        windows = reporting_windows(self.rows)
        previous_week = next(w for w in windows if w['key'] == '2020-11-30')
        self.assertEqual(selectable_investigations(rows_for_window(self.rows, previous_week)), [])

    def test_all_window_contains_all_rows(self):
        windows = reporting_windows(self.rows)
        self.assertEqual(len(rows_for_window(self.rows, windows[0])), 3)
        self.assertEqual(windows[0]['key'], 'all')

    def test_bad_date_rejected(self):
        with self.assertRaises(ValueError):
            reporting_windows([{'investigation_date': '2020-99-99'}])


if __name__ == '__main__':
    unittest.main()
