"""Unit tests for core modules."""
import unittest
import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from calc_visits import parse_schedule_config, calculate_visit_dates


class TestCalcVisits(unittest.TestCase):
    def setUp(self):
        self.config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'config', 'schedules', 'anc_who2016.conf'
        )

    def test_parse_config(self):
        visits = parse_schedule_config(self.config_path)
        self.assertEqual(len(visits), 4)
        self.assertEqual(visits[0]['name'], 'First contact')

    def test_calculate_dates(self):
        visits = parse_schedule_config(self.config_path)
        schedule = calculate_visit_dates('2024-01-15', visits)
        self.assertEqual(len(schedule), 4)
        self.assertEqual(schedule[0]['scheduled_date'], '2024-01-15')
        # Second visit at 20 weeks
        self.assertEqual(schedule[1]['visit_name'], 'Second contact')


if __name__ == '__main__':
    unittest.main()
