"""Failure boundaries must preserve existing evidence before any native execution."""
from pathlib import Path
import sys
import tempfile
import unittest
import evaluate_transport as study


class StudyBoundaries(unittest.TestCase):
    def test_missing_runtime_preserves_previous_result(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'result.json';output.write_text('previous evidence')
            with self.assertRaisesRegex(ValueError,'unavailable'):study.evaluate(output,'no-such-transport-engine')
            self.assertEqual(output.read_text(),'previous evidence')

    def test_invalid_protocol_preserves_result_with_specific_validation_error(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'result.json';output.write_text('previous evidence')
            for changes in ({'repetitions':True},{'repetitions':0},{'repetitions':4},{'profiles':[]},{'profiles':['direct','direct']},{'profiles':['unknown']}):
                with self.assertRaisesRegex(ValueError,'Repetitions' if 'repetitions' in changes else 'Unsupported'):
                    study.evaluate(output,sys.executable,**changes)
                self.assertEqual(output.read_text(),'previous evidence')

    def test_prototype_input_output_is_rejected(self):
        output=study.a.ROOT/'authority/remote.gd';before=output.read_bytes()
        with self.assertRaisesRegex(ValueError,'prototype inputs'):study.evaluate(output,sys.executable)
        self.assertEqual(output.read_bytes(),before)


if __name__=='__main__':unittest.main()
