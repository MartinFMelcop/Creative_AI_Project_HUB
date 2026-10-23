import importlib.util
from pathlib import Path
import tempfile
import unittest
import wave
spec=importlib.util.spec_from_file_location('audio',Path(__file__).with_name('run.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class InstrumentTests(unittest.TestCase):
 def test_silence_rejected(self):
  with self.assertRaisesRegex(ValueError,'silence'):m.signal_checks([0]*10,10)
 def test_clipping_rejected(self):
  with self.assertRaisesRegex(ValueError,'clipping'):m.signal_checks([0,32767,0],3)
 def test_endpoint_rejected(self):
  with self.assertRaisesRegex(ValueError,'Endpoint'):m.signal_checks([0,100,20],3)
 def test_length_rejected(self):
  with self.assertRaisesRegex(ValueError,'count'):m.signal_checks([0,100,0],4)
 def test_clean_signal(self):self.assertEqual(m.signal_checks([0,-100,100,0],4)['peak_integer'],100)
 def test_stereo_format_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'stereo.wav'
   with wave.open(str(p),'wb') as w:w.setparams((2,2,44100,0,'NONE','not compressed'));w.writeframes(b'\0'*16)
   with self.assertRaisesRegex(ValueError,'mono16'):m.pcm(p)
 def test_empty_pcm_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'empty.wav'
   with wave.open(str(p),'wb') as w:w.setparams((1,2,44100,0,'NONE','not compressed'));w.writeframes(b'')
   with self.assertRaisesRegex(ValueError,'length'):m.pcm(p)
 def test_output_cannot_touch_sources(self):
  with self.assertRaisesRegex(ValueError,'outside'):m.run(m.ROOT/'forbidden.json')
if __name__=='__main__':unittest.main()
