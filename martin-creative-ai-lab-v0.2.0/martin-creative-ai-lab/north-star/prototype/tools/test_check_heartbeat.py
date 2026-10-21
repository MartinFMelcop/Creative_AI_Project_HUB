"""Protect post-execution conclusions using actual measured rows and corrupt controls."""
import json
from pathlib import Path
import tempfile
import unittest
import check_heartbeat as gate

EVIDENCE=Path(__file__).resolve().parents[3]/'evidence'


class LeaseEvidenceChecks(unittest.TestCase):
    def current(self):return json.loads((EVIDENCE/'north-star-heartbeat/transport.json').read_text())

    def test_actual_current_grouped_rows_pass(self):
        self.assertEqual(gate.check_rows(self.current()['observations']),4)

    def test_actual_pre_fix_rows_fail_repeated_expiry_rule(self):
        old=json.loads((EVIDENCE/'north-star-transport/results.json').read_text())
        with self.assertRaisesRegex(ValueError,'lease expiry'):gate.check_rows(old['observations'])

    def test_missing_stale_exposure_cannot_prove_recovery(self):
        data=self.current()
        for row in data['observations']:row['client_observation']['frame_visits']['stale']=0
        with self.assertRaisesRegex(ValueError,'No observed stale'):gate.check_rows(data['observations'])

    def check_file(self, data):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'study.json';file.write_text(json.dumps(data));return gate.check(file)

    def test_omitted_take_is_rejected_even_with_adjusted_total(self):
        data=self.current();data['identities']=gate.study.identities()
        data['observations'].pop();data['checks']['terminal_and_stream_contracts_passed']-=1
        with self.assertRaisesRegex(ValueError,'omitted or duplicated'):self.check_file(data)

    def test_source_identity_mismatch_is_rejected(self):
        data=self.current();data['identities']=gate.study.identities();data['identities']['authority/remote.gd']='0'*64
        with self.assertRaisesRegex(ValueError,'source identity'):self.check_file(data)


if __name__=='__main__':unittest.main()
