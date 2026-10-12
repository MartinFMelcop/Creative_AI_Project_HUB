# Cinderwatch — P05 0.1.0

A complete small tactical rescue campaign, newly adapted from P05's turn-based
seed. [Download the compiled native project](dist/cinderwatch-0.1.0.zip) and
[run it with Godot .NET](Native/README.md). This replaces the absence of a P05
runtime with an actual three-encounter destination; it does not restore an RMXP
game or import P10's historical rules.

Rook shields, Vale reaches screened targets or pins an upcoming enemy action,
and Neri treats injuries and scorch with finite kits. Front/rear screening,
fixed announced intentions and stable initiative make timing/target decisions
visible. The yard introduces protection; the gallery's armoured Bulwark and
repair drone reward reaching the rear; the Governor alternates charge and
party-wide steam. Injuries, cells and kits persist. Two salvage decisions trade
recovery against interruption capacity, then cover against damage. The final
scene reacts to which rescuers remain standing.

The interface previews by forking the **same C# domain** that commits actions.
It provides confirmation, manually paced enemy turns, a persistent chronological
log, rules, accepted-action autosave/replay, failure feedback and restart.
No browser bridge, duplicate rules, cloud service or RNG dependency.

## Build and verify

C#/.NET 10 provides a pure, independently executable domain. Godot .NET 4.6.3
consumes it directly for a native desktop scene. Both tools were available;
Unity was not found. A Unity/editor migration would add setup and integration
cost without improving this bounded turn-based milestone.

```sh
dotnet run --project Checks -c Release
dotnet build Native/Cinder.Native.csproj -c Debug
godot-dotnet --headless --path Native --editor --import --quit
godot-dotnet --headless --path Native -- --verify --save-path /tmp/cinder-source/save.json
python3 tools/pack.py
python3 tools/check_pack.py
```

The pack contains only owned assemblies, configuration and editable sources.
Godot's engine/API assemblies and .NET runtime are external. Rebuilding consumes
the pinned Godot NuGet SDK; playing the compiled pack needs the engine/runtime.

[Execution evidence](../../evidence/cinderwatch/RUN.json) distinguishes compilation,
actual headless controls, OpenGL visual inspection and the delivered consumer
outside source using runtime-only .NET. The implementing-agent controller wins
four salvage routes; a Strike-only controller loses, and Brace-only hits the
deadline. These are bounded comparisons, not an optimal-strategy proof or human
playtest. The initial supply configuration was revised after a route became too
fragile; visible text/layout and incapacitated-character continuity were reviewed.

[Native frame](../../evidence/cinderwatch/governor.png) shows the Governor's real
announced threat, current resources and crew condition. No external art/audio
was reused or generated for this milestone. Functional UI is not finished art
direction. Timing-free discrete turns do not establish hardware accessibility.
Unassisted play, alternative policies, balance/creative appeal, other platforms,
sound/art production and commercial interest need external evidence.
