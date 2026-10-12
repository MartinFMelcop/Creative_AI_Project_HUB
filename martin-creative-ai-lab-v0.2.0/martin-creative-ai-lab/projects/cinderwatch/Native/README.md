# Cinderwatch native player

Unzip `cinderwatch-0.1.0.zip`. This is a **compiled Godot .NET project**, not a
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
and Enter. The scene scales proportionally from 1280 × 800.

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
the ordinary player slot. Tests are not independent player feedback. Artwork is
functional geometric UI; this version has no soundtrack or animated characters.
Linux execution is recorded; other OS exports/input/accessibility remain untested.
