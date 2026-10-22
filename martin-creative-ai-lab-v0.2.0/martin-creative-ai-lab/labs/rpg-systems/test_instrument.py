#!/usr/bin/env python3
"""Control the source assay and reject fabricated/incomplete destination observations."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('rpg_study',HERE/'run.py')
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)

class SourceStudy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text={name:(study.SNAPSHOT/path).read_text(encoding='utf-8-sig') for name,path in study.SOURCE_NAMES.items()}
        cls.levels=study.parse_tables(cls.text['thresholds'],cls.text['budgets'])
        cls.protocol,cls.expected,cls.goldens=study.make_protocol(cls.levels,cls.text['goldens'])

    def test_full_source_protocol_has_goldens_boundaries_and_partitioned_grants(self):
        self.assertEqual((len(self.levels),self.goldens,len(self.expected)),(180,9,555))
        self.assertEqual(len({case['id'] for case in self.protocol['cases']}),555)
        self.assertEqual(self.expected[0]['hp_gained'],30)
        self.assertEqual(self.expected[6]['level'],180)
        self.assertEqual(self.expected[6]['hp_gained'],2460)
        for index in range(9):
            original={key:value for key,value in self.expected[index].items() if key!='id'}
            partition={key:value for key,value in self.expected[-9+index].items() if key!='id'}
            self.assertEqual(original,partition)

    def test_historical_source_binding_mismatch_is_retained(self):
        for runtime,budgets in [('runtime','budgets'),('shipped_runtime','shipped_budgets')]:
            result=study.source_binding_assay(self.text[runtime],self.text[budgets],self.expected,9)
            self.assertEqual(result['missing_columns'],['HP','SP'])
            self.assertEqual(result['decision'],'REJECTED')
            self.assertEqual(len(result['golden_mismatches']),9)
            self.assertTrue(all(row['projected_hp']==row['projected_sp']==0 for row in result['golden_mismatches']))

    def test_exact_threshold_controls_reject_off_by_one_reference(self):
        changed=[study.reference(self.levels,case,strict=True) for case in self.protocol['cases']]
        rejected=[row['id'] for row,golden in zip(changed,self.expected) if row!=golden]
        self.assertGreaterEqual(len(rejected),179)
        self.assertTrue(all(f'boundary/{level}/+0' in rejected for level in range(2,181)))

    def test_malformed_curve_and_budget_contracts_are_rejected(self):
        threshold=self.text['thresholds'];budget=self.text['budgets']
        mutations=[
            (threshold,budget.replace('HP_Gain','HP')),
            (threshold,budget.replace('SP_Gain','SP')),
            (threshold.replace('2,262,348','2,0,348'),budget),
            (threshold.replace('2,262,348','1,262,348'),budget),
            (threshold.replace('1,0,262','1,0,263'),budget),
            (threshold,budget.replace('1,EARLY_GROWTH,8,30,12','1,EARLY_GROWTH,8,-30,12')),
            (threshold,budget.replace('1,EARLY_GROWTH,8,30,12','1,EARLY_GROWTH,8,30.5,12')),
        ]
        for xp,stats in mutations:
            with self.subTest(xp=xp[:30],budget=stats[:50]):
                with self.assertRaises(ValueError):study.parse_tables(xp,stats)

    def test_destination_cannot_omit_reorder_forge_or_retype_observations(self):
        result={'schema_version':1,'rows':copy.deepcopy(self.expected)}
        study.validate_results(result,self.expected)
        mutations=[]
        bad=copy.deepcopy(result);bad['rows'].pop();mutations.append(bad)
        bad=copy.deepcopy(result);bad['rows'][0],bad['rows'][1]=bad['rows'][1],bad['rows'][0];mutations.append(bad)
        bad=copy.deepcopy(result);bad['rows'][0]['hp_gained']=0;mutations.append(bad)
        bad=copy.deepcopy(result);bad['rows'][0]['level']=True;mutations.append(bad)
        bad=copy.deepcopy(result);bad['schema_version']=True;mutations.append(bad)
        bad=copy.deepcopy(result);bad['rows'][0]['unity_playable']=True;mutations.append(bad)
        for value in mutations:
            with self.assertRaises(ValueError):study.validate_results(value,self.expected)

    def test_changed_historical_golden_is_not_silently_rederived(self):
        changed=self.text['goldens'].replace('T001,0,1,262,2,262,1,8,30,12','T001,0,1,262,2,262,1,8,0,0')
        self.assertNotEqual(changed,self.text['goldens'])
        with self.assertRaises(ValueError):study.make_protocol(self.levels,changed)

    def test_outputs_cannot_overwrite_inputs(self):
        for path in [HERE/'run.py',study.SNAPSHOT/'RM_CORE/DATA/CORE/PLAYER_LEVEL_XP_TABLE.csv',study.DOMAIN/'global.json']:
            with self.assertRaises(ValueError):study.run(path,'definitely-no-dotnet')

if __name__=='__main__':unittest.main()
