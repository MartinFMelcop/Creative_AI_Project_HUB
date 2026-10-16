# Cinderwatch native player 0.5.0

## Play the Linux distribution

Download/extract the entire [Linux player](../dist/cinderwatch-linux-0.5.0.zip).
From its `Cinderwatch` directory:

```sh
./cinderwatch.x86_64
```

Godot and .NET are included; no editor, installed runtime, SDK, Python, account or
source checkout is required. Keep `cinderwatch.pck`, `data_Cinder.Native_linuxbsd_x86_64`
and `media` beside the executable. If your extractor drops the permission, use
`chmod +x cinderwatch.x86_64`. The OS needs a desktop/audio stack, ICU and compatible
OpenGL support. This is a Linux x86_64 prototype; tested systems and limits are
recorded in [recovery execution](../../../evidence/cinderwatch/RECOVERY_RUN.json);
the earlier [response checks](../../../evidence/cinderwatch/RESPONSE_RUN.json) remain.

Read the brief, enter the yard, inspect enemy intentions and the `NEXT` queue.
Choose an action, inspect its computed forecast, then **Confirm action**.
Enemy turns advance with **Resolve announced enemy action**. Tactics, selection
and inspection spend nothing. Scroll the action list, or use Tab/Shift+Tab and
Enter. After acceptance, focus follows the next legal action/resolution/salvage.
The scene scales proportionally from 1280 × 800. Closing asks before leaving
unpreserved accepted progress, then stops/drains playback before releasing owned resources.

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

Accepted actions autosave to `user://cinderwatch-save.json`. The app name and
original schema/rules 0.1.0 remain compatible with previous native saves.
**Resume** validates and replays the primary autosave to the exact next turn.
**Save** retries that location. A successful write is read back and replayed
before the app reports that the current accepted actions have been preserved.
Write failures keep current progress in memory and show an error.

After at least one accepted action, choose **Run files → Save recovery copy…**
to select another JSON file. The copy contains the same action journal, not a
screenshot or a new save format. It is also read back and replayed before success.
The current run stays open; future accepted actions continue to use the primary
autosave, rather than replacing the recovery copy. Choose a different path from
the primary autosave; use **Save** to retry the primary location.

**Run files → Open run…** selects an existing journal, including a recovery copy.
The candidate must validate before replacing live play and is checked again when
opened. Invalid files leave the current run intact. Opening does not modify the
selected source file; subsequent accepted actions use the primary autosave.
Resume opens that primary slot, while Open run lets you choose a recovery file.

If accepted progress has not been preserved, **New run**, **Resume**, **Open run**
and window close show **Keep this run before leaving**. Choose **Keep this run**,
**Retry autosave**, **Save recovery copy…**, or the explicit **Leave without saving**.
A successful retry or copy returns to the current run; request the navigation
again when ready. Cancelling a copy returns to this choice. Failed recovery does
not discard the run. **New run** starts fresh memory only after this guard; its
first accepted action or explicit Save replaces the primary slot.

This is one primary slot with portable recovery files, not a multi-slot manager.
No undo, cloud sync or power-loss durability guarantee. [Recovery execution](../../../evidence/cinderwatch/RECOVERY_RUN.json)
records technical failure/control checks; these do not establish unassisted
player recovery, physical accessibility or independent approval.

The player loads raw original PNG/WAV files beside its executable, independently
of the shell's working directory. Source/compiled-project play still loads them
from `res://media`. A missing media copy exits with a specific extraction diagnostic.
Package checks cover runtime/files/source/media identity. Godot/.NET license and
third-party notices accompany the bundle; original creative provenance remains
in `media/provenance.json`. Hashes are integrity records, not origin signatures.

## Editable compiled project

The [compiled project pack](../dist/cinderwatch-0.5.0.zip) remains available for
editor/runtime use. It requires Godot **4.6.3 .NET** and .NET **10 runtime**:

```sh
godot-dotnet --path Native
```

No SDK/NuGet restore is needed to play that alternate pack. The standard Godot
editor cannot execute C#. It contains owned assemblies/source/configuration;
its engine/API/runtime are external. Earlier 0.1.0/0.2.0/0.3.0/0.4.0 packs are preserved.

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
