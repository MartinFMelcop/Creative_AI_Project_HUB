"""Refutable live-protocol and verification-boundary controls, using real processes."""
import copy
import json
import os
from pathlib import Path
import shutil
import socket
import tempfile
import subprocess
import threading
import time
import unittest

import verify_authority as r


class AuthorityChecks(unittest.TestCase):
    def setUp(self):
        self.storage = tempfile.TemporaryDirectory(prefix="authority-tests-")
        self.folder = Path(self.storage.name)
        self.engine = os.environ.get("CROSSING_GODOT", "godot")

    def tearDown(self):self.storage.cleanup()

    def test_missing_engine_preserves_result(self):
        output = self.folder / "keep.json";output.write_text("keep")
        with self.assertRaisesRegex(ValueError, "unavailable"):r.verify(output, "no-such-authority-engine")
        self.assertEqual(output.read_text(), "keep")

    def test_oversize_partial_frame_is_closed_without_starting_model(self):
        with r.server(self.engine, self.folder / "oversize", seconds=2) as (port, report, process):
            peer = r.Peer(port)
            try:
                peer.socket.sendall(b"x" * 600)
                try:reply = peer.receive(lambda message:True, timeout=1)
                except (ValueError, ConnectionResetError):reply = {"reason":"closed"}
                self.assertIn(reply.get("reason"), ("oversize", "closed"))
            finally:peer.close()
        data = json.loads(report.read_text())
        self.assertEqual(data["model"]["mode"], "title")
        self.assertEqual(data["model"]["tick"], 0)
        self.assertEqual(data["rejected"].get("oversize"), 1)

    def test_bad_stream_before_hello_does_not_consume_the_one_session(self):
        with r.server(self.engine, self.folder / "recovery", seconds=2) as (port, report, process):
            peer = r.Peer(port);peer.socket.sendall(b"x" * 600);peer.close()
            # The server must poll and release this malformed transport first.
            import time
            time.sleep(.1)
            peer = r.Peer(port)
            try:
                peer.send(r.hello("standard"))
                self.assertEqual(peer.receive(lambda m:m.get("kind") == "welcome")["tick_hz"], 60)
            finally:peer.close()
        self.assertNotEqual(json.loads(report.read_text())["model"]["mode"], "title")

    def test_clock_mutant_is_rejected_by_real_observation(self):
        original = r.SERVER
        modified = self.folder / "fast.gd"
        text = original.read_text();needle = "game.step(STEP,command())"
        self.assertEqual(text.count(needle), 1)
        modified.write_text(text.replace(needle, needle + ";" + needle))
        r.SERVER = modified
        try:
            with r.server(self.engine, self.folder / "clock-mutant", seconds=2) as (port, report, process):
                peer = r.Peer(port)
                try:
                    peer.send(r.hello("standard"));peer.receive(lambda m:m.get("kind") == "welcome")
                finally:peer.close()
            with self.assertRaisesRegex(ValueError, "accelerated model time"):
                r.check_report(json.loads(report.read_text()))
        finally:r.SERVER = original

    def test_weak_schema_mutant_fails_the_live_safety_probe(self):
        original = r.SERVER;modified = self.folder / "weak.gd"
        text = original.read_text();needle = "data.size()==names.size() and names.all"
        self.assertIn(needle, text);modified.write_text(text.replace(needle, "names.all"))
        r.SERVER = modified
        try:
            with self.assertRaisesRegex(ValueError, "observation timed out"):
                r.safety(self.engine, self.folder / "weak-schema")
        finally:r.SERVER = original

    def test_stale_pack_identity_is_rejected(self):
        original = r.ROOT
        staged = self.folder / "prototype"
        for name in r.CONSUMERS:
            destination = staged / name;destination.parent.mkdir(parents=True, exist_ok=True);shutil.copyfile(original / name, destination)
        (staged / "dist").mkdir();shutil.copyfile(original / "dist/crossing-drill.pck", staged / "dist/crossing-drill.pck")
        with (staged / "combat.gd").open("a") as stream:stream.write("\n# Same rules, deliberately different identity.\n")
        r.ROOT = staged
        try:
            with r.server(self.engine, self.folder / "stale-pack", packed=True, seconds=2) as (port, report, process):
                peer = r.Peer(port)
                try:peer.send(r.hello("standard"));peer.receive(lambda m:m.get("kind") == "welcome")
                finally:peer.close()
            with self.assertRaisesRegex(ValueError, "identity mismatch"):r.check_report(json.loads(report.read_text()))
        finally:r.ROOT = original

    def test_recorded_model_time_cannot_exceed_server_steps(self):
        data = {"consumer_hashes": {name:r.digest(r.ROOT / name) for name in r.CONSUMERS if name != "tests/policy.gd"},
                "model":{"tick":121,"energy":100,"hp":5},"active_ticks":119}
        with self.assertRaisesRegex(ValueError, "accelerated model time"):r.check_report(data)

    def test_remote_client_waits_for_terminal_rejection_after_duplicate_states(self):
        listener = socket.socket();listener.bind(("127.0.0.1", 0));listener.listen(1);listener.settimeout(3)
        ready = threading.Event();release = threading.Event();errors = []
        def fake_authority():
            try:
                connection, _ = listener.accept();connection.settimeout(3)
                with connection:
                    stream = connection.makefile("rb")
                    json.loads(stream.readline())
                    state = {"v":1,"kind":"state","tick":1,"ack":-1,"quarantined":False,"state":{"mode":"won"}}
                    connection.sendall(r.canonical({"v":1,"kind":"welcome","session":"fixture"}) + r.canonical(state) + r.canonical(state))
                    request = json.loads(stream.readline())
                    if request.get("kind")!="hello":raise ValueError("Client omitted terminal reset probe")
                    ready.set()
                    if not release.wait(3):raise ValueError("Test terminal reply not released")
                    connection.sendall(r.canonical({"v":1,"kind":"reject","reason":"already_started"}) + r.canonical(state))
            except Exception as error:errors.append(error);ready.set()
        worker = threading.Thread(target=fake_authority, daemon=True);worker.start()
        output = self.folder / "terminal-client.json"
        with (self.folder / "terminal-client.log").open("w") as log:
            process = subprocess.Popen([self.engine,"--headless","--path",str(r.ROOT),"--script",str(r.CLIENT),"--",str(listener.getsockname()[1]),str(output),"Guardian","standard"], env=r.environment(self.folder),stdout=log,stderr=log)
            try:
                self.assertTrue(ready.wait(3));self.assertFalse(errors, str(errors));time.sleep(.1)
                self.assertIsNone(process.poll(), "Duplicate terminal snapshots must not bypass the reply")
                release.set();process.wait(timeout=4);self.assertEqual(process.returncode, 0)
                self.assertTrue(json.loads(output.read_text())["terminal_probe_confirmed"])
            finally:
                release.set();listener.close()
                if process.poll() is None:process.terminate();process.wait(timeout=3)
                worker.join(timeout=3)
        self.assertFalse(errors, str(errors))

    def test_remote_observer_does_not_reuse_an_older_matching_state(self):
        # A real socket pair transports states out of a previously unmatched predicate.
        peer = r.Peer.__new__(r.Peer);incoming, outgoing = socket.socketpair()
        peer.socket = incoming;incoming.settimeout(.1);peer.buffer = b"";peer.messages = [];peer.last_state_tick = -1
        try:
            outgoing.sendall(r.canonical({"kind":"state","tick":1,"quarantined":True}) +
                             r.canonical({"kind":"state","tick":2,"quarantined":False}))
            self.assertEqual(peer.state(lambda m:not m["quarantined"])["tick"], 2)
            outgoing.sendall(r.canonical({"kind":"state","tick":3,"quarantined":True}))
            self.assertEqual(peer.state(lambda m:m["quarantined"])["tick"], 3)
        finally:incoming.close();outgoing.close()


if __name__ == "__main__":unittest.main()
