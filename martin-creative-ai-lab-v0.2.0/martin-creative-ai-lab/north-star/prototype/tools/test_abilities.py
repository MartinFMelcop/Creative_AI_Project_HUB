#!/usr/bin/env python3
"""Refutable candidate authoring controls through the actual pinned engine."""
import json
import os
from pathlib import Path
import tempfile
import unittest
import abilities

class Candidates(unittest.TestCase):
    def test_changed_candidate_executes_without_adoption(self):
        before=abilities.identities()
        live=abilities.ROOT/'abilities/catalog.json';original=live.read_bytes()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);candidate=root/'catalog.json';output=root/'result.json'
            data=json.loads(original);data['rushes'][0]['speed']=500;candidate.write_text(json.dumps(data))
            self.assertEqual(abilities.check(candidate,output,os.environ.get('CROSSING_GODOT','godot')),0)
            report=json.loads(output.read_text());profile=report['profiles'][0]
            self.assertAlmostEqual(profile['travel']['distance'],60,places=3)
            self.assertEqual(profile['travel']['energy_after_travel'],80)
            self.assertEqual(profile['journey']['starts'],1)
            self.assertEqual(report['candidate_sha256'],abilities.hashlib.sha256(candidate.read_bytes()).hexdigest())
        self.assertEqual(original,live.read_bytes());self.assertEqual(before,abilities.identities())

    def test_invalid_and_oversized_content_is_rejected_with_report(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name,content in [('bad','{"schema_version":true,"rushes":[]}'),('large',' '*17000),('malformed','{')]:
                candidate=root/(name+'.json');output=root/(name+'-result.json');candidate.write_text(content)
                self.assertEqual(abilities.check(candidate,output,os.environ.get('CROSSING_GODOT','godot')),2)
                self.assertFalse(json.loads(output.read_text())['valid'])
                self.assertEqual(candidate.read_text(),content)

    def test_output_cannot_overwrite_candidate_or_live_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            candidate=Path(folder)/'catalog.json';candidate.write_text('{}')
            for output in (candidate,abilities.ROOT/'abilities/catalog.json'):
                with self.assertRaises(ValueError):abilities.check(candidate,output)
            self.assertEqual(candidate.read_text(),'{}')

if __name__=='__main__':unittest.main()
