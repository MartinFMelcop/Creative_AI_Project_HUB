"""Reject source mutations and fabricated measured reports using owned copies."""
import importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('availability_assay',Path(__file__).with_name('run.py'));run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)
class AssayTests(unittest.TestCase):
 def test_current_literal_cases(self):
  value,rows,phases=run.cases();self.assertEqual((len(rows),len(phases),len(value['cases'])),(27,5,135));self.assertEqual(value,json.loads(Path(__file__).with_name('source-cases.json').read_text()))
 def mutation(self,key,change):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary)
   for name in ('schedules','phases'):
    p=root/run.PATHS[name];p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(run.ROOT/run.PATHS[name],p)
   p=root/run.PATHS[key];p.write_text(change(p.read_text()))
   with self.assertRaises(ValueError):run.cases(root)
 def test_duplicate_npc(self):self.mutation('schedules',lambda s:s.replace('NPC-0002','NPC-0001',1))
 def test_unknown_phase(self):self.mutation('schedules',lambda s:s.replace('0|1|2|3|4','0|1|2|3|5',1))
 def test_duplicate_phase(self):self.mutation('schedules',lambda s:s.replace('0|1|2|3|4','0|1|2|3|3',1))
 def test_unknown_time_identity(self):self.mutation('phases',lambda s:s.replace('PH_DAWN,4','PH_UNKNOWN,4',1))
 def test_empty_phase(self):self.mutation('schedules',lambda s:s.replace('0|1|2|3|4','',1))
 def test_bad_width(self):self.mutation('schedules',lambda s:s.replace('IdNPC,Nome','IdNPC,Extra,Nome',1))
 def test_changed_phase_order(self):self.mutation('phases',lambda s:s.replace('PH_DAWN,4','PH_DAWN,5',1))
 def report(self):
  f,_,_=run.cases();return f,{'schema':1,'case_count':135,'passed':135,'failed':0,'results':[{'id':c['id'],'allowed':c['expected'],'expected':c['expected'],'passed':True} for c in f['cases']]}
 def test_positive_report(self):
  f,r=self.report();self.assertEqual(run.verify(r,f),135)
 def test_false_allowed_report(self):
  f,r=self.report();r['results'][0]['allowed']=not r['results'][0]['allowed']
  with self.assertRaises(ValueError):run.verify(r,f)
 def test_boolean_schema(self):
  f,r=self.report();r['schema']=True
  with self.assertRaises(ValueError):run.verify(r,f)
 def test_truncated_report(self):
  f,r=self.report();r['results'].pop()
  with self.assertRaises(ValueError):run.verify(r,f)
 def test_false_totals(self):
  f,r=self.report();r['passed']=0
  with self.assertRaises(ValueError):run.verify(r,f)
 def test_reordered_report(self):
  f,r=self.report();r['results'][0],r['results'][1]=r['results'][1],r['results'][0]
  with self.assertRaises(ValueError):run.verify(r,f)
 def test_negative_models(self):
  r=run.counterexamples();self.assertEqual((r['mask_presence_policy_errors'],r['mask_completion_policy_errors']),(1,2))
 def test_conflicts_remain_explicit(self):
  r=run.inspect();self.assertEqual(len(r['retained_ambiguities']),4);self.assertTrue(r['observed_position'].startswith('UNKNOWN'));self.assertIn('NPC-0006',r['retained_ambiguities'][1]['npcs'])
if __name__=='__main__':unittest.main()
