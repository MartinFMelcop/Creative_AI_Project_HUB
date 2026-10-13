#!/usr/bin/env python3
"""Check original atlas identity and PCM contracts, not artistic approval."""
from pathlib import Path
import json,hashlib,wave,struct,zlib
ROOT=Path(__file__).resolve().parents[1]
media=ROOT/'Native/media'
meta=json.loads((media/'provenance.json').read_text())
data=(media/'portraits.png').read_bytes()
assert data[:8]==b'\x89PNG\r\n\x1a\n'
assert list(struct.unpack('>II',data[16:24]))==meta['visual']['size']==[1774,887]
assert hashlib.sha256(data).hexdigest()==meta['visual']['sha256']
# Validate every PNG chunk CRC; pixel bytes are not modified by this check.
pos=8
while pos<len(data):
    length=struct.unpack('>I',data[pos:pos+4])[0];chunk=data[pos+4:pos+8+length]
    assert zlib.crc32(chunk)&0xffffffff==struct.unpack('>I',data[pos+8+length:pos+12+length])[0]
    pos+=12+length
assert pos==len(data)
catalog=json.loads((media/'audio/catalog.json').read_text());assert len(catalog['cues'])==7
for cue in catalog['cues']:
    path=media/'audio'/(cue['name']+'.wav')
    assert hashlib.sha256(path.read_bytes()).hexdigest()==cue['sha256']
    with wave.open(str(path)) as f:
        assert f.getparams()[:3]==(1,2,44100)
        assert abs(f.getnframes()/44100-cue['seconds'])<1e-6
        values=struct.unpack('<'+'h'*f.getnframes(),f.readframes(f.getnframes()))
    assert 0<max(abs(v) for v in values)<32767
    assert abs(values[0])<=1 and abs(values[-1])<30
print('PASS: unchanged 4x2 portrait PNG/CRC and seven mono PCM16 cue hashes/durations/endpoints/non-clipping.')
