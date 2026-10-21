#!/usr/bin/env python3
"""Measure bounded fixed-policy return outcomes using the actual Godot models.

Losses/timeouts are measurements. Invalid protocols, failed controls, changed source,
nonrepeatability and source/PCK disagreement are instrument errors and never published.
"""
import argparse
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from export_linux import ROOT, VERSION

PROBE = ROOT / "analysis/return_envelope.gd"
PROTOCOL = ROOT / "analysis/return-envelope.json"
CONSUMERS = ("combat.gd", "return_gate.gd", "route.gd", "fittings.gd", "data/fittings.json",
             "tests/policy.gd", "tests/gate_policy.gd")
AXES = {"approaches": ("steady", "riposte", "duelist"),
        "aids": ("none", "heal", "brace"), "strategies": ("work", "quiet", "ground")}
COUNTERS = {"blocks", "redirects", "dodges", "counters", "courier_hits", "player_hits", "rejected"}
MEASURES = {"mode", "ticks", "hp", "integrity", "energy", "min_energy", "grounded", "ward_disabled",
            "raised", "exit_reached", "first_winch_hit_tick", "first_work_tick", "ground_tick",
            "ground_interruptions", "counters", "end_reason", "trace_sha256"}
LIMIT = "Fixed policies at 60 Hz; initial idle delay is a controlled intervention, not human reaction time. Loss does not prove no feasible policy exists. Repetitions and deliveries are not independent participants. No enjoyment, balance, physical input, release-template or production-engine claim."


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_json(path):
    require(Path(path).stat().st_size <= 8_000_000, "JSON input exceeds bounded size")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "Duplicate JSON key: " + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("Nonfinite JSON number: " + value)
    def finite(value):
        number = float(value)
        require(math.isfinite(number), "Nonfinite JSON number")
        return number
    return json.loads(Path(path).read_text(), object_pairs_hook=unique, parse_constant=invalid, parse_float=finite)


def protocol(path):
    require(Path(path).stat().st_size <= 32_768, "Protocol exceeds bounded size")
    data = read_json(path)
    require(isinstance(data, dict) and set(data) == {"schema_version", "approaches", "outfits", "aids",
            "strategies", "delay_ticks", "repetitions", "max_ticks"}, "Unknown or missing protocol fields")
    require(type(data["schema_version"]) is int and data["schema_version"] == 1, "Unsupported protocol version")
    for axis in (*AXES, "outfits", "delay_ticks"):
        values = data[axis]
        require(isinstance(values, list) and 0 < len(values) <= 16, "Invalid axis: " + axis)
        if axis == "delay_ticks":
            require(all(type(v) is int and 0 <= v <= 600 for v in values), "Delay must be integer ticks in 0..600")
            require(values == sorted(set(values)), "Delays must be unique and increasing")
        else:
            require(all(isinstance(v, str) for v in values), "Axis must contain strings: " + axis)
            require(len(values) == len(set(values)), "Duplicate axis value: " + axis)
            if axis in AXES:
                require(all(v in AXES[axis] for v in values), "Unknown value: " + axis)
            else:
                require(all(re.fullmatch(r"[a-z][a-z0-9_]{0,31}", v) for v in values), "Invalid outfit identifier")
    require(type(data["repetitions"]) is int and 2 <= data["repetitions"] <= 3, "Use 2..3 repeatability takes")
    require(type(data["max_ticks"]) is int and 60 <= data["max_ticks"] <= 7200, "Budget must be integer ticks in 60..7200")
    require(max(data["delay_ticks"]) < data["max_ticks"], "Delay must leave observation time")
    require(len(cases(data)) <= 600, "Protocol exceeds 600 conditions")
    return data


def cases(data):
    return [dict(zip(("approach", "outfit", "aid", "strategy", "delay_ticks"), values)) for values in
            itertools.product(data["approaches"], data["outfits"], data["aids"], data["strategies"], data["delay_ticks"])]


def case_id(case):
    return "/".join(str(v) for v in case.values())


def invoke(command, env, timeout):
    process = subprocess.run(command, env=env, text=True, capture_output=True, timeout=timeout)
    log = process.stdout + process.stderr
    require(process.returncode == 0 and not any(s in log for s in ("SCRIPT ERROR:", "Parse Error:", "ERROR:")),
            "Native instrument failed: " + log[-2500:])
    return process.stdout.strip()


