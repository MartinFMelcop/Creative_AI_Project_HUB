# Forge: scarce expedition preparation

An **original experimental C# consumer**, composing the unchanged
[Crossing](../README.md) encounter with an actual inventory and crafting ledger.
It is a separate supplies scenario, not a retroactive restriction of the original
Crossing, approved class canon, Unity scene or packaged Windows/Steam game.

## Build and run

From `north-star/csharp`, use the pinned SDK10.0.401:

```bash
dotnet build ForgeChecks/NorthStar.ForgeChecks.csproj -c Release
dotnet run --project Forge/NorthStar.Forge.csproj -c Release --no-build
dotnet ForgeChecks/bin/Release/net10.0/NorthStar.ForgeChecks.dll native /tmp/forge-native.json
dotnet Forge/bin/Release/net10.0/NorthStar.Forge.dll --demo /tmp/forge-demo.json
```

Start with **4fiber and2binder**. At the workbench, each Plate or Trail rig costs
2fiber+1binder. The local survey license is already known. Crafting commits material
consumption and one output together. **Entering an encounter consumes one rig;
failure never refunds it.** Two rigs total can be made from starting supplies.
Unprepared entry consumes nothing and remains possible after exhaustion.

| Entry | Actual encounter behavior |
|---|---|
| Plate rig | Plate health14/resolve6; Anchor skill blocks bolts in place for2resolve |
| Trail rig | Trail health10/resolve10; Lure skill advances1 against bolts for3resolve |
| Unprepared | Plate health14/resolve6; walk/dash/wait available, skill rejected |

Earned progression adds resources as documented by Crossing. Both prepared skills
remain exposed to pulses. Crafting, entry and allocation are locked during encounters;
allocation also requires earned points. Completing the expedition cannot reset it.
The console displays resources, inventory, remaining distance/deadline and the next
threat. Invalid commands reject without changing gameplay state. EOF/`quit` closes
without saving. There is no account, server authority, durable replay or persistence.

Interactive commands: `craft plate`, `craft trail`, `enter plate`, `enter trail`,
`enter unprepared`, `vitality N`, `focus N`; during encounters `walk`, `dash`, `skill`,
`wait`. This fixed mixed policy is reproducible through actual stdin:

```text
enter unprepared
walk
walk
walk
walk
craft trail
focus 2
enter trail
skill
skill
dash
skill
dash
skill
```

It succeeds with one rig consumed and2fiber+1binder remaining. This demonstrates a
conservation option rather than requiring crafting before every encounter. The demo
also executes two fully crafted journeys: Trail with Focus and a skill/dash policy;
Plate with Vitality and a different exposed walking/skill policy. Controls retain a
no-craft walking survey success, no-craft harder-crossing walking failure and failed
rig/no-refund retry. These fixed policies do not establish optimal play, balance,
player preference or impossibility of every unprepared policy.

## Contract and source relationship

[Crafting.cs](../Domain/Crafting.cs) belongs to the existing C#8/netstandard2.1 domain.
It validates IDs, bounded quantities, aggregate duplicate ingredients, recipe identity,
station, unlock, all input availability and output capacity before committing mutation.
Outputs cannot finance missing inputs. Successful request IDs are locally idempotent;
substituting recipe/station/operation rejects. Replaying a craft after its output was
consumed never recreates it. Failed requests do not reserve IDs. Detached immutable
snapshots prevent external mutation. Inventory types/recipes/unlocks are bounded at128;
quantities at1,000,000 and committed requests at10,000.

The private expedition Session prevents bypassing preparation locks. External craft
request IDs cannot use the internal `entry_` namespace. Each prepared entry consumes
one output through the same transaction owner before starting the validated encounter.
Retried attempts retain inventory expenditure and previously earned progression.

The useful P01 Eclipse invariant is adapted: validate the complete resource transaction
before applying any component. Its .NET10 records/ImmutableArray, world and game rules
are not imported. XP recipe/station tables inform the separate Economy laboratory's
source assay, not these original recipe names, amounts or authorial decisions. No
historical source bytes or existing Crossing code are modified. The existing progression
laboratory must be rerun because the domain assembly now contains the new implementation.

The checks execute80 native controls including conservation, replay/substitution,
missing inputs/unlock/station, aggregate quantities, output overflow, immutable views,
ledger cap, whole-state rejection, scarce preparation, real completion/failure and retry.
The lab evidence owns exact source identities and observed results. A source build on
Linux does not establish Unity import/API compatibility, activation/license, Windows
modules/player or Steam execution.
