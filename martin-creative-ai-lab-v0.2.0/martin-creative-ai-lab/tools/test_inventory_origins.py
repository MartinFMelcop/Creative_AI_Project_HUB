#!/usr/bin/env python3
"""Inventory controls: deterministic identity, ownership overlap and corrupt inputs."""
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
import inventory_origins as inventory

class InventoryControls(unittest.TestCase):
    def test_classification_and_tree_identity_detect_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'model.cs').write_text('public class Model {}')
            (root/'tests').mkdir();(root/'tests/test_model.py').write_text('assert True')
            self.assertEqual(inventory.classify('tests/test_model.py'),'tests_and_controls')
            first=inventory.summarize(root,['model.cs','tests/test_model.py'])
            self.assertEqual(first,inventory.summarize(root,['tests/test_model.py','model.cs']))
            (root/'model.cs').write_text('public class Changed {}')
            self.assertNotEqual(first['tree_sha256'],inventory.summarize(root,['model.cs','tests/test_model.py'])['tree_sha256'])

    def test_missing_or_linked_file_cannot_count_as_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with self.assertRaises(ValueError):inventory.summarize(root,['missing.cs'])
            (root/'actual.cs').write_text('class A {}');(root/'alias.cs').symlink_to(root/'actual.cs')
            with self.assertRaises(ValueError):inventory.summarize(root,['alias.cs'])

    def test_package_identity_does_not_promote_partial_duplication(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name,unique in [('first.zip','a'),('second.zip','b')]:
                with ZipFile(root/name,'w') as archive:
                    archive.writestr('runtime',b'x'*(1024*1024));archive.writestr('source',unique)
            report=inventory.package_audit(root,['first.zip','second.zip'])
            self.assertEqual(report['package_count'],2)
            self.assertEqual(report['identical_whole_packages'],[])
            self.assertEqual(len(report['repeated_payloads_over_1_mib']),1)
            self.assertEqual(len(report['repeated_payloads_over_1_mib'][0]['copies']),2)
            (root/'broken.zip').write_text('not an archive')
            with self.assertRaises(ValueError):inventory.package_audit(root,['broken.zip'])

    def test_origin_identity_and_overlap_are_explicit(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'registry').mkdir()
            rows=[{'id':key} for key in inventory.LABS]
            (root/'registry/projects.json').write_text(json.dumps({'projects':rows}))
            self.assertEqual(len(inventory.read_origins(root)),11)
            rows.append({'id':'NORTH-STAR'});(root/'registry/projects.json').write_text(json.dumps({'projects':rows}))
            self.assertEqual(len(inventory.read_origins(root)),11)
            rows.pop()
            rows[-1]['id']='P01';(root/'registry/projects.json').write_text(json.dumps({'projects':rows}))
            with self.assertRaises(ValueError):inventory.read_origins(root)
            self.assertTrue(inventory.selected('shared/model.cs',['shared']))
            self.assertFalse(inventory.selected('shared-other/model.cs',['shared']))

if __name__=='__main__':unittest.main()
