# Eclipse Fair — native board 0.2.0

A complete desktop board consumer of the existing P01 C# economy. Eight connected
venues, one human and three visible rivals, forecasts, concrete action previews,
bounded theft/wards, rites, Gate/deadline results and automatic replayable saving.
The original CLI/rules/compiled package remain 0.1.0 and compatible.

## Play the delivered package

Install **Godot .NET 4.6.3** (the standard GDScript engine cannot load C#) and the
**.NET 10 runtime**. Unzip `eclipse-board-0.2.0.zip`, then from its `eclipse-board`
directory:

```bash
/path/to/Godot_mono --path Native
```

The package includes the actual compiled game assemblies and editable sources.
It uses the installed engine's GodotSharp API; engine/runtime binaries, external
art and third-party managed assemblies are not redistributed. No SDK or NuGet
restore is required to play it. This is a runtime-dependent native project pack,
**not a standalone OS executable or an engine export**. Linux x86_64 is the tested
platform. Other systems/controllers remain unverified.

## Play

You control **Vaelis**. Click a venue, select an action, inspect the actual budget
and consequences, then **Commit this plan**. Travel costs one obol and crosses
at most one edge; staying is free. The gold line shows the proposed route.
Faded venues remain inspectable but are too far to act at now.

Buy three sigils at Market/Bazaar. Each purchase adds curse and raises the next
price; prices rise again after round 10. Rites at the Chapel remove two curse,
for two obols or free during a procession. Curse reduces work income. Reach the
Gate with three sigils and zero curse, then choose **Claim the Gate**.

Raven wards block one co-located theft. Stealing transfers existing obols and
adds curse if successful. Forecasts, current/next work income and rival resources
are public. **Suggest plan** selects a one-turn heuristic; it does not commit,
predict rival choices or guarantee victory. Round 20 ends by sigils, least curse,
then obols; exact ties share the win. A Gate claim wins immediately.

Watch rivals one at a time or enable **Auto rivals** (one turn per second).
Losing window focus disables auto turns; resume explicitly. Tab/arrow keys
navigate native controls; Enter/Space activate the focused control. This is a
desktop prototype without audio or controller support.

Accepted turns autosave to Godot's per-user data directory as `match.json`.
**Save** retries a failed write; **Resume save** validates/replays every action
before replacing play. A valid save also resumes at startup; no wall time passes.
Malformed/incompatible saves leave the current match intact. A failed write
keeps accepted progress in memory, with visible feedback. **New fair** confirms
a seed and restores baseline rules/policies. Its first accepted turn or an explicit
**Save** replaces the saved match. No undo or
automatic backup is provided. Save files share the CLI 0.1.0 journal contract.

## Build and check

Use SDK **10.0.401** and Godot .NET **4.6.3**. From the parent `eclipse-fair` directory:

```bash
dotnet build Native/Eclipse.Board.csproj -c Debug
Godot_mono --headless --path Native --editor --import --quit
# Always use an isolated check directory, not your normal save:
Godot_mono --headless --path Native -- --verify --save-path /tmp/eclipse-check/match.json
python3 tools/pack_board.py
```

Verification drives the actual Godot scene, focused keyboard input and control
signals through plans, optional theft/protection, journal failures/resume, Gate
and deadline matches. Result/action parity uses the unchanged Core/Agents, not
duplicated engine rules. These are synthetic workflows, **not human playtests**.
With a display, `--verify --save-path <scratch>/match.json --capture <scratch>/frames`
also captures real rendered frames for implementing-agent inspection.

The compiled package is additionally exercised outside source; packaging includes
only owned assemblies/config/source, no caches or engine libraries. Technical
execution and visual review do not prove unassisted strategy, enjoyment,
accessibility, hardware performance, cross-platform support or commercial demand.
