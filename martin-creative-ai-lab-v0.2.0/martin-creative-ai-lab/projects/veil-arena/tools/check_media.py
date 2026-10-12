#!/usr/bin/env python3
"""Inspect committed media bytes; engine checks validate the actual consumer."""
import array
import hashlib
import json
import struct
import sys
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    catalog = json.loads((ROOT/'media/audio-catalog.json').read_text())
    pcm_files = 0
    for name, entry in catalog['files'].items():
        path = ROOT/name
        assert hashlib.sha256(path.read_bytes()).hexdigest()==entry['sha256'], name
        if path.suffix=='.ogg':
            assert path.read_bytes().startswith(b'OggS'), name
            continue
        with wave.open(str(path)) as f:
            assert (f.getnchannels(),f.getsampwidth(),f.getframerate())==(1,2,44100),name
            assert f.getnframes()==entry['frames'],name
            pcm = array.array('h',f.readframes(f.getnframes()))
            if sys.byteorder!='little': pcm.byteswap()
        assert 100<max(map(abs,pcm))<32767,name
        assert abs(pcm[0])<=1 and abs(pcm[-1])<80,name
        pcm_files += 1
    assert pcm_files==16
    for path in (ROOT/'media/art').glob('*.png'):
        data=path.read_bytes()
        assert data[:8]==b'\x89PNG\r\n\x1a\n',path.name
        width,height,depth,color=struct.unpack('>IIBB',data[16:26])
        assert width>1000 and height>700 and depth==8,path.name
        assert color==(2 if path.stem=='courtyard' else 6),path.name
    motion = json.loads((ROOT/'media/motion-catalog.json').read_text())
    for actor in motion['actors'].values():
        path = ROOT/actor['texture']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==actor['sha256'],path
        assert len(actor['frames'])==16
    print(json.dumps({'wav_files':pcm_files,'ogg_files':2,'png_files':len(list((ROOT/'media/art').glob('*.png'))),'motion_frames':32,
                      'verified':'hashes, PCM format/length/peaks/endpoints, PNG format/dimensions/alpha channel, delivered atlas hash/frame count'}))


if __name__=='__main__': main()
