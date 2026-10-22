import binascii
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
spec=importlib.util.spec_from_file_location('visual',Path(__file__).with_name('run.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def chunk(kind,body):return struct.pack('>I',len(body))+kind+body+struct.pack('>I',binascii.crc32(kind+body)&0xffffffff)
def png(raw):return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,len(raw),8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(raw)))+chunk(b'IEND',b'')
class InstrumentTests(unittest.TestCase):
 def decode(self,data):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a.png';p.write_bytes(data);return m.png_alpha(p)
 def test_all_five_png_filters(self):
  # One pixel/row; raw reconstructed RGBA values are [10,20,30,40] throughout.
  rows=[bytes([0,10,20,30,40]),bytes([1,10,20,30,40]),bytes([2,0,0,0,0]),bytes([3,5,10,15,20]),bytes([4,0,0,0,0])]
  self.assertEqual(self.decode(png(rows)),(1,5,[bytes([40])]*5))
 def test_crc_corruption_rejected(self):
  data=bytearray(png([bytes([0,1,2,3,4])]));data[-1]^=1
  with self.assertRaisesRegex(ValueError,'CRC'):self.decode(data)
 def test_trailing_bytes_rejected(self):
  with self.assertRaisesRegex(ValueError,'Incomplete'):self.decode(png([bytes([0,1,2,3,4])])+b'x')
 def test_filter_corruption_rejected(self):
  with self.assertRaisesRegex(ValueError,'filter'):self.decode(png([bytes([5,1,2,3,4])]))
 def test_empty_frame_rejected(self):
  with self.assertRaisesRegex(ValueError,'Empty'):m.derive(16,16,[bytes(16)]*16)
 def test_registration_both_mirrors(self):
  for scale in [.331658,.506024,.5,1,2]:
   for flipped in [True,False]:self.assertEqual(m.registration([186.67,306],scale,flipped),[320,240])
 def test_output_inside_source_rejected(self):
  with self.assertRaisesRegex(ValueError,'outside'):m.run(m.ROOT/'forbidden.json')
 def test_float32_boundary_is_not_integer_threshold(self):
  converted=struct.unpack('>f',struct.pack('>f',32/255))[0]
  self.assertGreater(converted,32/255);self.assertFalse(32>32)
if __name__=='__main__':unittest.main()
