#!/usr/bin/env python3
"""Exercise the real compiled terminal workflow; all input is synthetic."""
import csv
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
DLL = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "Cli/bin/Release/net10.0/eclipse.dll"
DOTNET = os.environ.get("ECLIPSE_DOTNET", "dotnet")

with tempfile.TemporaryDirectory(prefix="eclipse-cli-") as scratch:
    cwd = Path(scratch)
    def run(*args, text=None, success=True):
        result = subprocess.run([DOTNET, str(DLL), *args], input=text, text=True,
                                cwd=cwd, capture_output=True, timeout=60)
        assert (result.returncode == 0) == success, result.stdout + result.stderr
        return result

    save = cwd / "partial.json"
    first = run("play", "--seed", "1", text=f"999\nhint\nsave {cwd}\nsave {save}\nquit\n")
    assert "Choose a displayed plan; nothing changed." in first.stdout
    assert "Collector suggestion:" in first.stdout and save.is_file()
    assert "Save failed:" in first.stdout and "Match is still active and unchanged." in first.stdout
    assert len(json.loads(save.read_text())["actions"]) == 3  # Other seats act before Vaelis.
    resumed = run("play", "--load", str(save), text="auto\n" * 40)
    assert "RESULT:" in resumed.stdout and "Assisted turn:" in resumed.stdout
    run("demo", "--seed", "1", "--out", str(cwd / "demo"))
    replay = run("replay", "--load", str(cwd / "demo/journal.json"))
    assert resumed.stdout.split("RESULT:")[-1] == replay.stdout.split("RESULT:")[-1]
    forged = json.loads(save.read_text()); forged["actions"][0]["destination"] = 99
    save.write_text(json.dumps(forged))
    assert "unavailable action" in run("play", "--load", str(save), success=False).stderr
    run("play", "--rules", str(ROOT / "rules/baseline.json"), "--load", str(save), success=False)
    result = run("compare", "--runs", "4", "--seed", "0", "--variant",
                 str(ROOT / "rules/expensive-seals.json"), "--out", str(cwd / "compare"))
    summary = json.loads((cwd / "compare/summary.json").read_text())
    assert summary["matchesPerScenario"] == 16 and summary["seeds"] == 4
    rows = list(csv.DictReader((cwd / "compare/matches.csv").open()))
    assert len(rows) == 128
    for scenario in ["baseline", "variant"]:
        for seed in range(4):
            for policy in ["collector", "keeper", "opportunist", "worker"]:
                seats = {int(r["seat"]) for r in rows if r["scenario"] == scenario and
                         int(r["seed"]) == seed and r["policy"] == policy}
                assert seats == {0, 1, 2, 3}
    for scenario in summary["scenarios"]:
        assert abs(sum(scenario["winCredits"].values()) - scenario["matches"]) < 1e-9
    run("compare", "--runs", "0", "--variant", str(ROOT / "rules/expensive-seals.json"), success=False)
    run("demo", "--unknown", "value", success=False)
    print(json.dumps({"workflow": "real compiled CLI", "input": "synthetic", "passed": [
        "numbered-plan rejection/hint/atomic save", "resume to same complete result",
        "independent replay", "invalid journal/option rejection", "common-seed four-seat comparison/CSV"
    ]}))
