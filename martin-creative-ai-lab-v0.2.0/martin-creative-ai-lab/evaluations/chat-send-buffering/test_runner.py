"""Exercise export boundaries and gates that can invalidate an artifact result."""

import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("task_runner", Path(__file__).with_name("run.py"))
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class TaskRunnerTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.workspace = Path(self.scratch.name) / "candidate"
        runner.prepare(self.workspace)

    def test_export_has_only_starter_and_brief_without_reference_or_history(self):
        paths = {p.relative_to(self.workspace).as_posix()
                 for p in self.workspace.rglob("*") if p.is_file()}
        self.assertEqual(paths, {*runner.FILES, "BRIEF.md", "task-manifest.json"})
        client = (self.workspace / "public/client.js").read_bytes()
        self.assertEqual(client, runner.git_bytes(runner.BASELINE, "public/client.js"))
        self.assertNotEqual(client, (runner.PROJECT / "public/client.js").read_bytes())
        self.assertEqual(runner.read_submission(self.workspace), client)

    def test_export_never_overwrites_an_existing_workspace(self):
        user_file = self.workspace / "keep.txt"
        user_file.write_text("existing user work")
        with self.assertRaises(FileExistsError):
            runner.prepare(self.workspace)
        self.assertEqual(user_file.read_text(), "existing user work")

    def test_support_file_change_is_rejected_before_execution(self):
        (self.workspace / "server.cjs").write_text("changed server")
        record = runner.check(self.workspace)
        self.assertEqual(record["status"], "rejected")
        self.assertIn("server.cjs", record["reason"])
        self.assertEqual(record["commands"], [])

    def test_reference_or_extra_file_in_submission_is_rejected(self):
        (self.workspace / "answer.js").write_text("reference")
        self.assertEqual(runner.check(self.workspace)["gate"], "submission_scope")

    def test_missing_client_is_a_rejected_submission(self):
        (self.workspace / "public/client.js").unlink()
        self.assertEqual(runner.check(self.workspace)["status"], "rejected")

    def test_linked_client_cannot_substitute_an_external_artifact(self):
        client = self.workspace / "public/client.js"
        client.unlink()
        client.symlink_to(runner.PROJECT / "public/client.js")
        self.assertEqual(runner.check(self.workspace)["status"], "rejected")

    def test_complete_results_distinguish_acceptance_and_rejection(self):
        accepted = "# tests 17\n# pass 17\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n"
        rejected = accepted.replace("# pass 17", "# pass 15").replace("# fail 0", "# fail 2")
        self.assertEqual(runner.classify_tap(accepted, 0)[0], "accepted")
        self.assertEqual(runner.classify_tap(rejected, 1)[0], "rejected")
        self.assertEqual(runner.classify_tap(accepted, 1)[0], "inconclusive")

    def test_incomplete_or_skipped_execution_is_never_accepted(self):
        for output in ("", "# tests 0\n# pass 0\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n",
                       "# tests 17\n# pass 16\n# fail 0\n# cancelled 0\n# skipped 1\n# todo 0\n"):
            with self.subTest(output=output):
                self.assertEqual(runner.classify_tap(output, 0)[0], "inconclusive")

    def test_command_failure_preserves_both_streams_and_actual_exit(self):
        command = [sys.executable, '-c', "import sys; print('progress'); print('diagnostic',file=sys.stderr); sys.exit(7)"]
        record = runner.invoke(command, Path(self.scratch.name), os.environ.copy(), 5)
        self.assertEqual(record['exit_code'], 7)
        self.assertEqual(record['stdout'], 'progress\n')
        self.assertEqual(record['stderr'], 'diagnostic\n')
        self.assertFalse(record['timed_out'])

    def test_timeout_preserves_attempt_and_partial_output(self):
        command = [sys.executable, '-c', "import sys,time; print('progress',flush=True); print('diagnostic',file=sys.stderr,flush=True); time.sleep(60)"]
        record = runner.invoke(command, Path(self.scratch.name), os.environ.copy(), .3)
        self.assertEqual(record['command'], command)
        self.assertEqual(record['stdout'], 'progress\n')
        self.assertEqual(record['stderr'], 'diagnostic\n')
        self.assertTrue(record['timed_out'])
        self.assertEqual(record['timeout_seconds'], .3)
        self.assertGreaterEqual(record['elapsed_seconds'], .3)
        self.assertTrue(record['capture_complete'])

    @unittest.skipUnless(os.name == 'posix' and Path('/proc').exists(), 'POSIX/Linux process-group verification')
    def test_timeout_stops_inherited_child_even_when_it_ignores_termination(self):
        child = "import signal,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); print('child ready',flush=True); time.sleep(60)"
        parent = "import signal,subprocess,sys,time; signal.signal(signal.SIGTERM,signal.SIG_IGN); child=subprocess.Popen([sys.executable,'-c',sys.argv[1]]); print('child_pid='+str(child.pid),flush=True); time.sleep(60)"
        started = time.monotonic()
        try:
            record = runner.invoke([sys.executable, '-c', parent, child],
                                   Path(self.scratch.name), os.environ.copy(), .5)
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout.decode() if isinstance(exc.stdout, bytes) else exc.stdout
            self.stop_probe_child(output)
            raise
        try:
            child_pid = int(record['stdout'].split('child_pid=')[1].splitlines()[0])
            state_path = Path(f'/proc/{child_pid}/stat')
            state = state_path.read_text().split(') ', 1)[1].split()[0] if state_path.exists() else None
            self.assertIn(state, (None, 'Z', 'X'), 'No running probe child may survive timeout')
            self.assertTrue(record['timed_out'])
            self.assertIn('child ready', record['stdout'])
            self.assertLess(time.monotonic() - started, 3.5)
        finally:
            self.stop_probe_child(record['stdout'])

    @staticmethod
    def stop_probe_child(output):
        if output and 'child_pid=' in output:
            pid = int(output.split('child_pid=')[1].splitlines()[0])
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    @unittest.skipUnless(os.name == 'posix' and Path('/proc').exists(), 'POSIX/Linux detached-child verification')
    def test_detached_pipe_holder_marks_incomplete_capture_and_returns(self):
        parent = "import subprocess,sys,time; child=subprocess.Popen([sys.executable,'-c','import time; print(\"detached ready\",flush=True); time.sleep(60)'],start_new_session=True); print('child_pid='+str(child.pid),flush=True); time.sleep(60)"
        started = time.monotonic()
        try:
            record = runner.invoke([sys.executable, '-c', parent], Path(self.scratch.name), os.environ.copy(), .3)
        except subprocess.TimeoutExpired as exc:
            output = exc.stdout.decode() if isinstance(exc.stdout, bytes) else exc.stdout
            self.stop_probe_child(output)
            raise
        try:
            self.assertTrue(record['timed_out'])
            self.assertFalse(record['capture_complete'])
            self.assertIn('detached ready', record['stdout'])
            self.assertLess(time.monotonic() - started, 3.5)
        finally:
            # This fixture deliberately escapes the group; only its own PID is stopped.
            self.stop_probe_child(record['stdout'])

    def test_timeout_at_each_gate_is_inconclusive_and_keeps_diagnostics(self):
        actual_invoke = runner.invoke
        command = [sys.executable, '-c', "import time; print('gate progress',flush=True); time.sleep(60)"]
        success = {'exit_code': 0, 'stdout': '{}', 'stderr': '', 'timed_out': False, 'launch_error': None}
        for index, gate in enumerate(('client_syntax', 'environment', 'behavior_and_regressions')):
            with self.subTest(gate=gate):
                calls = []
                def injected(*args):
                    calls.append(args)
                    if len(calls) <= index:
                        return dict(success)
                    return actual_invoke(command, Path(self.scratch.name), os.environ.copy(), .3)
                with patch.object(runner, 'invoke', side_effect=injected):
                    record = runner.check(self.workspace)
                self.assertEqual(record['status'], 'inconclusive')
                self.assertEqual(record['gate'], gate)
                self.assertEqual(record['commands'][-1]['stdout'], 'gate progress\n')
                self.assertTrue(record['commands'][-1]['timed_out'])

    def test_pass_summary_after_deadline_cannot_be_accepted(self):
        success = {'exit_code': 0, 'stdout': '{}', 'stderr': '', 'timed_out': False, 'launch_error': None}
        late = {**success, 'timed_out': True,
                'stdout': '# tests 17\n# pass 17\n# fail 0\n# cancelled 0\n# skipped 0\n# todo 0\n'}
        with patch.object(runner, 'invoke', side_effect=[success, success, late]):
            record = runner.check(self.workspace)
        self.assertEqual(record['status'], 'inconclusive')
        self.assertTrue(record['commands'][-1]['timed_out'])

    def test_missing_executable_keeps_attempt_without_rejecting_artifact(self):
        actual_invoke = runner.invoke
        command = [str(Path(self.scratch.name) / 'absent-command')]
        with patch.object(runner, 'invoke', side_effect=lambda *args: actual_invoke(command, Path(self.scratch.name), os.environ.copy(), 5)):
            record = runner.check(self.workspace)
        self.assertEqual(record['status'], 'inconclusive')
        self.assertEqual(record['commands'][-1]['command'], command)
        self.assertIsNotNone(record['commands'][-1]['launch_error'])


if __name__ == "__main__":
    unittest.main()
