# Cinderwatch — P05 0.4.0

A complete small tactical rescue campaign, newly adapted from P05's turn-based
seed. [Download the Linux player](dist/cinderwatch-linux-0.4.0.zip), extract the
whole folder and run `./cinderwatch.x86_64`: Godot and .NET are included. The
[editable compiled project](dist/cinderwatch-0.4.0.zip) is also maintained.
[Play/rebuild](Native/README.md) explains both distributions, controls and saves.
This is an actual three-encounter destination, not recovered RMXP/P10 code.

Release **0.4.0** adds an optional **Inspect response** report after selecting an
action. It branches the same deterministic Core through consecutive announced
enemy replies, stopping before the next crew decision, salvage or result. Compare
projected HP/shields/scorch/supplies and the full event chain before confirming.
The report never assumes another hero's move, spends a turn or writes a save.
Short immediate previews and manually paced enemy turns remain available.

After Vale braces in the opening, compare Rook's Brace (36 HP after Bite) with
Strike (29 HP, but damage dealt to the hound). Cover, Pin, repair, expiry and
start-turn scorch follow actual rules, including skipped incapacitated actors.
[Response execution](../../evidence/cinderwatch/RESPONSE_RUN.json) records domain
comparisons, native keyboard/modal checks, actual frames and shipped player use.
This is bounded tactical feedback, not an optimal-plan solver or human learning
validation. Existing campaign rules, save schema, art/audio and old ZIPs remain.

Release 0.3.0 established the self-contained Godot .NET/Linux distribution with
verified source/runtime/payload identity and original raw media. That delivery
pattern is retained for 0.4.0; the earlier package and execution record remain.

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

## Native identity and action feedback

![Actual illustrated Governor encounter](../../evidence/cinderwatch/presentation-governor.png)

Eight original generated portraits distinguish the three rescuers and five
machine types. The unchanged 4×2 PNG is consumed through native atlas regions;
these are static portraits, not recovered artwork or animated actor clips.
State dimming, active/selected outlines and fading transaction labels accompany
the actual rules. HP, shielding, row change, Pin and scorch removal feedback is
computed from accepted before/after states rather than an invented damage roll.
Threat/queue/resource text stays visible. No turn is delayed or queued by effects.

Seven original synthesized PCM action cues cover strike, brace, Pin, treatment,
movement, steam and stage completion. Sound can be muted; focus loss, Tactics and
reset stop active playback. A short mixer drain precedes window/test shutdown.
The UI reuses cards/action buttons and a small owned style cache; selection no
longer destroys those controls. Raw media loading makes the compiled project
usable outside source without imported texture/audio caches or an SDK.

[Media provenance](Native/media/provenance.json) and
[execution](../../evidence/cinderwatch/PRESENTATION_RUN.json) distinguish image
production, actual native/mixer checks and Codex visual judgment. A prior CI
Godot/.NET shutdown abort motivated lifetime inspection; bounded clean runs do
not prove every platform/GC schedule is repaired. Physical audio, unassisted
readability, enjoyment/accessibility and commercial clearance remain unverified.
The original 0.1.0 ZIP is retained. Game/Content/Journal and rules/save schema
0.1.0 remain unchanged; 0.4.0 adds a separate Core response helper. Presentation
0.2.0 and Linux distribution 0.3.0 remain recorded historical increments.

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
python3 tools/check_media.py
python3 tools/pack.py
python3 tools/check_pack.py
python3 tools/export_linux.py --godot /path/to/Godot_mono --templates /path/to/official-mono-templates.tpz
python3 tools/check_linux.py
```

The editable project pack contains owned assemblies/configuration/source; its
engine/API/runtime are external. The Linux player includes the verified engine,
.NET runtime/API, original media and their notices. Rebuilding consumes
the pinned Godot NuGet SDK; playing the compiled pack needs the engine/runtime.

[Execution evidence](../../evidence/cinderwatch/RUN.json) distinguishes compilation,
actual headless controls, OpenGL visual inspection and the delivered consumer
outside source using runtime-only .NET. The implementing-agent controller wins
four salvage routes; a Strike-only controller loses, and Brace-only hits the
deadline. These are bounded comparisons, not an optimal-strategy proof or human
playtest. The initial supply configuration was revised after a route became too
fragile; visible text/layout and incapacitated-character continuity were reviewed.

[Native frame](../../evidence/cinderwatch/governor.png) shows the Governor's real
announced threat, current resources and crew condition. The frame is historical 0.1.0 evidence; the new presentation frame above
records 0.2.0. No old project media was reused. Generated art and native feedback
do not establish finished art direction or independent approval. Timing-free discrete turns do not establish hardware accessibility.
Unassisted play, alternative policies, balance/creative appeal, other platforms,
sound/art production and commercial interest need external evidence.