def measure(value, case, budget):
    require(isinstance(value, dict) and set(value) == MEASURES, "Incomplete measurement")
    require(value["mode"] in ("play", "won", "lost"), "Invalid terminal mode")
    for key in ("ticks", "hp", "integrity", "ground_interruptions"):
        require(type(value[key]) is int and value[key] >= 0, "Invalid measurement: " + key)
    require(0 < value["ticks"] <= budget, "Measurement exceeds observation budget")
    for key in ("energy", "min_energy"):
        require(type(value[key]) in (int, float) and math.isfinite(value[key]) and 0 <= value[key] <= 100,
                "Invalid resource observation")
    require(value["min_energy"] <= value["energy"], "Inconsistent minimum energy")
    for key in ("grounded", "ward_disabled", "exit_reached"):
        require(type(value[key]) is bool, "Invalid boolean observation")
    require(isinstance(value["raised"], list) and len(value["raised"]) == 2 and
            all(type(v) is bool for v in value["raised"]), "Invalid catch observation")
    for key in ("first_winch_hit_tick", "first_work_tick", "ground_tick"):
        require(type(value[key]) is int and -1 <= value[key] <= value["ticks"] and value[key] != 0,
                "Invalid event tick")
    require(isinstance(value["trace_sha256"], str) and re.fullmatch("[a-f0-9]{64}", value["trace_sha256"]), "Invalid trace identity")
    counts = value["counters"]
    require(isinstance(counts, dict) and set(counts) == COUNTERS and all(type(v) is int and v >= 0 for v in counts.values()),
            "Incomplete action counters")
    require(value["integrity"] <= (3 if case["aid"] == "brace" else 2), "Integrity exceeds prepared checkpoint")
    if value["grounded"]:
        require(value["ward_disabled"] and value["ground_tick"] > 0 and counts["counters"] == 0 and
                value["integrity"] <= (2 if case["aid"] == "brace" else 1), "Grounding cost/event invariant violated")
    if value["mode"] == "won":
        require(value["raised"] == [True, True] and value["exit_reached"] and value["hp"] > 0 and
                value["integrity"] > 0 and value["end_reason"] == "exit", "Success omitted objective or survival")
        if case["strategy"] == "ground":require(value["grounded"], "Ground policy success omitted actual grounding")
        if case["strategy"] == "quiet":require(value["ward_disabled"], "Quiet policy success omitted shutdown")
    elif value["mode"] == "lost":
        require((value["integrity"] == 0 and value["end_reason"] == "winch") or
                (value["hp"] == 0 and value["end_reason"] == "player"), "Loss lacks measured cause")
    else:
        require(value["ticks"] == budget and value["end_reason"] == "budget", "Live run is not a complete bounded observation")


def validate(raw, data):
    require(isinstance(raw, dict) and set(raw) == {"schema_version", "checks", "consumer_hashes", "checkpoints", "controls", "cases"},
            "Incomplete native report")
    require(raw["schema_version"] == 1, "Invalid native schema")
    labels = raw["checks"]
    require(labels["failed"] == [] and len(labels["passed"]) == 7 + 2 * len(data["approaches"]) * len(data["outfits"])
            and len(set(labels["passed"])) == len(labels["passed"]), "Failed or incomplete calibration controls")
    require(raw["consumer_hashes"] == {p: digest(ROOT / p) for p in CONSUMERS}, "Executed consumer identity mismatch")
    expected_entries = list(itertools.product(data["approaches"], data["outfits"]))
    require([(v["approach"], v["outfit"]) for v in raw["checkpoints"]] == expected_entries, "Missing/reordered arrival checkpoints")
    require(all(0 < v["hp"] < v["health_limit"] and 0 < v["ticks"] <= 4200 for v in raw["checkpoints"]), "Invalid wounded escort checkpoint")
    control = raw["controls"]
    require(set(control) == {"idle", "off_line", "ground"} and control["idle"]["mode"] == "lost" and control["idle"]["hp"] == 0 and
            control["idle"]["integrity"] == 2 and control["off_line"]["mode"] == "lost" and control["off_line"]["integrity"] == 0 and
            control["ground"]["mode"] == "won" and control["ground"]["grounded"] and control["ground"]["integrity"] == 1,
            "Failed positive/negative outcome controls")
    expected_cases = cases(data)
    require([v["id"] for v in raw["cases"]] == [case_id(c) for c in expected_cases], "Missing/reordered matrix conditions")
    outcomes = []
    for case, observed in zip(expected_cases, raw["cases"]):
        takes = observed["takes"]
        require(len(takes) == data["repetitions"], "Missing repeatability take")
        checkpoint = raw["checkpoints"][expected_entries.index((case["approach"], case["outfit"]))]
        for take in takes:
            measure(take, case, data["max_ticks"])
            require(take["hp"] <= checkpoint["health_limit"], "Health exceeds actual fitting limit")
        require(all(t == takes[0] for t in takes[1:]), "Nonrepeatable condition: " + observed["id"])
        outcomes.append({"id": observed["id"], **case, **takes[0]})
    return outcomes


