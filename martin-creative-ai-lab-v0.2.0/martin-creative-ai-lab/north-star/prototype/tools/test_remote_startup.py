"""Protect bounded startup, diagnostics and delayed real-window input verification."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

import verify_remote_input as runner


class StartupChecks(unittest.TestCase):
    def test_missing_window_is_bounded_and_child_remains_callers_responsibility(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder)/'child.log';log.write_text('Controlled missing-window diagnostic.\n')
            child = subprocess.Popen([sys.executable,'-c','import time; time.sleep(10)'])
            original = runner.window;runner.window = lambda display:None
            try:
                started = time.monotonic()
                with self.assertRaisesRegex(ValueError,'bounded startup: Controlled missing-window'):
                    runner.wait_window(None,child,log,timeout=.1)
                self.assertLess(time.monotonic()-started,1)
                self.assertIsNone(child.poll())
            finally:
                runner.window = original;child.terminate();child.wait(timeout=3)

    def test_stopped_process_reports_its_native_diagnostic(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder)/'child.log'
            with log.open('w') as stream:
                child = subprocess.Popen([sys.executable,'-c','print("Controlled renderer failure",flush=True)'],stdout=stream)
                child.wait(timeout=3)
            with self.assertRaisesRegex(ValueError,'stopped before discovery: Controlled renderer failure'):
                runner.wait_window(None,child,log,timeout=.1)

    def test_diagnostics_keep_bounded_known_logs_only(self):
        with tempfile.TemporaryDirectory() as folder:
            scratch = Path(folder)/'scratch';output = Path(folder)/'output';scratch.mkdir();output.mkdir()
            (scratch/'source-window.log').write_bytes(b'x'*70000+b'RENDERER_TAIL')
            (scratch/'not-a-diagnostic.json').write_text('Do not collect protocol files')
            runner.preserve_diagnostics(scratch,output)
            files = list((output/'failure').iterdir());self.assertEqual([p.name for p in files],['source-window.log'])
            self.assertEqual(files[0].stat().st_size,65536);self.assertTrue(files[0].read_bytes().endswith(b'RENDERER_TAIL'))

    def test_transport_live_still_waits_for_neutral_rearm(self):
        ready = dict(status='live', confirmed={'tick': 1}, focused=True,
                     suspended=False, quarantined=False,
                     actions=[{'caption': 'READY', 'cost': 999}] * 3)
        blocked = dict(ready, actions=[{'caption': 'RELEASE TO REARM'}] * 3)
        sequence = iter([blocked, ready])
        observed = runner.wait_input_ready(lambda: next(sequence), timeout=.2)
        self.assertEqual(observed, ready)
        # Readiness must not wait for desired semantic values and hide a real defect.
        self.assertEqual(observed['actions'][1]['cost'], 999)

    def test_rearm_timeout_and_terminal_state_remain_fail_closed(self):
        blocked = dict(status='live', confirmed={'tick': 1}, focused=True,
                       suspended=False, quarantined=True, actions=[])
        with self.assertRaisesRegex(ValueError, 'bounded neutral rearm'):
            runner.wait_input_ready(lambda: blocked, timeout=.01)
        with self.assertRaisesRegex(ValueError, 'failed before neutral'):
            runner.wait_input_ready(lambda: dict(blocked, status='error'), timeout=.1)

    def test_six_second_graphical_startup_preserves_real_source_and_pack_controls(self):
        engine = shutil.which(os.environ.get('CROSSING_GODOT','godot'))
        self.assertIsNotNone(engine)
        with tempfile.TemporaryDirectory(prefix='remote-delayed-startup-') as folder:
            root = Path(folder);wrapper = root/'delayed-godot'
            wrapper.write_text('#!'+sys.executable+'\nimport os,sys,time\n'
                               'if "--headless" not in sys.argv and "--version" not in sys.argv:time.sleep(6)\n'
                               f'os.execv({engine!r},[{engine!r},*sys.argv[1:]])\n')
            wrapper.chmod(0o755)
            original_server = runner.authority.SERVER
            staged_server = root/'delayed-neutral-server.gd'
            source = original_server.read_text()
            marker = '\thigh_water=int(data.seq);input_tick=server_tick;accepted+=1'
            self.assertIn(marker, source)
            staged_server.write_text(source.replace(marker,
                '\tif quarantined and server_tick-active_tick<24:return\n' + marker))
            runner.authority.SERVER = staged_server
            try:result = runner.verify(root/'result',str(wrapper))
            except Exception:
                destination = os.environ.get('NORTH_STAR_STARTUP_RESULT')
                if destination and (root/'result/failure').is_dir():
                    shutil.copytree(root/'result/failure',Path(destination).with_suffix('')/'failure',dirs_exist_ok=True)
                raise
            finally:
                runner.authority.SERVER = original_server
            result['controlled_initial_neutral_delay_ticks'] = 24
            result['base_input_identities'] = result.pop('identities')
            result['controlled_authority'] = {
                'base_sha256': runner.authority.digest(original_server),
                'executed_staged_sha256': runner.authority.digest(staged_server),
                'injection': 'Hold initial neutral rearm until 24 server ticks after hello; preserve model and client gates.'}
            result['scope'] = 'Controlled delayed-neutral authority fixture with actual unchanged source/PCK model and remote window; not an unchanged authority-script execution.'
            self.assertEqual(result['checks'],{'passed':46,'failed':0})
            self.assertEqual(set(result['startup']),{'source','pack'})
            for observed in result['startup'].values():
                self.assertGreaterEqual(observed['rendered_input_ready_ms'],6000)
                self.assertTrue(observed['authority_started_after_preflight'])
            destination = os.environ.get('NORTH_STAR_STARTUP_RESULT')
            if destination:
                output = Path(destination);output.parent.mkdir(parents=True,exist_ok=True)
                output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')


if __name__=='__main__':unittest.main()
