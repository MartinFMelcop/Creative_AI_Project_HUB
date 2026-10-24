#!/usr/bin/env python3
"""Reject substantive source-contract and evaluator errors without editing originals."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('reputation_method', HERE/'run.py')
method = importlib.util.module_from_spec(spec)
spec.loader.exec_module(method)


class SourceBoundMethod(unittest.TestCase):
    def fixture(self, root):
        for name in method.SOURCES:
            target = root/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((method.ROOT/name).read_bytes())

    def test_actual_table_and_semantic_boundaries(self):
        result = method.source_assay()
        self.assertEqual(result['typed_source_effect_rows'], 420)
        cases = method.vectors(result['config'])['cases']
        values = {(r['current'], r['delta']): r['expected'] for r in cases if r['operation'] == 'add'}
        self.assertEqual([values[-1, 1], values[-1, 2], values[1, -1], values[1, -2]], [-1, 1, 1, -1])
        self.assertEqual(method.model_set(0, result['config']), 1)
        self.assertEqual(len(cases), len(method.SETS) + 6*len(method.DELTAS))

    def test_changed_both_helper_thresholds_is_not_rebased(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            for name in (method.DEV, method.DIST):
                p = root/name
                p.write_text(p.read_text().replace('def self.crossing_threshold_abs; 2; end', 'def self.crossing_threshold_abs; 1; end'))
            with self.assertRaisesRegex(ValueError, 'configuration changed'):
                method.source_assay(root)

    def test_nonempty_hook_does_not_retain_empty_claim(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            for name in (method.DEV, method.DIST):
                p = root/name
                p.write_text(p.read_text().replace('    []\n', '    [:new_effect]\n'))
            with self.assertRaisesRegex(ValueError, 'no longer empty'):
                method.source_assay(root)

    def test_both_tables_zero_domain_mutant_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.fixture(root)
            for name in (method.CORE_TABLE, method.DIST_TABLE):
                p = root/name
                p.write_text(p.read_text().replace('VILA_ROSE,-3,SHOP,shop_buy_mult', 'VILA_ROSE,0,SHOP,shop_buy_mult', 1))
            with self.assertRaisesRegex(ValueError, 'identity/domain'):
                method.source_assay(root)

    def test_false_csharp_result_and_reordering_are_detected(self):
        vectors = method.vectors({'clamp_min': -3, 'clamp_max': 3, 'crossing_threshold_abs': 2})
        result = {'schema_version': 1, 'cases': [{'id': row['id'], 'actual': row['expected'], 'expected': row['expected'], 'passed': True} for row in vectors['cases']], 'passed': len(vectors['cases']), 'failed': 0}
        method.compare_results(vectors, result)
        wrong = copy.deepcopy(result)
        wrong['cases'][0]['actual'] = 0
        with self.assertRaisesRegex(ValueError, 'False, reordered'):
            method.compare_results(vectors, wrong)
        wrong = copy.deepcopy(result)
        wrong['cases'][0], wrong['cases'][1] = wrong['cases'][1], wrong['cases'][0]
        with self.assertRaisesRegex(ValueError, 'False, reordered'):
            method.compare_results(vectors, wrong)


if __name__ == '__main__':
    unittest.main()
