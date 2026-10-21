# Mapped gamepad destination execution

Baseline: `3c11446fe86b7eac755650a10aaa8339d7a94470`. See `RUN.json` for exact
sources, artifacts, commands and limits. The published-baseline South button is
ignored at title; current South starts the real consumer. Probe tick after start
is an observation, not a latency measurement.

From the maintained lab, with Godot 4.6.3:

```bash
python3 north-star/prototype/tools/test_verify_gamepad.py
python3 north-star/prototype/tools/verify_gamepad.py --archive north-star/prototype/dist/crossing-drill-linux-0.2.0.zip --output /tmp/pad.json --compare evidence/north-star-gamepad/gamepad.json
python3 north-star/prototype/tools/verify_linux.py --output /tmp/player.json --compare evidence/north-star-gamepad/results.json
```

The mapped driver injects `InputEventJoypadButton`/`InputEventJoypadMotion` through
`Input.parse_input_event`, flushes the viewport and advances the real scene physics
at fixed 1/60 steps. Existing policy decisions become mapped events, not direct
combat commands. Both actual escort/arrival/aid/return goals complete. Drift,
unknown inputs, held confirmations, analog/digital motion, independent aim,
appearance draft/apply/cancel, real workshop travel/make/recycle/deploy, rehearsal,
guide/options, explicit resume, disconnect/focus and keyboard takeover have controls.
Two Python tests include nine malformed/incomplete/misleading report mutations.

For a desktop or owned Xorg dummy display, inspect the actual scene views:

```bash
mkdir -p /tmp/pad-views
PAD_SHOTS=/tmp/pad-views godot --path north-star/prototype --audio-driver Dummy --script "$PWD/evidence/north-star-gamepad/capture.gd"
```

Bound that graphical command to 60 seconds externally; close only its owned display.
The four stored PNGs are actual source scene views following mapped event receipt.
The capture helper must advance scene presentation before freezing the frame so
appearance portraits use their actual positions. Agent inspection found readable
unclipped hints; workshop pause needed a distinct A resume hint rather than Y deploy.
These views and injected events are not physical hardware or external human review.

The retained source/PCK suites exercise 782 earlier controls. Their exposed gameplay
fields match the preceding evidence; source identities and identity-bearing opaque
observation digests necessarily change. Full current source/PCK observations must
match each other and CI compares the current records exactly. Previous records and
Linux 0.1.0 remain historical, not rewritten. Mixer checks execute again; PCM runs
are validated by their existing bounded metrics rather than invented byte equality.

No physical pad, haptics, pad remapping, OS-wide compatibility, comfort, accessibility,
identity recognition, enjoyment, multiplayer or market validation is claimed.
