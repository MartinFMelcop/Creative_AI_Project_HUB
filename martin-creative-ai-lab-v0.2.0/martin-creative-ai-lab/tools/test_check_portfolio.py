#!/usr/bin/env python3
"""Negative controls for the actual portfolio artifact contract, not human research."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile

import check_portfolio as contract

ROOT = Path(__file__).resolve().parents[1]


class PortfolioClaims(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'showcase/portfolio.json').read_text())

    def data(self):
        return copy.deepcopy(self.catalog)

    def test_actual_recipient_and_source_evidence_are_accepted(self):
        result = contract.validate(ROOT, self.data())
        self.assertIsInstance(result, dict)
        self.assertTrue(result)

    def test_stale_evidence_pin_cannot_supply_recipient_execution(self):
        data = self.data()
        data['recipients'][0]['evidence_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, '(?i)recorded evidence identity mismatch'):
            contract.validate(ROOT, data)

    def test_other_platform_archive_cannot_replace_named_recipient(self):
        data = self.data()
        data['recipients'][0]['archive_path'] = data['recipients'][1]['archive_path']
        with self.assertRaisesRegex(ValueError, '(?i)recipient identity mismatch'):
            contract.validate(ROOT, data)

    def test_source_experiment_cannot_be_declared_as_packaged_feature(self):
        data = self.data()
        data['recipients'][0]['included_experiments'] = ['field-journey', 'selected-passives']
        with self.assertRaisesRegex(ValueError, 'unsupported or missing fields'):
            contract.validate(ROOT, data)

    def test_unexecuted_unity_readiness_claim_is_not_an_allowed_field(self):
        for claim in ('unity_ready', 'build_operations_ready'):
            with self.subTest(claim=claim):
                data = self.data()
                data[claim] = True
                with self.assertRaisesRegex(ValueError, 'unsupported or missing fields'):
                    contract.validate(ROOT, data)

    def test_recipient_owner_cannot_masquerade_as_new_source_experiment(self):
        data = self.data()
        data['source_experiments'][0]['consumer_paths'] = ['north-star/authored-scene/Host/Program.cs']
        with self.assertRaisesRegex(ValueError, 'Source experiment consumer identity differs'):
            contract.validate(ROOT, data)

    def test_changed_archive_bytes_fail_even_when_zip_is_still_readable(self):
        data = self.data()
        # Copy only the real contract's inputs. No source, package or fixture in
        # the maintained tree is changed. The baseline must pass before mutation.
        names = {'labs/origins.json'}
        for row in data['recipients']:
            names.update(row[key] for key in ('archive_path', 'evidence_path', 'guide_path'))
        for row in data['source_experiments']:
            names.update(row[key] for key in ('guide_path', 'evidence_path'))
            names.update(row['consumer_paths'])
        with tempfile.TemporaryDirectory(prefix='portfolio-contract-') as folder:
            root = Path(folder)
            for name in sorted(names):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, target)
            contract.validate(root, copy.deepcopy(data))
            archive = root / data['recipients'][0]['archive_path']
            with archive.open('ab') as output:
                output.write(b'\nDECLARED NEGATIVE: changed recipient identity\n')
            with zipfile.ZipFile(archive) as source:
                self.assertIsNone(source.testzip(), 'Mutation preserves actual ZIP member CRCs')
            with self.assertRaisesRegex(ValueError, 'Recipient identity mismatch'):
                contract.validate(root, data)


if __name__ == '__main__':
    unittest.main()
