"""Verify explicit illustrative role routing, not fake human assignments."""
import unittest

from src.executive_report import suggested_owner_role


class TestRoleSuggestions(unittest.TestCase):
    def test_inventory(self):
        self.assertEqual(suggested_owner_role('Investigate product stockouts and inventory'), 'Inventory & Sales Manager')

    def test_traffic_dilution(self):
        self.assertEqual(suggested_owner_role('Traffic dilution by acquisition channel'), 'Acquisition Manager')

    def test_checkout(self):
        self.assertEqual(suggested_owner_role('Check payment friction and checkout errors'), 'Ecommerce Operations Manager')

    def test_attribution(self):
        self.assertEqual(suggested_owner_role('Audit GA4 attribution and tracking'), 'Digital Analytics Lead')

    def test_nothing_specific_defaults_to_analytics(self):
        self.assertEqual(suggested_owner_role('Investigate unexplained pattern'), 'Digital Analytics Lead')


if __name__ == '__main__':
    unittest.main()
