#!/usr/bin/env python3
"""Check the distributed ELF/PCK, permissions, exact contents and required notices."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NAMES = {'veilbreak.x86_64','veilbreak.pck','README.txt','GODOT-LICENSE.txt','GODOT-COPYRIGHT.txt','ASSET-PROVENANCE.json'}


def check(path):
    with zipfile.ZipFile(path) as z:
        assert len(z.namelist())==len(NAMES) and set(z.namelist())=={'Veilbreak/'+name for name in NAMES}, 'Unexpected bundle entries.'
        assert z.testzip() is None, 'Corrupt ZIP entry.'
        elf = z.read('Veilbreak/veilbreak.x86_64')
        assert elf[:4]==b'\x7fELF' and elf[4:6]==b'\x02\x01' and struct.unpack_from('<H',elf,18)[0]==62, 'Not a Linux x86_64 ELF.'
        assert (z.getinfo('Veilbreak/veilbreak.x86_64').external_attr>>16)&0o111, 'Executable permission absent.'
        assert z.read('Veilbreak/veilbreak.pck')[:4]==b'GDPC', 'Missing Godot resource pack.'
        for name in ['GODOT-LICENSE.txt','GODOT-COPYRIGHT.txt']:
            assert z.read('Veilbreak/'+name)==(ROOT/'third-party'/name).read_bytes(), 'Engine notice differs.'
        assert z.read('Veilbreak/ASSET-PROVENANCE.json')==(ROOT/'media/provenance.json').read_bytes(), 'Asset provenance differs.'
        json.loads(z.read('Veilbreak/ASSET-PROVENANCE.json'))
    with path.open('rb') as f:
        sha = hashlib.file_digest(f,'sha256').hexdigest()
    assert path.with_suffix('.zip.sha256').read_text()==sha+'  '+path.name+'\n', 'Download checksum mismatch.'
    return {'entries':len(NAMES),'bytes':path.stat().st_size,'sha256':sha}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('archive', nargs='?', type=Path, default=ROOT/'dist/veilbreak-linux-0.5.0.zip')
    try:
        print('LINUX_PACKAGE',json.dumps(check(p.parse_args().archive)))
    except (AssertionError,OSError,ValueError,zipfile.BadZipFile) as e:
        p.exit(1, 'FAIL: '+str(e)+'\n')