def markdown(result):
    data = result["protocol"]
    rows = ["# Return encounter envelope", "", LIMIT, "", "## Actual observations", "",
            f"{len(result['outcomes'])} conditions, {data['repetitions']} identical takes per delivery; source/PCK equality required.", "",
            "W = policy won; L = policy lost; T = observation budget exhausted. Cells show HP / winch at stop. These are deterministic conditions, not success probabilities.", ""]
    by_id = {r["id"]: r for r in result["outcomes"]}
    for strategy in data["strategies"]:
        for aid in data["aids"]:
            rows += [f"## {strategy} / aid: {aid}", "", "| Approach / outfit | " + " | ".join(f"{d}/60 s idle" for d in data["delay_ticks"]) + " |",
                     "|---|" + "---|" * len(data["delay_ticks"])]
            for approach, outfit in itertools.product(data["approaches"], data["outfits"]):
                cells = []
                for delay in data["delay_ticks"]:
                    r = by_id[f"{approach}/{outfit}/{aid}/{strategy}/{delay}"]
                    cells.append(f"{dict(won='W', lost='L', play='T')[r['mode']]} {r['hp']} / {r['integrity']}")
                rows.append(f"| {approach} / {outfit} | " + " | ".join(cells) + " |")
            rows.append("")
    return "\n".join(rows)



def encode(result):
    header = {k: v for k, v in result.items() if k != "outcomes"}
    text = json.dumps(header, indent=2, sort_keys=True).rstrip()[:-1].rstrip()
    rows = ",\n".join("    " + json.dumps(row, sort_keys=True) for row in result["outcomes"])
    return text + ',\n  "outcomes": [\n' + rows + '\n  ]\n}\n'

def evaluate(output, protocol_path=PROTOCOL, godot="godot", pack=None, compare=None, report=None, timeout=180):
    data = protocol(protocol_path)
    require(type(timeout) is int and 1 <= timeout <= 300, "Timeout must be 1..300 seconds")
    output = Path(output).resolve();report = Path(report).resolve() if report else None
    protected = {Path(protocol_path).resolve(), PROBE.resolve(), Path(__file__).resolve(), Path(pack or ROOT / "dist/crossing-drill.pck").resolve()}
    for target in (output, report):
        if target:
            require(target not in protected and ROOT not in target.parents, "Output must not replace prototype inputs")
    require(output != report, "JSON and Markdown outputs must differ")
    engine = shutil.which(godot)
    require(engine is not None, "Godot executable unavailable")
    def identities():
        return {"protocol_sha256": digest(protocol_path), "probe_sha256": digest(PROBE),
                "runner_sha256": digest(__file__), "pack_sha256": digest(pack or ROOT / "dist/crossing-drill.pck"),
                "consumer_hashes": {p: digest(ROOT / p) for p in CONSUMERS}}
    before = identities()
    with tempfile.TemporaryDirectory(prefix="return-envelope-") as folder:
        scratch = Path(folder);env = os.environ.copy()
        for key in ("CROSSING_PROFILE", "CROSSING_CONTROLS", "CROSSING_CAPTURE"):env.pop(key, None)
        require(invoke([engine, "--version"], env, 10) == VERSION, "Pinned Godot 4.6.3 standard editor required")
        configuration = scratch / "protocol.json"
        configuration.write_text(json.dumps(data))
        native = []
        for name, location in [("source", ["--path", str(ROOT)]), ("pack", ["--main-pack", str(pack or ROOT / "dist/crossing-drill.pck")])]:
            env.update({k: str(scratch / name / k) for k in ("XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME")})
            path = scratch / (name + ".json")
            invoke([engine, "--headless", *location, "--script", str(PROBE), "--", str(configuration), str(path)], env, timeout)
            raw = read_json(path);validate(raw, data);native.append(raw)
        require(native[0] == native[1], "Source/PCK observations differ")
        require(identities() == before, "Inputs changed during execution")
        result = {"schema_version": 1, "runtime": VERSION, "protocol": data, "limitations": LIMIT,
                  "identities": before,
                  "checks": {"passed": len(native[0]["checks"]["passed"]), "failed": 0},
                  "checkpoints": native[0]["checkpoints"], "controls": native[0]["controls"],
                  "outcomes": validate(native[0], data)}
        if compare:require(result == read_json(compare), "Envelope comparison changed")
        rendered = markdown(result) if report else None
        pending = []
        try:
            for target, content in [(output, encode(result)), (report, rendered)]:
                if target is None:continue
                target.parent.mkdir(parents=True, exist_ok=True)
                require(not target.is_dir(), "Output is a directory")
                with tempfile.NamedTemporaryFile(mode="w", dir=target.parent, prefix=".envelope-", delete=False) as stream:
                    pending.append((Path(stream.name), target));stream.write(content)
            for temporary, target in pending:temporary.replace(target)
        finally:
            for temporary, _ in pending:temporary.unlink(missing_ok=True)
    print(f"PASS: {len(result['outcomes'])} conditions; repeated takes and source/PCK identical; all losses retained")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True);parser.add_argument("--protocol", type=Path, default=PROTOCOL)
    parser.add_argument("--godot", default="godot");parser.add_argument("--pack", type=Path);parser.add_argument("--compare", type=Path)
    parser.add_argument("--report", type=Path);parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    try:evaluate(args.output, args.protocol, args.godot, args.pack, args.compare, args.report, args.timeout)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:parser.exit(1, f"FAIL: {error}\n")
