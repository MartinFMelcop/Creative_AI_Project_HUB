# Explicit prepared identity and actions

An original **C# terminal experiment** composes the actual Forge and Crossing rules.
It separates experimental discipline, compatible background, equipped action slots
and outfit. It is not a Unity scene, final class system or port of the historical game.

## Build and play

From `north-star/csharp`, use the exact SDK10.0.401 pin:

```bash
dotnet build LoadoutChecks/NorthStar.LoadoutChecks.csproj -c Release
dotnet run --project Loadout/NorthStar.Loadout.csproj -c Release --no-build
dotnet LoadoutChecks/bin/Release/net10.0/NorthStar.LoadoutChecks.dll native /tmp/loadout-native.json
dotnet Loadout/bin/Release/net10.0/NorthStar.Loadout.dll --demo /tmp/loadout-demo.json
```

| Prepared layer | Actual effect / requirement |
|---|---|
| Anchor discipline / Brace | Level1, 2resolve, stops a bolt in place |
| Lure discipline / Draw | Level1, 3resolve, draws a bolt while advancing1 |
| Shared Dash | Level2 earned through actual survey completion, 1resolve, distance2 |
| Background | Compatibility-only: Anchor supports workshop/trailborn; Lure supports trailborn |
| Outfit | Independent PlateHP14/resolve6 or TrailHP10/resolve10, before earned bonuses |

These names/relations/values are original experiments, not adopted lore, approved
classes or demographic restrictions. Background has no hidden stat/supply effect.
Only three action definitions exist; four slots are capacity, not four distinct
implemented abilities. Walk and Wait remain baseline commands. Skills remain exposed
to pulses; no prepared slot supplies immunity or free resources.

Submit a complete proposal with exactly four slots, `-` meaning empty:
`loadout anchor trailborn brace dash - -`. Unknown IDs, class/background incompatibility,
duplicate skills or unmet earned levels refuse the whole proposal. Prior identity and
all slots remain intact. Explicit replacement is allowed only before/between encounters;
it does not restore health/resolve, refund supplies, change earned allocations or repay
rewards. The current proposal is revalidated before entry and slot execution.

`craft plate/trail` costs2fiber+1binder from finite4fiber+2binder. `enter plate/trail`
consumes one rig per attempt, including failures. `enter unprepared` consumes nothing
but cannot execute the discipline skill. Existing Forge defaults remain unchanged;
the new overload validates an explicit approach before consumption. No mutable
underlying Expedition/Session escapes this consumer.

## Reproduce an actual earned-slot journey

Run the console with these stdin commands:

```text
craft trail
craft trail
loadout anchor workshop brace dash - -
enter trail
walk
slot 1
walk
slot 1
focus 2
loadout anchor trailborn brace dash - -
enter trail
slot 1
slot 1
slot 2
slot 1
slot 2
slot 1
```

The first Dash proposal is rejected at level1, preserving Brace. The survey earns
level2 and two points; Focus allocation and explicit Dash equipping then permit the
harder crossing. The fixed Anchor/Trail policy completes at HP11/resolve5, position4,
XP25/level3 with two rigs consumed. `slot 1..4`, `walk`, `wait`, `vitality N`, `focus N`
and `quit` are the remaining commands. EOF/quit closes without a save.

The demo also completes Lure/Plate at HP7, position6; this reverses the old outfit/
approach coupling rather than merely renaming it. Empty preparation can pass the
survey by walking, but the retained harder all-walk policy dies. These fixed policies
do not prove optimality, necessity of every skill, balance, preference or enjoyment.

## Source contract and verification boundary

[The domain](../Domain/Loadout.cs) is C#8/netstandard2.1 and validates immutable catalogs,
explicit class/background relations, skill ownership, learned levels, duplicate IDs
and complete four-slot proposals. It has no class-dependent global cache or destructive
sanitation. The [World laboratory](../../../labs/world-gameplay/README.md) executes
actual source compatibility/level queries through this domain against an independent
reference and retains distinct helper variants/models. Described legacy effects are
not executed merely because an eligibility query accepts a skill ID.

Native controls exercise detached immutable slots, fail-closed relations, active locks,
whole-state refusal, earned prerequisites, actual action costs/displacement, independent
outfits and connected completion/failure/retry. The bounded JSON study host rejects
unknown/duplicate/missing fields and unsupported types before output. Exact identities,
observations and limitations belong in [execution evidence](../../../evidence/world-loadout/RUN.json).
No Ruby/RGSS, Unity Editor/import, Windows player, Steam, persistence, networking or
independent player execution is implied by Linux .NET execution.
