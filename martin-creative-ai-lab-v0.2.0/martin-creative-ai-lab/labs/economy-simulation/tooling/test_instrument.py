#!/usr/bin/env python3
"""Reject source-intake and comparison rivals in owned temporary copies, never originals."""
import copy
import csv
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tooling_method',HERE/'run.py');method=importlib.util.module_from_spec(spec);spec.loader.exec_module(method)

class SourceContract(unittest.TestCase):
    def fixture(self,root):
        for name in method.SOURCES:
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((method.ROOT/name).read_bytes())
    def mutate_csv(self,p,operation):
        raw=list(csv.reader(io.StringIO(p.read_text(encoding='utf-8-sig'))));operation(raw)
        out=io.StringIO();csv.writer(out,lineterminator='\n').writerows(raw);p.write_text(out.getvalue())
    def test_actual_source_identity_is_not_activation(self):
        a,c=method.inspect_sources()
        self.assertEqual((a['item_records'],a['structurally_valid_identity_records'],len(a['quarantined_records']),a['recipe_records']), (372,370,2,21))
        self.assertEqual((a['actual_resolved_literal_references'],len(c['references'])),(81,87))
        self.assertEqual(sum(r['expected'] for r in c['references']),81)
        self.assertEqual(set(c),{'schema_version','known_ids','references'})
        self.assertTrue(method.QUARANTINE_IDS.isdisjoint(c['known_ids']))
        self.assertEqual(len(a['ambiguous_unlock_references']),4)
        self.assertFalse(a['quest_variants_byte_identical'])
        self.assertEqual(a['recipe_skill_ids_missing_in_unlock_namespace'],['20','22','23','28'])
    def test_duplicate_literal_id_is_not_first_match_resolution(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);self.fixture(r);self.mutate_csv(r/method.ITEMS,lambda raw:raw[2].__setitem__(0,raw[1][0]))
            with self.assertRaisesRegex(ValueError,'Duplicate literal'):method.inspect_sources(r)
    def test_additional_ragged_row_does_not_silently_drop_an_item(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);self.fixture(r);self.mutate_csv(r/method.ITEMS,lambda raw:raw[1].pop())
            with self.assertRaisesRegex(ValueError,'Quarantine changed'):method.inspect_sources(r)
    def test_tool_rule_cannot_be_rebased_to_consumed(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);self.fixture(r);p=r/method.CLASSES;p.write_text(p.read_text().replace('ferramenta requerida (não consumida)','ferramenta requerida (consumida)'))
            with self.assertRaisesRegex(ValueError,'nonconsumed tool'):method.inspect_sources(r)
    def test_synthetic_missing_reference_is_not_an_actual_source_failure(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);self.fixture(r);self.mutate_csv(r/method.RECIPES,lambda raw:raw[1].__setitem__(2,'UNKNOWN_ITEM_0001'))
            with self.assertRaisesRegex(ValueError,'Unresolved actual item reference'):method.inspect_sources(r)
    def test_ambiguous_unlock_is_not_silently_resolved(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);self.fixture(r);p=r/method.RECIPES;p.write_text(p.read_text().replace('SDQ-0001;SDQ-0007','SDQ-0007'))
            with self.assertRaisesRegex(ValueError,'Ambiguous unlock reference set'):method.inspect_sources(r)
    def test_deprecated_quest_cannot_become_a_grant_by_stripping_status(self):
        with tempfile.TemporaryDirectory() as t:
            r=Path(t);self.fixture(r)
            for name in (method.QUESTS,method.DIST_QUESTS):
                p=r/name;p.write_text(p.read_text().replace('[DESCONSIDERAR]',''))
            with self.assertRaisesRegex(ValueError,'Deprecated quest'):method.inspect_sources(r)
    def test_false_reordered_or_permission_bearing_csharp_results_fail(self):
        _,c=method.inspect_sources()
        good={'schema_version':1,'references':[dict(id=x['id'],item_id=x['item_id'],actual=x['expected'],expected=x['expected'],passed=True) for x in c['references']],'passed':len(c['references']),'failed':0}
        method.compare_results(c,good)
        bad=copy.deepcopy(good);bad['references'][-1]['actual']=True
        with self.assertRaisesRegex(ValueError,'False, reordered'):method.compare_results(c,bad)
        bad=copy.deepcopy(good);bad['references'][0],bad['references'][1]=bad['references'][1],bad['references'][0]
        with self.assertRaisesRegex(ValueError,'False, reordered'):method.compare_results(c,bad)
        bad=copy.deepcopy(good);bad['unlocks']=['SDQ-0007']
        with self.assertRaisesRegex(ValueError,'fields/schema'):method.compare_results(c,bad)

if __name__=='__main__':unittest.main()
