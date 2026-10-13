# Cinderwatch native player

Unzip `cinderwatch-0.2.0.zip`. This is a **compiled Godot .NET project**, not a
standalone OS executable. Install Godot **4.6.3 .NET** and .NET **10 runtime**.
The standard GDScript-only Godot editor cannot load this C# assembly.

From the extracted `cinderwatch/` directory:

```sh
godot-dotnet --path Native
```

`godot-dotnet` denotes your installed Godot .NET executable. No SDK, NuGet or
source checkout is needed to play this delivered package. Editing/rebuilding
requires SDK 10.0.401 and `dotnet build Native/Cinder.Native.csproj -c Debug`.

Read the brief, enter the yard, inspect enemy intentions and the `NEXT` queue.
Choose an action, inspect its computed forecast, then **Confirm action**.
Enemy turns advance only with **Resolve announced enemy action**; inspection,
Tactics and selection spend nothing. Scroll the action list, or use Tab/Shift+Tab
and Enter. After accepting a turn, focus follows the next legal action, enemy
resolution or salvage control. The scene scales proportionally from 1280 × 800.

Three fights, two one-time salvage choices and an ending; the pressure deadline
is 12 rounds per fight. HP/supplies persist. Fallen allies recover at salvage,
but cannot act or receive combat Mend. `Tactics` explains screening, Cover,
interrupts and scorch. The ending acknowledges incapacitated rescuers.

Accepted turns autosave to Godot's `user://cinderwatch-save.json`. Resume replays
validated actions to the exact next turn. Invalid saves preserve live play;
write failures preserve memory progress and show an error. **New run** creates
fresh memory; the first accepted turn or explicit Save replaces the old slot.
There is one slot and no undo, cloud save or power-loss durability guarantee.

Reproduce declared synthetic native checks without a display:

```sh
godot-dotnet --headless --path Native -- --verify --save-path /tmp/cinder-check/save.json
```

This executes real native controls, save/error flows, all four complete salvage
routes and a deadline defeat. It overwrites **the specified test save**, not
the ordinary player slot. Tests are not independent player feedback. The new eight-portrait industrial atlas, transaction markers and seven action
cues are delivered with this package. They load raw PNG/WAV bytes without an
editor import or SDK. Sound: on/off is available above the brief and remains a
window-local preference across new runs. Tactics/focus loss/reset stop a cue;
closing drains the mixer briefly before disposing owned resources.

Selection outlines the actual chosen target. Portraits dim when down; HP/shield/
row/cancellation/scorch markers come from accepted before/after states, then fade.
There is no queued turn or delay before applying a transaction/autosave. Static
portraits with state feedback are not full character animation or a soundtrack.
Linux execution is recorded; other OS exports/input/accessibility remain untested.
