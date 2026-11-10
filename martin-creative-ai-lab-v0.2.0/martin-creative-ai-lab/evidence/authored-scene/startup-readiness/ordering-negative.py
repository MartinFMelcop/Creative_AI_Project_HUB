import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

root = Path('/workspace/work/authored-startup/martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab')
out = Path('/workspace/work/authored-startup-science')
relative = 'martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/north-star/authored-scene/tools/continuity-process.py'
old = subprocess.check_output(['git', 'show', '5990be50bc7ea023cb1f13db24c64f465d72cf58:' + relative], cwd=root)
old_path = out / 'original-5990-continuity-process.py'
old_path.write_bytes(old)

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

test_path = root / 'north-star/authored-scene/tools/test_continuity_process.py'
tests = load('readiness_tests', test_path)
original = load('original_continuity_process', old_path)
# The process is a declared fixture, but keep launch path globals identical too.
for name in ('ROOT', 'STUDY', 'DLL', 'WEB'):
    setattr(original, name, getattr(tests.subject, name))
tests.subject = original
suite = unittest.TestSuite([tests.ReadinessProtocol('test_start_does_not_probe_http_before_exact_ready')])
stream = io.StringIO()
result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
transcript = stream.getvalue()
(out / 'ordering-negative.txt').write_text(transcript)
record = {
    'kind': 'actual_old_instrument_ordering_negative',
    'baseline_commit': '5990be50bc7ea023cb1f13db24c64f465d72cf58',
    'original_instrument_sha256': hashlib.sha256(old).hexdigest(),
    'current_test_sha256': hashlib.sha256(test_path.read_bytes()).hexdigest(),
    'test': 'ReadinessProtocol.test_start_does_not_probe_http_before_exact_ready',
    'tests_run': result.testsRun,
    'failures': len(result.failures),
    'errors': len(result.errors),
    'observed_failure': 'HTTP was attempted before matching READY',
    'specific_failure_detected': len(result.failures) == 1 and not result.errors and 'HTTP was attempted before matching READY' in transcript,
    'scope': 'The same current ordering test exercises original Instrument.start with the identical declared fake process/clock/HTTP probe. No host/runtime/source archive changed. This is a controlled protocol negative, separate from actual captured HttpListener stack and full integration.',
    'transcript': 'ordering-negative.txt'
}
(out / 'ordering-negative.json').write_text(json.dumps(record, indent=2) + '\n')
print(transcript)
assert record['specific_failure_detected'], 'Old-client negative did not fail in the intended way'
sys.exit(1)
