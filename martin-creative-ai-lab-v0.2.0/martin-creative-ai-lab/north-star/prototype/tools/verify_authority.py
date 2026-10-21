#!/usr/bin/env python3
"""Run actual loopback peers against the unchanged North Star combat model.

Wall-clock samples are observations, not deterministic golden traces or latency claims.
A comparison checks source identity and contract checks, not identical packet timing.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time

from export_linux import ROOT, VERSION

SERVER = ROOT / "authority/server.gd"
CLIENT = ROOT / "authority/client.gd"
CONSUMERS = ("combat.gd", "route.gd", "fittings.gd", "data/fittings.json", "tests/policy.gd", "project.godot")


def require(value, message):
    if not value:raise ValueError(message)


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(data):return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + b"\n"


class Peer:
    def __init__(self, port):
        self.socket = socket.create_connection(("127.0.0.1", port), timeout=3)
        self.socket.settimeout(.2);self.buffer = b"";self.messages = [];self.last_state_tick = -1

    def send(self, data):self.socket.sendall(canonical(data))

    def receive(self, predicate, timeout=3):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            for i, message in enumerate(self.messages):
                if predicate(message):return self.messages.pop(i)
            try:data = self.socket.recv(65536)
            except socket.timeout:continue
            require(data, "Authority connection closed before observation")
            self.buffer += data
            require(len(self.buffer) <= 100_000, "Unbounded authority output")
            while b"\n" in self.buffer:
                line, self.buffer = self.buffer.split(b"\n", 1)
                self.messages.append(json.loads(line))
                require(len(self.messages) <= 512, "Unbounded unmatched authority messages")
        raise ValueError("Authority observation timed out")

    def state(self, condition=lambda value: True):
        message = self.receive(lambda m: m.get("kind") == "state" and m["tick"] > self.last_state_tick and condition(m))
        self.last_state_tick = message["tick"]
        self.messages = [m for m in self.messages if m.get("kind") != "state" or m["tick"] > self.last_state_tick]
        return message

    def close(self):self.socket.close()


def environment(folder):
    env = os.environ.copy()
    for key in ("CROSSING_PROFILE", "CROSSING_CONTROLS", "CROSSING_CAPTURE"):env.pop(key, None)
    env.update({key: str(folder / key) for key in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME")})
    return env


@contextmanager
def server(engine, folder, packed=False, seconds=12, port=None):
    folder.mkdir(parents=True, exist_ok=True)
    if port is None:
        with socket.socket() as chosen:
            chosen.bind(("127.0.0.1", 0));port = chosen.getsockname()[1]
    require(type(port) is int and 1024 <= port <= 65535, "Invalid selected loopback port")
    report = folder / "server.json";log_path = folder / "server.log"
    location = ["--main-pack", str(ROOT / "dist/crossing-drill.pck")] if packed else ["--path", str(ROOT)]
    with log_path.open("w") as log:
        process = subprocess.Popen([engine, "--headless", *location, "--script", str(SERVER), "--", str(port), str(report), str(seconds)],
                                   env=environment(folder), stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 6
            while time.monotonic() < deadline:
                text = log_path.read_text()
                if f"AUTHORITY_READY {port}" in text:break
                require(process.poll() is None, "Authority startup failed: " + text[-2000:])
                time.sleep(.02)
            else:raise ValueError("Authority startup timed out")
            yield port, report, process
            try:process.wait(timeout=seconds + 3)
            except subprocess.TimeoutExpired as error:raise ValueError("Authority shutdown timed out") from error
            text = log_path.read_text()
            require(process.returncode == 0 and not any(s in text for s in ("SCRIPT ERROR:", "Parse Error:", "ERROR:")), "Native authority error: " + text[-2000:])
            require(report.is_file(), "Authority omitted its final observation")
        finally:
            if process.poll() is None:
                process.terminate()
                try:process.wait(timeout=3)
                except subprocess.TimeoutExpired:process.kill();process.wait()


def hello(outfit="riveted"):
    return {"v": 1, "kind": "hello", "role": "Guardian", "style": "Steady", "outfit": outfit}


def intent(session, sequence, **changes):
    return {"v": 1, "kind": "input", "session": session, "seq": sequence, "move": [0, 0], "aim": [1000, 0],
            "guard": False, "feint": False, "step": False, "strike": False, **changes}


def check_report(data):
    expected = {name: digest(ROOT / name) for name in CONSUMERS if name != "tests/policy.gd"}
    require(data["consumer_hashes"] == expected, "Executed model identity mismatch")
    require(data["model"]["tick"] <= data["active_ticks"] + 1, "Client traffic accelerated model time")
    require(0 <= data["model"]["energy"] <= 100 and data["model"]["hp"] <= 6, "Authority resource bounds failed")


def safety(engine, folder, packed=False):
    checks = []
    def check(condition, label):
        require(condition, label);checks.append(label)
    with server(engine, folder, packed, seconds=10) as (port, report, process):
        peer = Peer(port)
        try:
            invalid = [b'{"kind":"hello","outfit":"standard","role":"Duelist","role":"Guardian","style":"Steady","v":1}\n',
                       b'{"v":NaN}\n', b'\xff\n', b'{"kind":\n', b'{"v":1e999}\n']
            for frame in invalid:
                peer.socket.sendall(frame)
                check(peer.receive(lambda m:m.get("kind") == "reject")["reason"] == "frame", "Reject malformed/ambiguous frame " + str(len(checks)))
            for data in [{**hello(), "hp": 999}, {**hello(), "v": True}, {**hello(), "role": "Administrator"},
                         {**hello(), "style": "none"}, {**hello(), "outfit": "unknown"}]:
                peer.send(data);check(peer.receive(lambda m:m.get("kind") == "reject")["ack"] == -1, "Invalid hello cannot begin or sequence the model " + str(len(checks)))
            frame = canonical(hello())
            peer.socket.sendall(frame[:13]);time.sleep(.03);peer.socket.sendall(frame[13:])
            welcome = peer.receive(lambda m:m.get("kind") == "welcome");session = welcome["session"]
            initial = peer.state()
            check(initial["state"]["hp"] == 6 and initial["state"]["outfit"]["id"] == "riveted", "Fragmented hello initializes server-owned catalog values")
            peer.send(intent(session, 0));state = peer.state(lambda m:m["ack"] == 0)
            check(not state["quarantined"], "Released initial intent arms the connection")
            for changes in [{"hp": 999}, {"delta": 99}, {"player": [999999, 999999]}, {"role": "Duelist"}, {"outfit": "trail"},
                            {"move": [1001, 0]}, {"move": [True, 0]}, {"move": [0, 0, 0]}, {"move": [0.5, 0]},
                            {"aim": None}, {"guard": "true"}, {"session": {}}, {"session": "obsolete"},
                            {"seq": 0}, {"seq": 65}, {"seq": True}, {"seq": -1}, {"seq": 1.5}]:
                data = intent(session, 1);data.update(changes);peer.send(data)
                rejection = peer.receive(lambda m:m.get("kind") == "reject")
                check(rejection["ack"] == 0, "Reject forged state/sequence/schema without consuming input " + str(len(checks)))
            peer.send(intent(session, 1));state = peer.state(lambda m:m["ack"] == 1)
            check(state["state"]["hp"] <= 6 and state["state"]["role"] == "Guardian", "Rejected mutations preserve server ownership")
            first_tick = state["state"]["tick"];first_clock = state["tick"]
            frames = b"".join(canonical(intent(session, seq, move=[1000, 1000])) for seq in range(2, 102))
            peer.socket.sendall(frames)
            state = peer.state(lambda m:m["rejected"].get("rate", 0) > 0 and m["ack"] >= 50)
            check(state["state"]["tick"] - first_tick <= state["tick"] - first_clock + 1, "Burst cannot advance model faster than server physics")
            check(state["accepted"] < 102, "At most one sequenced intent is accepted per physics tick")
            check(50 <= state["state"]["player"][0] <= 1102 and 185 <= state["state"]["player"][1] <= 645, "Quantized diagonal input stays within actual movement/field rules")
            state = peer.state(lambda m:m["quarantined"] and m["stale_clears"] > 0)
            check(not state["state"]["guard"], "Silence clears held actions and requires release")
            seq = state["ack"] + 1;peer.send(intent(session, seq, guard=True))
            check(peer.receive(lambda m:m.get("kind") == "reject" and m.get("reason") == "release_required")["reason"] == "release_required", "Stale held guard cannot rearm without release")
            peer.send(intent(session, seq + 1));state = peer.state(lambda m:m["ack"] == seq + 1)
            peer.send(intent(session, seq + 2, guard=True, step=True, move=[0, -1000]))
            state = peer.state(lambda m:m["ack"] == seq + 2)
            check(state["state"]["counters"]["dodges"] == 1, "A fresh press enters the actual paid step once")
            start = state["tick"];sequence = state["ack"] + 1
            while state["tick"] - start < 9:
                peer.send(intent(session, sequence, guard=True, step=True));sequence += 1
                state = peer.state(lambda m:m["ack"] >= sequence - 1)
            check(state["state"]["counters"]["dodges"] == 1, "Repeated held packets cannot repeat an edge action")
            peer.send(hello("trail"));peer.receive(lambda m:m.get("kind") == "reject" and m["reason"] == "already_started")
            check(True, "Connected client cannot reset or change loadout")
            other = Peer(port)
            try:
                try:message = other.receive(lambda m:True, timeout=1)
                except (ValueError, ConnectionResetError):message = {"kind": "closed"}
                check(message.get("kind") != "welcome", "Second connection cannot become authority owner")
            finally:other.close()
        finally:peer.close()
        time.sleep(.1)
        other = Peer(port)
        try:
            try:message = other.receive(lambda m:True, timeout=1)
            except (ValueError, ConnectionResetError):message = {"kind": "closed"}
            check(message.get("kind") != "welcome", "Disconnect cannot mint a new prepared session")
        finally:other.close()
    data = json.loads(report.read_text());check_report(data)
    check(data["disconnected"] and data["quarantined"] and not data["guard"], "Disconnect fails closed without pausing the server clock")
    return {"checks": checks, "sample": {k:data[k] for k in ("model", "accepted", "rejected", "stale_clears", "server_ticks", "active_ticks")}}


def journey(engine, folder, role, packed=False):
    with server(engine, folder, packed, seconds=65) as (port, report, process):
        output = folder / "client.json"
        result = subprocess.run([engine, "--headless", "--path", str(ROOT), "--script", str(CLIENT), "--", str(port), str(output), role, "standard"],
                                env=environment(folder / "client"), capture_output=True, text=True, timeout=66)
        require(result.returncode == 0 and not any(s in result.stdout + result.stderr for s in ("SCRIPT ERROR:", "Parse Error:", "ERROR:")),
                "Remote journey failed: " + (result.stdout + result.stderr)[-2000:])
        require(output.is_file(), "Remote client omitted its report")
    client = json.loads(output.read_text());authority = json.loads(report.read_text());check_report(authority)
    require(client["state"]["mode"] == authority["model"]["mode"] == "won" and authority["model"]["hp"] > 0 and authority["model"]["cargo"] > 0,
            "Remote player did not reach a living escort win")
    require(client["terminal_probe_sent"] and client["terminal_probe_confirmed"] and "already_started" in client["rejects"], "Terminal client reset was not rejected")
    require(authority["model"]["role"] == role and authority["model"]["courier_x"] >= 1000, "Remote model ownership/goal failed")
    return {"role": role, "mode": authority["model"]["mode"], "hp": authority["model"]["hp"], "cargo": authority["model"]["cargo"],
            "model_ticks": authority["model"]["tick"], "server_ticks": authority["active_ticks"], "accepted": authority["accepted"],
            "snapshots": client["snapshots"], "terminal_reset_rejected": True, "counters": authority["model"]["counters"]}


def verify(output, godot="godot", compare=None):
    engine = shutil.which(godot);require(engine is not None, "Godot executable unavailable")
    inputs = {"server": digest(SERVER), "client": digest(CLIENT), "runner": digest(__file__),
              "pack": digest(ROOT / "dist/crossing-drill.pck"), "consumers": {name:digest(ROOT / name) for name in CONSUMERS}}
    output = Path(output).resolve()
    require(ROOT not in output.parents, "Do not overwrite prototype inputs")
    with tempfile.TemporaryDirectory(prefix="north-star-authority-") as temporary:
        scratch = Path(temporary)
        version = subprocess.run([engine, "--version"], env=environment(scratch), capture_output=True, text=True, timeout=10)
        require(version.returncode == 0 and version.stdout.strip() == VERSION, "Pinned standard Godot 4.6.3 required")
        observations = {}
        for label, packed in (("source", False), ("pack", True)):
            observed = safety(engine, scratch / label / "safety", packed)
            observed["journeys"] = [journey(engine, scratch / label / role, role, packed) for role in ("Guardian", "Duelist")]
            observations[label] = observed
        require(observations["source"]["checks"] == observations["pack"]["checks"], "Delivery safety contracts differ")
        require({"server": digest(SERVER), "client": digest(CLIENT), "runner": digest(__file__), "pack": digest(ROOT / "dist/crossing-drill.pck"),
                 "consumers": {name:digest(ROOT / name) for name in CONSUMERS}} == inputs, "Authority inputs changed during execution")
        contract = {"schema_version": 1, "runtime": VERSION, "identities": inputs, "checks": {"passed": len(observed["checks"]), "failed": 0},
                    "safety_controls": observed["checks"], "remote_journeys_per_delivery": 2,
                    "scope": "Loopback TCP, one authoritative escort session, server physics and real combat model. No shipped multiplayer client, account/authentication, WAN/TLS, reconnect, persistence, load capacity, production-engine or MMO readiness claim."}
        if compare:
            previous = json.loads(Path(compare).read_text());require(previous["contract"] == contract, "Authority contract/source comparison changed")
        result = {"contract": contract, "observations": observations,
                  "observation_limits": "Actual packet/physics schedules vary. Recorded samples are not exact golden traces, independent players, a latency benchmark or a capacity estimate."}
        output.parent.mkdir(parents=True, exist_ok=True);output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(f"PASS: {len(observed['checks'])} live authority controls per delivery and four remote living escort wins")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--godot", default="godot");parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    try:verify(args.output, args.godot, args.compare)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:parser.exit(1, f"FAIL: {error}\n")
