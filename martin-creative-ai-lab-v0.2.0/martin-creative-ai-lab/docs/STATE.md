# Lab state

**Updated:** 2026-10-13 (UTC). **Seed:** 0.22.0.
**Current milestone:** P06 Veilbreak 0.4.0 — Linux player and mapped gamepad.

[Download/play](../projects/veil-arena/README.md). A six-file Linux x86_64 ZIP
includes the verified official Godot release runtime, actual exported resources,
checksums, instructions and engine/asset notices. Extract and run; no editor,
SDK, .NET or source checkout is required. Desktop/system OpenGL libraries remain
requirements. Existing source and the current engine-dependent PCK are retained.

Left stick/D-pad, three combat buttons and begin/pause/tactics/sound/restart now
use native input. Deadzone/partial speed, bounded diagonal movement, fresh presses,
automatic hints and active-pad loss handling preserve keyboard continuity.
Reconnection never auto-resumes. A keyboard player is not paused by an old pad's
loss. Costs/contact clocks, opponent rules and existing media remain unchanged.

[Execution](../evidence/veil-arena/RELEASE_RUN.json): 30 native controller checks,
116 checks on the exact exported PCK, complete two-phase synthetic pad/keyboard
victories, package/digest checks and a rejected real GDScript import failure.
The final release ELF window was operated by X11 keyboard events outside checkout:
title/combat/pause/tactics, actual idle defeat and restart. Real OpenGL frames
reviewed. Release templates lack the test-script executor: PCK checks use the
editor, while release-window input is separate evidence. Physical controller and
audio output, independent enjoyment/accessibility, other OS and demand are open.

Started clean at `a9af690`, matching fetched main; push permission verified.
Compared completed P10/P01/P11 work, P03 feedback needs, P05's .NET packaging and
P06's required external engine. Native delivery with input removes a demonstrable
access barrier; standard Godot/GDScript fits its existing physics/audio consumer.
Official templates were available, downloaded and verified; Unity was not located.
No new art/audio, shared framework, legacy recovery or Sites deployment. Archive
and other product bytes remain preserved. Main publication is authorized.

Next compare real Linux/controller use with P01 strategy, P10 reader/player
choices, P03 listening and P11 team handoffs before selecting another milestone.
