#!/usr/bin/env python3
"""Inspect the default release scene using bounded XTest keys, not a test scene."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from check_linux import require
from export_linux import DEFAULT
from verify_linux import unpack, environment
from verify_routes_input import C, X, T, window, ROOT, x_error, x_errors


def verify(archive, output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    server = game = display = None
    x_errors.clear()
    old_handler = X.XSetErrorHandler(C.cast(x_error, C.c_void_p))
    with tempfile.TemporaryDirectory(prefix="crossing-player-input-") as folder:
        scratch = Path(folder)
        executable, package = unpack(archive, scratch / "download")
        env = environment(scratch)
        number = next((n for n in range(210,230) if not Path(f"/tmp/.X11-unix/X{n}").exists() and not Path(f"/tmp/.X{n}-lock").exists()), None)
        require(number is not None, "No unused local display")
        env["DISPLAY"] = f":{number}"
        capture = scratch / "capture.png"
        env["CROSSING_CAPTURE"] = str(capture)
        observations = {}
        with (output / "display.log").open("w") as log:
            try:
                xorg = shutil.which("Xorg")
                require(xorg, "Xorg executable unavailable")
                server = subprocess.Popen([xorg, env["DISPLAY"], "-config", str(ROOT / "tests/dummy-display.conf"),
                                           "-logfile", str(scratch / "Xorg.log"), "-noreset", "-nolisten", "tcp"], stdout=log, stderr=log)
                for _ in range(60):
                    display = X.XOpenDisplay(env["DISPLAY"].encode())
                    if display:
                        break
                    time.sleep(.05)
                require(display, "Owned display unavailable")
                def key(name, down):
                    code = X.XKeysymToKeycode(display, X.XStringToKeysym(name.encode()))
                    T.XTestFakeKeyEvent(display, code, down, 0)
                    X.XFlush(display)
                def tap(name):
                    key(name, True); time.sleep(.05); key(name, False); time.sleep(.10)
                def shot(label):
                    receipt = Path(str(capture) + ".json")
                    prior = receipt.stat().st_mtime_ns if receipt.exists() else 0
                    tap("F12")
                    for _ in range(100):
                        if receipt.exists() and receipt.stat().st_mtime_ns != prior:
                            try:
                                value = json.loads(receipt.read_text())
                            except json.JSONDecodeError:
                                time.sleep(.03); continue
                            shutil.copyfile(capture, output / (label + ".png"))
                            (output / (label + ".json")).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
                            return value
                        time.sleep(.03)
                    raise ValueError("Release did not acknowledge capture: " + label)
                for fresh in (False, True):
                    game = subprocess.Popen([str(executable), "--audio-driver", "Dummy"], cwd=scratch, env=env, stdout=log, stderr=log)
                    target = None
                    # The pinned release exposes a "Godot" splash before naming
                    # the actual scene. A measured cold startup took sixteen seconds.
                    for _ in range(600):
                        target = window(display)
                        if target:
                            break
                        require(game.poll() is None, "Release exited before its window")
                        time.sleep(.05)
                    require(target, "Release window unavailable")
                    X.XSetInputFocus(display, target, 1, 0); X.XSync(display, False); time.sleep(.4)
                    initial = shot("fresh" if fresh else "title")
                    require(initial["mode"] == "title" and initial["tick"] == 0, "Default release scene did not start at selection")
                    if fresh:
                        require(initial["character_look"]["applied"] == {"skin":1,"hair":1,"dye":1}, "Default-path appearance did not survive actual restart")
                        observations["fresh_process_retained"] = initial["character_look"]["applied"]
                    else:
                        tap("F3")
                        for name in ("Right", "Down", "Right", "Down", "Right"):
                            tap(name)
                        draft = shot("editor")
                        require(draft["character_look"]["draft"] == {"skin":1,"hair":1,"dye":1}, "Release editor did not receive native keys")
                        tap("Return"); applied = shot("applied")
                        require(not applied["keepsakes"]["dirty"] and applied["character_look"]["applied"] == draft["character_look"]["draft"], "Release apply did not save")
                        tap("2"); tap("Return"); started = shot("started")
                        key("d", True); time.sleep(.25); key("d", False); moved = shot("moved")
                        require(moved["mode"] == "play" and moved["role"] == "Duelist" and moved["player_position"][0] > started["player_position"][0], "Release movement was not acknowledged")
                        tap("Escape"); paused = shot("paused")
                        require(paused["mode"] == "paused", "Release Escape did not pause")
                        observations["native_movement_right"] = True
                        observations["native_pause"] = True
                    game.terminate(); game.wait(timeout=4); game = None
                    time.sleep(.15)
                profiles = list(Path(env["XDG_DATA_HOME"]).rglob("crossing-keepsakes.json"))
                require(len(profiles) == 1, "Default profile missing or duplicated")
                saved = json.loads(profiles[0].read_text())
                require(saved["look"] == observations["fresh_process_retained"], "Default profile differs from loaded look")
                observations["default_profile_outside_download"] = not profiles[0].is_relative_to(executable.parent)
                require(observations["default_profile_outside_download"], "Profile unexpectedly written inside download")
            finally:
                if display: X.XCloseDisplay(display)
                for child in (game, server):
                    if child is not None and child.poll() is None:
                        child.terminate()
                        try: child.wait(timeout=4)
                        except subprocess.TimeoutExpired: child.kill(); child.wait()
                X.XSetErrorHandler(old_handler)
        require(not x_errors, "Unexpected X11 errors")
        text = (output / "display.log").read_text()
        require(not any(s in text for s in ("ERROR:", "SCRIPT ERROR:", "Parse Error:")), text[-2000:])
        result = {"schema_version":1,"kind":"release_default_scene_and_synthetic_os_keys","package_sha256":package["sha256"],
                  "observations":observations,"images":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.glob("*.png"))},
                  "scope":"Actual unmodified default release scene, neutral cwd and absent developer-tool PATH; Xorg software display and synthetic keys, not independent human or hardware validation."}
        (output / "display.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
        print("PASS: default release window, native edit/apply/move/pause and default-path restart")
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        verify(args.archive, args.output)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        parser.exit(1, "FAIL: " + str(error) + "\n")
