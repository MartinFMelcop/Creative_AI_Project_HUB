"""Exercise false readiness and bounded preflight without replacing game owners."""
import json
import os
import shutil
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
import run_source_experiment as launch

class LaunchControls(unittest.TestCase):
    def test_unknown_catalog_selection(self):
        with self.assertRaises(ValueError):launch.portfolio.validate_launch(launch.ROOT,'invented',{})

    def test_invalid_lifetime_before_build(self):
        for duration in (0,601):
            with self.assertRaises(ValueError):launch.launch('field-journey','dotnet',8099,duration,{})

    def test_wrong_sdk_refuses_before_host(self):
        result=subprocess.run([sys.executable,str(launch.ROOT/'tools/run_source_experiment.py'),'run','field-journey','--dotnet','/bin/false','--seconds','1'],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,1);self.assertIn('Exact SDK',result.stderr);self.assertNotIn('"event": "ready"',result.stdout)

    def test_wrong_observation_schema(self):
        with self.assertRaises(ValueError):launch.validate_http('field-journey',{'sequence':0,'accepted':True})

    def test_false_ready_with_actual_wrong_http(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b'{"sequence":0,"accepted":true}')
            def log_message(self,*args):pass
        server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        url=f'http://127.0.0.1:{server.server_port}/'
        process=subprocess.Popen([sys.executable,'-c',f'import time; print({("READY "+url)!r},flush=True); time.sleep(5)'],stdout=subprocess.PIPE,text=True)
        advertised=process.stdout.readline().strip()
        try:
            with self.assertRaisesRegex(ValueError,'Expected Field observation'):
                launch.wait_ready(process,url,'field-journey',[advertised],time.monotonic()+1)
        finally:
            process.terminate();process.wait(timeout=3);process.stdout.close();server.shutdown();server.server_close();thread.join(timeout=2)

    def test_occupied_port_refuses_without_host(self):
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));sock.listen();port=sock.getsockname()[1]
            result=subprocess.run([sys.executable,str(launch.ROOT/'tools/run_source_experiment.py'),'run','field-journey','--dotnet',os.environ.get('SOURCE_LAUNCH_DOTNET') or shutil.which('dotnet') or '/workspace/work/authored-scene/dotnet/dotnet','--port',str(port),'--seconds','1'],capture_output=True,text=True,timeout=10)
            self.assertEqual(result.returncode,1);self.assertIn('Address already in use',result.stderr);self.assertNotIn('"event": "ready"',result.stdout)

if __name__=='__main__':unittest.main()
