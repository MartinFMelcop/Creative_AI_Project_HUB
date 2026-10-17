"""Adversarial checks against actual recorded mixer artifacts, using private copies."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import wave

sys.path.insert(0, str(Path(__file__).parent))
from verify_sound import ROOT, inspect

FIXTURE = ROOT.parents[1] / 'evidence/north-star-guard-techniques'


class MixerEvidenceChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        for path in FIXTURE.iterdir():
            if path.suffix == '.wav' or path.name == 'capture.json':
                shutil.copyfile(path, self.folder / path.name)

    def tearDown(self):
        self.temp.cleanup()

    def rewrite(self, name, sample):
        path = self.folder / (name + '.wav')
        with wave.open(str(path)) as source:
            params = source.getparams()
            data = bytearray(source.readframes(source.getnframes()))
        if sample == 0:
            data[:] = bytes(len(data))
        else:
            data[0:2] = int(sample).to_bytes(2, 'little', signed=True)
        with wave.open(str(path), 'wb') as target:
            target.setparams(params)
            target.writeframes(data)

    def test_recorded_actual_output_is_accepted(self):
        self.assertEqual(inspect(self.folder)['driver'], 'Dummy')

    def test_silent_warning_is_rejected(self):
        self.rewrite('guardian-block', 0)
        with self.assertRaisesRegex(ValueError, 'audible mixer'):
            inspect(self.folder)

    def test_mute_leak_is_rejected(self):
        self.rewrite('muted-block', 100)
        with self.assertRaisesRegex(ValueError, 'Silence control'):
            inspect(self.folder)

    def test_wrong_response_ownership_is_rejected(self):
        path = self.folder / 'capture.json'
        record = json.loads(path.read_text())
        next(r for r in record['records'] if r['name'] == 'guardian-block')['sound']['events'][-1]['cue'] = 'draw'
        path.write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError, 'cue ownership'):
            inspect(self.folder)

    def test_changed_synthesis_is_rejected(self):
        self.rewrite('cue-block', 1)
        with self.assertRaisesRegex(ValueError, 'synthesis differs'):
            inspect(self.folder)

    def test_sound_is_not_accepted_as_historical_silence(self):
        with self.assertRaisesRegex(ValueError, 'Historical silent'):
            inspect(self.folder, baseline=True)


if __name__ == '__main__':
    unittest.main()
