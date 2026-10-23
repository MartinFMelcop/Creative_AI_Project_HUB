"""Fault controls for source intake; no protected source mutation."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('status_instrument', HERE / 'run.py')
instrument = importlib.util.module_from_spec(spec)
spec.loader.exec_module(instrument)


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        for rel in instrument.verify():
            target = self.source / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(instrument.SOURCE / rel, target)

    def tearDown(self):
        self.temp.cleanup()

    def test_tampered_staged_payload_rejected(self):
        staged, _, lock = instrument.stage(self.root / 'evidence', self.source)
        path = staged / 'DATA/QA/TEST_COMBAT_HIT.csv'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'staged vector'):
            instrument.verify_staged(staged, lock)
        shutil.copyfile(self.source / 'RM_QA/DATA/QA/TEST_COMBAT_HIT.csv', path)
        runner = staged / 'runner.py'
        runner.write_bytes(runner.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'staged runner'):
            instrument.verify_staged(staged, lock)

    def test_49_duplicate_passing_results_rejected(self):
        _, vectors, _ = instrument.stage(self.root / 'evidence', self.source)
        first = vectors[0]
        expected = next(v for k, v in first['row'].items() if k.startswith('Expected_'))
        record = dict(component=first['component'], id=first['row']['TestID'], expected=expected, actual=expected, passed=True)
        with self.assertRaisesRegex(AssertionError, 'identity'):
            instrument.verify_results(vectors, [record] * 49)
        legacy = dict(Component=first['component'], TestID=first['row']['TestID'], Expected=expected, Got=expected, PASS='TRUE')
        with self.assertRaisesRegex(AssertionError, 'identity'):
            instrument.verify_results(vectors, [legacy] * 49, historical=True)

    def test_changed_result_expectation_rejected(self):
        _, vectors, _ = instrument.stage(self.root / 'evidence', self.source)
        records = [dict(component=v['component'], id=v['row']['TestID'],
                        expected=next(x for k,x in v['row'].items() if k.startswith('Expected_')),
                        actual=next(x for k,x in v['row'].items() if k.startswith('Expected_')), passed=True) for v in vectors]
        instrument.verify_results(vectors, records)
        records[-1]['expected'] = float(records[-1]['expected']) + 1
        with self.assertRaisesRegex(AssertionError, 'expectation'):
            instrument.verify_results(vectors, records)

    def test_fabricated_actual_passing_flag_rejected_in_both_formats(self):
        vector = {'component':'HIT', 'row':{'TestID':'sample', 'Expected_HitChance':'0.45'}}
        current = dict(component='HIT', id='sample', expected=.45, actual=999999, passed=True)
        legacy = dict(Component='HIT', TestID='sample', Expected='.45', Got='999999', PASS='TRUE')
        for record, historical in ((current, False), (legacy, True)):
            with self.assertRaisesRegex(AssertionError, 'expectation'):
                instrument.verify_results([vector], [record], historical=historical)

    def test_nonfinite_source_and_report_rejected(self):
        for source, declared, actual in (('nan', .45, .45), ('.45', float('inf'), .45), ('.45', .45, float('nan'))):
            vector = {'component':'HIT', 'row':{'TestID':'sample', 'Expected_HitChance':source}}
            record = dict(component='HIT', id='sample', expected=declared, actual=actual, passed=True)
            with self.assertRaisesRegex(AssertionError, 'Nonfinite'):
                instrument.verify_results([vector], [record])

    def test_component_specific_actual_tolerance(self):
        for component, error, accepted in (('RAW', .000009, True), ('RAW', .00002, False), ('HIT', .0000009, True), ('HIT', .000002, False), ('DOT', .00000001, False)):
            vector = {'component':component, 'row':{'TestID':'sample', 'Expected_Value':'1'}}
            record = dict(component=component, id='sample', expected=1, actual=1+error, passed=True)
            if accepted:
                instrument.verify_results([vector], [record])
            else:
                with self.assertRaises(AssertionError):
                    instrument.verify_results([vector], [record])

    def test_workspace_evidence_rejected(self):
        with self.assertRaisesRegex(ValueError, 'outside'):
            instrument.validate_output(instrument.ROOT / 'work/status')

    def test_external_evidence_allowed(self):
        self.assertEqual(instrument.validate_output(self.root / 'evidence'), self.root / 'evidence')

    def test_explicit_configuration_selection(self):
        self.assertIn('/Release/', str(instrument.consumer_path('Release')))
        self.assertIn('/Debug/', str(instrument.consumer_path('Debug')))
        with self.assertRaises(ValueError):
            instrument.consumer_path('../escape')

    def test_executable_resolves_path(self):
        self.assertEqual(instrument.resolve_dotnet(sys.executable), Path(sys.executable).resolve())
        self.assertTrue(instrument.resolve_dotnet('python3').is_file())
        with self.assertRaisesRegex(ValueError, 'not found'):
            instrument.resolve_dotnet('nonexistent-combat-dotnet')

    def test_exact_intake_has_nine_components_and_49_rows(self):
        _, rows, _ = instrument.stage(self.root / 'evidence', self.source)
        self.assertEqual(len(rows), 49)
        self.assertEqual({r['component'] for r in rows}, set(instrument.COMPONENTS))

    def test_missing_vector_rejected_even_though_historical_runner_skips_it(self):
        (self.source / 'RM_QA/DATA/QA/TEST_COMBAT_HIT.csv').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing or changed'):
            instrument.verify(self.source)

    def test_changed_expected_vector_rejected(self):
        path = self.source / 'RM_QA/DATA/QA/TEST_COMBAT_DOT.csv'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'Missing or changed'):
            instrument.verify(self.source)

    def test_changed_runner_rejected(self):
        path = self.source / instrument.RUNNER
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'Missing or changed'):
            instrument.verify(self.source)

    def test_variant_identity_is_exact(self):
        dev = self.source / 'RM_ACT1/DATA/DEV/RGSS/RM_COMBAT_RUNTIME.rb'
        dist = self.source / 'RM_DIST/RMXP_BASE/ScriptsCustom/RM_COMBAT_RUNTIME.rb'
        self.assertEqual(dev.read_bytes(), dist.read_bytes())

    def test_false_invalid_domain_equivalence_rejected(self):
        class FalseEquivalent:
            @staticmethod
            def hit_chance(*_): return .95
        with self.assertRaisesRegex(AssertionError, 'discrepancy'):
            instrument.ratio_distinction(FalseEquivalent)

    def test_reviewed_surrogate_difference_and_half_rounding(self):
        path = self.source / instrument.RUNNER
        spec = importlib.util.spec_from_file_location('intake_test_surrogate', path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        self.assertFalse(instrument.ratio_distinction(module)['equivalent'])
        self.assertEqual([module.ruby_round(x) for x in (2.5, -2.5)], [3, -3])


if __name__ == '__main__':
    unittest.main()
