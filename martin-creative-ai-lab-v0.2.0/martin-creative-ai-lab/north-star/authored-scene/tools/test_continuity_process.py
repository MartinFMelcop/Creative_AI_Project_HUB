"""Refutable readiness ordering for the existing process instrument.

Fake processes isolate the client protocol; actual host/runtime evidence belongs to
continuity-process.py integration execution. No host assembly or recipient is edited.
"""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

PATH = Path(__file__).with_name('continuity-process.py')
spec = importlib.util.spec_from_file_location('authored_continuity_process', PATH)
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


class Clock:
    def __init__(self):
        self.now = 0.0

    def monotonic(self):
        return self.now

    def sleep(self, seconds):
        self.now += seconds


class Process:
    def __init__(self, command, stdout, stderr, clock, events, line=None,
                 dead=False, ready_at=None):
        self.stdout, self.stderr = stdout, stderr
        self.clock, self.events = clock, events
        port = command[command.index('--serve') + 1]
        self.expected = 'READY http://127.0.0.1:' + port + '/'
        self.line = self.expected if line is None else line.replace('{expected}', self.expected)
        self.dead, self.ready_at = dead, ready_at
        self.polls = 0
        self.emitted = False
        self.returncode = None
        if dead:
            stderr.write(b'Declared startup refusal\n')
            stderr.flush()

    def poll(self):
        self.polls += 1
        if self.dead:
            self.returncode = 1
            return self.returncode
        due = self.polls >= 3 if self.ready_at is None else self.clock.now >= self.ready_at
        if due and not self.emitted:
            self.stdout.write((self.line + '\n').encode())
            self.stdout.flush()
            self.events.append(('stdout', self.line))
            self.emitted = True
        return self.returncode


class ReadinessProtocol(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='authored-readiness-')
        self.root = Path(self.temp.name)
        self.instrument = subject.Instrument.__new__(subject.Instrument)
        self.instrument.dotnet = '/declared/fake/dotnet'
        self.instrument.output = self.root
        self.instrument.number = 0
        self.instrument.processes = []
        self.instrument.commands = []
        self.clock = Clock()
        self.events = []
        self.process = None

    def tearDown(self):
        for row in self.instrument.processes:
            row['stdout'].close()
            row['stderr'].close()
        self.temp.cleanup()

    def run_start(self, line=None, dead=False, ready_at=None, http_error=False):
        def spawn(command, **kwargs):
            self.process = Process(command, kwargs['stdout'], kwargs['stderr'],
                                   self.clock, self.events, line, dead, ready_at)
            return self.process

        def request(url, body=None):
            # This is the causal negative: the old polling client calls here
            # before any matching startup signal and must fail this assertion.
            self.assertIn(('stdout', self.process.expected), self.events,
                          'HTTP was attempted before matching READY')
            self.events.append(('http', url))
            if http_error:
                raise OSError('Declared endpoint not yet observable')
            return 200, {'declared': 'state'}

        with mock.patch.object(subject.subprocess, 'Popen', side_effect=spawn), \
             mock.patch.object(subject.time, 'monotonic', side_effect=self.clock.monotonic), \
             mock.patch.object(subject.time, 'sleep', side_effect=self.clock.sleep), \
             mock.patch.object(self.instrument, 'request', side_effect=request) as probe:
            self.probe = probe
            return self.instrument.start('--new', self.root / 'one run.json')

    def test_start_does_not_probe_http_before_exact_ready(self):
        row, observed = self.run_start()
        self.assertEqual(observed, {'declared': 'state'})
        self.assertEqual(self.probe.call_count, 1)
        self.assertEqual(self.events, [('stdout', 'READY ' + row['url'] + '/'),
                                       ('http', row['url'])])

    def test_other_url_or_embedded_banner_does_not_authorize_http(self):
        for label, line in (('wrong URL', 'READY http://127.0.0.1:1/'),
                            ('embedded exact banner', 'noise {expected}'),
                            ('no READY', '')):
            with self.subTest(label=label):
                self.clock.now = 0
                self.events.clear()
                with self.assertRaisesRegex(ValueError, 'matching READY'):
                    self.run_start(line=line)
                self.probe.assert_not_called()
                self.assertLessEqual(self.clock.now, 10.05)

    def test_process_refusal_before_ready_is_not_http_readiness(self):
        with self.assertRaisesRegex(ValueError, 'Declared startup refusal'):
            self.run_start(dead=True)
        self.probe.assert_not_called()
        self.assertEqual(self.clock.now, 0)

    def test_http_and_stdout_share_the_original_deadline(self):
        with self.assertRaisesRegex(ValueError, 'did not become ready'):
            self.run_start(ready_at=9.95, http_error=True)
        self.assertGreater(self.probe.call_count, 0)
        self.assertLessEqual(self.probe.call_count, 5)
        self.assertGreaterEqual(self.clock.now, 10)
        self.assertLessEqual(self.clock.now, 10.05)


if __name__ == '__main__':
    unittest.main()
