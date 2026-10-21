#!/usr/bin/env python3
"""Fail closed when mapped-input evidence loses coverage or source identity."""
import copy
import hashlib
import unittest
from verify_gamepad import EXPECTED, ROOT, validate

class ReportChecks(unittest.TestCase):
    def setUp(self):
        self.row = {'checks': {'passed': EXPECTED, 'failed': 0},
                    'labels': [str(i) for i in range(EXPECTED)], 'physical_controller': False,
                    'journeys': [{'role': role, 'game': {'mode': 'won'}, 'return_gate': {'raised': [True, True]}}
                                 for role in ('Guardian', 'Duelist')],
                    'consumer_hashes': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                                        for name in ('arena.gd', 'gamepad.gd', 'tests/gamepad_checks.gd', 'tests/gamepad_driver.gd')}}

    def test_complete(self):
        validate(self.row)

    def test_reject_incomplete_and_misleading_reports(self):
        variants = []
        for key, value in [('physical_controller', True), ('labels', ['same'] * EXPECTED),
                           ('checks', {'passed': EXPECTED - 1, 'failed': 0}),
                           ('checks', {'passed': EXPECTED, 'failed': 1}), ('journeys', [])]:
            row = copy.deepcopy(self.row)
            row[key] = value
            variants.append(row)
        for mutation in ('loss', 'catch', 'hash', 'missing_identity'):
            row = copy.deepcopy(self.row)
            if mutation == 'loss': row['journeys'][1]['game']['mode'] = 'lost'
            if mutation == 'catch': row['journeys'][0]['return_gate']['raised'][1] = False
            if mutation == 'hash': row['consumer_hashes']['gamepad.gd'] = '0' * 64
            if mutation == 'missing_identity': row['consumer_hashes'].pop('arena.gd')
            variants.append(row)
        for row in variants:
            with self.subTest(row=row), self.assertRaises(ValueError):
                validate(row)

if __name__ == '__main__':
    unittest.main()
