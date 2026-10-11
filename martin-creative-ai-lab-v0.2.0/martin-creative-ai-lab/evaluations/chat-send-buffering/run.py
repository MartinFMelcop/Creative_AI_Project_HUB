#!/usr/bin/env python3
"""Export one practice task and check client artifacts with evaluator-owned tests."""

import argparse
import hashlib
import json
import os
import re
import signal
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

TASK = "EVAL-001"
VERSION = "0.1.4"
TASK_VERSION = "0.1.0"
BASELINE = "66041e7fdd7687ee21099f95129dff41933c74dd"
SUITE_COMMIT = "911bf789e31dc2b1df9586a894e37312375771f3"
HERE = Path(__file__).resolve().parent
LAB = HERE.parents[1]
PROJECT = LAB / "projects/realtime-integration-lab"
PREFIX = "martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/projects/realtime-integration-lab"
FILES = (".node-version", "package.json", "package-lock.json", "server.cjs",
         "public/index.html", "public/style.css", "public/client.js")
TESTS = ("tests/browser.test.cjs", "tests/protocol.test.cjs")
TOTAL = 17


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_bytes(commit, path):
    return subprocess.run(["git", "show", f"{commit}:{PREFIX}/{path}"], cwd=LAB,
                          capture_output=True, check=True).stdout


