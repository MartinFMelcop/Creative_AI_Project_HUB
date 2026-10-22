import copy
import json
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location('narrative_instrument',Path(__file__).with_name('run.py'))
lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)
def sources():return {k:(lab.ROOT/v).read_text() for k,v in lab.SOURCE_NAMES.items()}

class NarrativeInstrumentTests(unittest.TestCase):
    def test_actual_source_bindings_keep_variants_distinct(self):
        result=lab.source_assay(sources())
        self.assertEqual(result['quest_rows_per_copy'],73)
        self.assertTrue(result['bindings']['dev_has_trigger_progress'])
        self.assertTrue(result['bindings']['dist_lacks_trigger_progress'])
        self.assertIn('no RMXP execution',result['scope'])
    def test_p04_refusal_must_precede_new_permission(self):
        texts=sources();texts['p04_story']=texts['p04_story'].replace('“No.”','“Yes.”')
        with self.assertRaises(ValueError):lab.source_assay(texts)
    def test_p04_limited_permission_cannot_disappear(self):
        texts=sources();texts['p04_story']=texts['p04_story'].replace('And he comes up before any box.','Anything goes.')
        with self.assertRaises(ValueError):lab.source_assay(texts)
    def test_legacy_variant_collapse_refused(self):
        texts=sources();texts['quest_dist']=texts['quest_dev']
        with self.assertRaises(ValueError):lab.source_assay(texts)
    def test_legacy_table_schema_and_typed_mutations_refused(self):
        for old,new in [('StepIndex','StepNumber'),(',Talk,',',Unknown,'),(',1,S1,',',0,S1,')]:
            texts=sources();texts['steps_dev']=texts['steps_dev'].replace(old,new)
            with self.assertRaises(ValueError):lab.source_assay(texts)
    def test_manual_completion_limit_cannot_disappear(self):
        texts=sources();texts['quest_dev']=texts['quest_dev'].replace('RM_QuestState.complete!(qid)','nothing')
        with self.assertRaises(ValueError):lab.source_assay(texts)
    def test_p10_fresh_consent_and_promise_limits_cannot_disappear(self):
        for old in ['His noon answer does not supply consent','A signature has set the deadline; no return has been observed.']:
            texts=sources();texts['p10_request']=texts['p10_request'].replace(old,'changed')
            with self.assertRaises(ValueError):lab.source_assay(texts)
    def test_native_missing_false_or_boolean_counts_refused(self):
        good={'schema_version':1,'checks':{'passed':1,'failed':0},'controls':['actual control']}
        lab.validate_native(good)
        for row in [{'schema_version':True,'checks':good['checks']},{'schema_version':1,'checks':{'passed':True,'failed':0}},{'schema_version':1,'checks':{'passed':1,'failed':False}},{'schema_version':1,'checks':{'passed':0,'failed':0}},{'schema_version':1,'checks':{'passed':1,'failed':1}}]:
            with self.assertRaises(ValueError):lab.validate_native(row)
    def test_actual_published_destination_negative_controls(self):
        # Actual executed output is the fixture; mutations contest the report contract.
        artifact=lab.ROOT/'evidence/narrative-continuity/results.json'
        valid=json.loads(artifact.read_text())['destination'];lab.validate_demo(valid)
        mutations=[('guided_dusk','crates',5),('solo_delivery','term','dusk'),
                   ('failed_delivery','guide_location','local'),('deadline_not_return','returned',True),
                   ('stale_proposal','revision',True)]
        for name,key,value in mutations:
            altered=copy.deepcopy(valid);row=next(j for j in altered['journeys'] if j['name']==name)
            row['final'][key]=value;row['observations'][-1]['after'][key]=value
            with self.assertRaises(ValueError):lab.validate_demo(altered)
    def test_missing_trace_and_rejection_claims_refused(self):
        valid=json.loads((lab.ROOT/'evidence/narrative-continuity/results.json').read_text())['destination']
        for action in ['remove_journey','remove_state','fake_rejection','erase_receipt']:
            altered=copy.deepcopy(valid)
            if action=='remove_journey':altered['journeys'].pop()
            if action=='remove_state':del altered['journeys'][0]['final']['guide_location']
            if action=='fake_rejection':altered['journeys'][0]['observations'][1]['accepted']=True
            if action=='erase_receipt':altered['journeys'][1]['observations'][-1]['after']['receipts']=[]
            with self.assertRaises(ValueError):lab.validate_demo(altered)
    def test_native_control_identities_required(self):
        for row in [{'schema_version':1,'checks':{'passed':1,'failed':0}},
                    {'schema_version':1,'checks':{'passed':2,'failed':0},'controls':['same','same']}]:
            with self.assertRaises(ValueError):lab.validate_native(row)
    def test_output_guard_preserves_all_maintained_sources(self):
        for name in ['brains/SCIENTIFIC_BRAIN.md','references/preserved.csv','docs/STATE.md','north-star/csharp/Narrative/Program.cs']:
            with self.assertRaises(ValueError):lab.run(lab.ROOT/name,dotnet='missing')

if __name__=='__main__':unittest.main()
