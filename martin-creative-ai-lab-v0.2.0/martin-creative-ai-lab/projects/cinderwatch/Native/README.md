# Cinderwatch native player 0.4.0

## Play the Linux distribution

Download/extract the entire [Linux player](../dist/cinderwatch-linux-0.4.0.zip).
From its `Cinderwatch` directory:

```sh
./cinderwatch.x86_64
```

Godot and .NET are included; no editor, installed runtime, SDK, Python, account or
source checkout is required. Keep `cinderwatch.pck`, `data_Cinder.Native_linuxbsd_x86_64`
and `media` beside the executable. If your extractor drops the permission, use
`chmod +x cinderwatch.x86_64`. The OS needs a desktop/audio stack, ICU and compatible
OpenGL support. This is a Linux x86_64 prototype; tested systems and limits are
recorded in [response execution](../../../evidence/cinderwatch/RESPONSE_RUN.json).

Read the brief, enter the yard, inspect enemy intentions and the `NEXT` queue.
Choose an action, inspect its computed forecast, then **Confirm action**.
Enemy turns advance with **Resolve announced enemy action**. Tactics, selection
and inspection spend nothing. Scroll the action list, or use Tab/Shift+Tab and
Enter. After acceptance, focus follows the next legal action/resolution/salvage.
The scene scales proportionally from 1280 × 800. Closing stops/drains playback
before releasing owned resources.

Three fights, two one-time salvage choices and an ending; each fight has a
12-round pressure deadline. HP/supplies persist. Fallen allies recover at salvage,
but cannot act or receive combat Mend. Tactics explains screening, Cover, Pin
and scorch. The ending acknowledges incapacitated rescuers. Portraits and seven
original cues show actual state changes; no queued turn, invented damage or full
actor animation. Sound toggles above the brief; focus loss/Tactics/reset stop it.

## Compare the next response

Select any legal crew action, then **Inspect response**. The scrollable report
calculates that action and all consecutive announced enemy actions, stopping
**before the next crew decision**, salvage or result. It names the stopping
actor/round and lists projected crew HP, rows, shields, scorch and supplies,
followed by the complete event chain. No later hero action or salvage is assumed.
This is an exact deterministic branch of the same Core, not a recommended move
or a prediction of an unchosen round. The short immediate preview remains visible.

In the opening, have Vale Brace. On Rook's turn compare Brace with Strike:
Brace leaves Rook at 36 HP after the screened Bite; Strike leaves 29 HP while
hurting the hound. Pin, Cover interception, repair, shield expiry, incapacitated
turn skips and the next actor's start-turn scorch follow actual rules.
A Vale inspection may stop immediately at Rook, with no intervening enemy.

Inspection pauses at a keyboard modal, stops active cues and spends no action,
supplies or save writes. The return button preserves selection and returns focus
to Inspect response; confirm only when ready. Scroll the report with the mouse
wheel or keyboard. Enemy turns still require their own explicit Resolve after
confirmation. [Response execution](../../../evidence/cinderwatch/RESPONSE_RUN.json)
separates scripted checks and implementing-agent frame review from human learning.

## Save and resume

Accepted turns autosave to `user://cinderwatch-save.json`. The app name and original
schema/rules 0.1.0 remain compatible with previous native saves. **Resume** replays
validated actions to the exact next turn. Malformed saves preserve live play;
write failures keep memory progress and show an error. **New run** creates fresh
memory; its first accepted turn or an explicit Save replaces the slot.
One slot, no undo, cloud save or power-loss durability guarantee.

The player loads raw original PNG/WAV files beside its executable, independently
of the shell's working directory. Source/compiled-project play still loads them
from `res://media`. A missing media copy exits with a specific extraction diagnostic.
Package checks cover runtime/files/source/media identity. Godot/.NET license and
third-party notices accompany the bundle; original creative provenance remains
in `media/provenance.json`. Hashes are integrity records, not origin signatures.

## Editable compiled project

The [compiled project pack](../dist/cinderwatch-0.4.0.zip) remains available for
editor/runtime use. It requires Godot **4.6.3 .NET** and .NET **10 runtime**:

```sh
godot-dotnet --path Native
```

No SDK/NuGet restore is needed to play that alternate pack. The standard Godot
editor cannot execute C#. It contains owned assemblies/source/configuration;
its engine/API/runtime are external. Earlier 0.1.0/0.2.0/0.3.0 packs are preserved.

## Build and verify

Rebuild with SDK **10.0.401**, official Godot .NET **4.6.3** and its verified Mono
release template. From the project directory:

```sh
dotnet build Native/Cinder.Native.sln -c Debug
godot-dotnet --headless --path Native --editor --import --quit
python3 tools/export_linux.py --godot /path/to/Godot_mono --templates /path/to/Godot_v4.6.3-stable_mono_export_templates.tpz
python3 tools/check_linux.py
```

The exporter validates editor/SDK/template identities and builds a fresh staging
project, without consuming the checkout's import/assembly cache. It publishes
ExportRelease with .NET **10.0.12** self-contained, copies unchanged media/notices,
and records source and payload hashes. Godot .NET requires the maintained solution
file. A zero process exit accompanied by a reported export error is rejected.
`--template` accepts the pinned extracted `linux_release.x86_64`; `--output` permits
an isolated rebuild. Binary fingerprints may differ across build paths; current
source/resource identity and actual runtime checks are required independently.

On the extracted player, technical checks drive actual controls, all four salvage
routes, deadline loss, save failures/replay, keyboard, rendering and AudioServer:

```sh
./cinderwatch.x86_64 --headless -- --verify --save-path /tmp/cinder-check/save.json
# With a display, add: --capture-dir /tmp/cinder-frames
```

Always isolate the save: checks overwrite the specified path. These are scripted
inputs, not human playtests. Source, compiled project and actual release execution
are distinct proofs. Physical listening, independent tactics/enjoyment/accessibility,
other platforms and commercial readiness remain unverified.