def starter():
    files = {name: git_bytes(BASELINE, name) for name in FILES}
    files["BRIEF.md"] = (HERE / "BRIEF.md").read_bytes()
    manifest = {"task": TASK, "version": TASK_VERSION, "baseline_commit": BASELINE,
                "files": {name: sha(data) for name, data in files.items()}}
    files["task-manifest.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    return files


def prepare(destination):
    """Create a fresh allowlisted workspace; never overlay an existing directory."""
    files = starter()
    destination.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return {"task": TASK, "version": TASK_VERSION, "runner_version": VERSION,
            "workspace": str(destination),
            "exported_files": sorted(files), "baseline_commit": BASELINE}


def read_submission(workspace):
    expected = starter()
    if not workspace.is_dir() or workspace.is_symlink():
        raise ValueError("Submission must be a regular directory")
    for directory, dirs, files in os.walk(workspace):
        root = Path(directory)
        # npm installation is permitted; its outputs are never evaluator inputs.
        if root == workspace and "node_modules" in dirs:
            dirs.remove("node_modules")
        for name in dirs:
            path = root / name
            if path.is_symlink() or path.relative_to(workspace).as_posix() != "public":
                raise ValueError(f"Unexpected directory: {path.relative_to(workspace)}")
        for name in files:
            path = root / name
            relative = path.relative_to(workspace).as_posix()
            if path.is_symlink() or relative not in expected:
                raise ValueError(f"Unexpected or linked file: {relative}")
    for name, data in expected.items():
        path = workspace / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Missing or linked file: {name}")
        if name != "public/client.js" and path.read_bytes() != data:
            raise ValueError(f"Out-of-scope change: {name}")
    return (workspace / "public/client.js").read_bytes()


def classify_tap(output, returncode):
    counts = {}
    for key in ("tests", "pass", "fail", "cancelled", "skipped", "todo"):
        matches = re.findall(rf"^# {key} (\d+)\s*$", output, re.M)
        if len(matches) != 1:
            return "inconclusive", counts
        counts[key] = int(matches[0])
    complete = (counts["tests"] == TOTAL and
                counts["pass"] + counts["fail"] == TOTAL and
                all(counts[key] == 0 for key in ("cancelled", "skipped", "todo")))
    if not complete or returncode not in (0, 1):
        return "inconclusive", counts
    if counts["fail"]:
        return ("rejected" if returncode == 1 else "inconclusive"), counts
    return ("accepted" if returncode == 0 else "inconclusive"), counts


def invoke(command, cwd, environment, timeout):
    started = time.monotonic()
    record = {"command": command, "exit_code": None, "stdout": "", "stderr": "",
              "timeout_seconds": timeout, "timed_out": False, "launch_error": None,
              "capture_complete": True, "termination_strategy": None}
    try:
        process = subprocess.Popen(command, cwd=cwd, env=environment,
                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   encoding="utf-8", errors="replace",
                                   start_new_session=os.name == "posix")
    except OSError as exc:
        record["launch_error"] = str(exc)
        record["elapsed_seconds"] = round(time.monotonic() - started, 3)
        return record

    def terminate(force=False):
        try:
            if os.name == "posix":
                # Only this command's private group; unrelated processes are excluded.
                os.killpg(process.pid, signal.SIGKILL if force else signal.SIGTERM)
            elif force:
                process.kill()
            else:
                process.terminate()
        except ProcessLookupError:
            pass

    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        record["timed_out"] = True
        record["termination_strategy"] = "posix_process_group" if os.name == "posix" else "direct_process"
        terminate()
        try:
            stdout, stderr = process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            terminate(force=True)
            try:
                stdout, stderr = process.communicate(timeout=1)
            except subprocess.TimeoutExpired as exc:
                # A descendant outside the group can retain pipes. Do not wait forever.
                def text(value):
                    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""
                stdout, stderr = text(exc.stdout), text(exc.stderr)
                record["capture_complete"] = False
                process.stdout.close()
                process.stderr.close()
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
        finally:
            # The parent can exit while an inherited child closes its pipes and lives on.
            terminate(force=True)
    record.update(exit_code=process.poll(), stdout=stdout, stderr=stderr,
                  elapsed_seconds=round(time.monotonic() - started, 3))
    return record


def check(workspace):
    record = {"schema_version": 1, "task": TASK, "task_version": TASK_VERSION,
              "runner_version": VERSION,
              "started_at": datetime.now(timezone.utc).isoformat(),
              "run_kind": "artifact_check", "status": "inconclusive",
              "baseline_commit": BASELINE, "suite_commit": SUITE_COMMIT,
              "runner_sha256": sha(Path(__file__).read_bytes()), "commands": [],
              "candidate_model": None, "score": None}
    try:
        artifact = read_submission(workspace)
    except ValueError as exc:
        record.update(status="rejected", reason=str(exc), gate="submission_scope")
        return record
    except (OSError, subprocess.CalledProcessError) as exc:
        record.update(reason=str(exc), gate="source_availability")
        return record
    record["artifact_sha256"] = sha(artifact)
    environment = os.environ.copy()
    environment.pop("CHAT_TEST_URL", None)
    environment.pop("CHAT_TEST_CLIENT_PATH", None)
    try:
        # Pin the evaluator runtime and suite; later changes require recalibration.
        trusted = ("server.cjs", "public/index.html", "public/style.css",
                   "package.json", "package-lock.json", *TESTS)
        record["evaluator_artifacts"] = {}
        for name in trusted:
            data = (PROJECT / name).read_bytes()
            if data != git_bytes(SUITE_COMMIT, name):
                raise ValueError(f"Evaluator changed; recalibration required: {name}")
            record["evaluator_artifacts"][name] = sha(data)
        with tempfile.TemporaryDirectory(prefix="p02-client-") as scratch:
            client = Path(scratch) / "client.js"
            client.write_bytes(artifact)
            syntax = invoke(["node", "--check", str(client)], PROJECT, environment, 15)
            record["commands"].append(syntax)
            if syntax["timed_out"] or syntax["launch_error"]:
                record.update(gate="client_syntax", reason="Syntax check did not complete")
                return record
            if syntax["exit_code"] != 0:
                # Node also fails for runtime options, preload errors and signals.
                # Reject only a complete parser diagnostic naming our client copy.
                client_error = (syntax["exit_code"] == 1 and
                                syntax["capture_complete"] and
                                re.search(rf"^{re.escape(str(client))}:\d+\s*$",
                                          syntax["stderr"], re.M) and
                                re.search(r"^SyntaxError:", syntax["stderr"], re.M))
                record.update(status="rejected" if client_error else "inconclusive",
                              gate="client_syntax",
                              reason="Submitted client is not valid JavaScript" if client_error
                              else "Syntax checker failed without a client parser diagnostic")
                return record
            probe = """
const { chromium } = require('playwright-core');
if (Number(process.versions.node.split('.')[0]) < 22) process.exit(2);
(async () => {
  const browser = await chromium.launch({
    executablePath: process.env.CHROMIUM_PATH || '/usr/bin/chromium',
    headless: true, args: ['--no-sandbox'],
  });
  console.log(JSON.stringify({ node: process.version, chromium: browser.version(),
    playwright: require('playwright-core/package.json').version,
    socket_io: require('socket.io/package.json').version }));
  await browser.close();
})().catch(error => { console.error(error.message); process.exit(2); });
"""
            ready = invoke(["node", "-e", probe], PROJECT, environment, 20)
            record["commands"].append(ready)
            if ready["timed_out"] or ready["launch_error"] or ready["exit_code"]:
                record.update(gate="environment", reason="Browser/dependency preflight failed")
                return record
            record["environment"] = json.loads(ready["stdout"])
            environment["CHAT_TEST_CLIENT_PATH"] = str(client)
            tests = invoke(["node", "--test", "--test-reporter=tap", *TESTS],
                           PROJECT, environment, 180)
            record["commands"].append(tests)
            record["status"], record["counts"] = classify_tap(tests["stdout"], tests["exit_code"])
            record["gate"] = "behavior_and_regressions"
            record["failed_checks"] = re.findall(r"^not ok \d+ - (.+)$", tests["stdout"], re.M)
            if tests["timed_out"] or tests["launch_error"]:
                record.update(status="inconclusive", reason="Behavior checks did not complete")
    except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        record.update(status="inconclusive", gate="execution", reason=str(exc))
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("prepare", help="Create a new candidate workspace")
    export.add_argument("workspace", type=Path)
    evaluate = commands.add_parser("check", help="Check only a submitted client artifact")
    evaluate.add_argument("workspace", type=Path)
    evaluate.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    workspace = args.workspace.absolute()
    try:
        if args.command == "prepare":
            print(json.dumps(prepare(workspace), indent=2))
            return 0
        result_path = args.result.absolute()
        if result_path.exists() or result_path.resolve().is_relative_to(workspace.resolve()):
            raise ValueError("Result must be a new file outside the candidate workspace")
        record = check(workspace)
        result_path.parent.mkdir(parents=True, exist_ok=True)
        with result_path.open("x", encoding="utf-8") as output:
            json.dump(record, output, indent=2)
            output.write("\n")
        print(json.dumps({"status": record["status"], "result": str(result_path),
                          "counts": record.get("counts"), "reason": record.get("reason")}, indent=2))
        return {"accepted": 0, "rejected": 1, "inconclusive": 2}[record["status"]]
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(2, f"Task error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
