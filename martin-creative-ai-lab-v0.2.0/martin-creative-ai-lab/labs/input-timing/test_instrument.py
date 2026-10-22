import copy
import importlib.util
import json
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('input_study',Path(__file__).with_name('run.py'));study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
class Contract(unittest.TestCase):
 def setUp(self):self.data=json.loads((study.ROOT/'evidence/input-timing/results.json').read_text())
 def test_actual_results(self):study.validate(self.data['native'],self.data['destination'])
 def test_false_native_counts(self):
  for key,value in [('passed',True),('passed',0),('failed',False),('failed',1),('schema_version',True)]:
   data=copy.deepcopy(self.data['native']);data[key]=value
   with self.assertRaises(ValueError):study.validate(data,self.data['destination'])
 def test_native_identities(self):
  for controls in [[],['same']*self.data['native']['passed']]:
   data=copy.deepcopy(self.data['native']);data['controls']=controls
   with self.assertRaises(ValueError):study.validate(data,self.data['destination'])
 def test_missing_whole_outcomes(self):
  for name in ['completed','same_boundary_hit','missing_input']:
   d=copy.deepcopy(self.data['destination']);del d[name]
   with self.assertRaises(ValueError):study.validate(self.data['native'],d)
 def test_false_consequences(self):
  for name,key,value in [('grounded_not_goal','won',True),('completed','paid',2),('release','progress_ms',500),('same_boundary_hit','grounded',True),('missing_input','paused',False),('held_resume','need_neutral',False),('optional_grounding','paid',1),('completed','integrity',True)]:
   d=copy.deepcopy(self.data['destination']);d[name][key]=value
   with self.assertRaises(ValueError):study.validate(self.data['native'],d)
 def test_all_maintained_outputs_protected(self):
  for name in ['brains/SCIENTIFIC_BRAIN.md','docs/STATE.md','north-star/csharp/Interaction/Program.cs']:
   with self.assertRaises(ValueError):study.run(study.ROOT/name,'missing')
if __name__=='__main__':unittest.main()
