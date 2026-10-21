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

    def test_six_second_graphical_startup_preserves_real_source_and_pack_controls(self):
        engine = shutil.which(os.environ.get('CROSSING_GODOT','godot'))
        self.assertIsNotNone(engine)
        with tempfile.TemporaryDirectory(prefix='remote-delayed-startup-') as folder:
            root = Path(folder);wrapper = root/'delayed-godot'
            wrapper.write_text('#!'+sys.executable+'\nimport os,sys,time\n'
                               'if "--headless" not in sys.argv and "--version" not in sys.argv:time.sleep(6)\n'
                               f'os.execv({engine!r},[{engine!r},*sys.argv[1:]])\n')
            wrapper.chmod(0o755)
            try:result = runner.verify(root/'result',str(wrapper))
            except Exception:
                destination = os.environ.get('NORTH_STAR_STARTUP_RESULT')
                if destination and (root/'result/failure').is_dir():
                    shutil.copytree(root/'result/failure',Path(destination).with_suffix('')/'failure',dirs_exist_ok=True)
                raise
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
