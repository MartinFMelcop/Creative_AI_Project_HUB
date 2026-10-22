# North Star C# gameplay foundation

A functioning **engine-independent C# domain and original terminal encounter**, built
as the first practical step toward the selected Unity/C# production direction.
This is not a Unity project, Editor execution, Windows player, Steamworks integration
or replacement for the existing Godot adventure. Windows remains the intended player
target; Linux here is a development/verification host.

## Build and play

Use the exact SDK in [global.json](global.json), **10.0.401**:

```bash
cd north-star/csharp
dotnet build Checks/NorthStar.Checks.csproj -c Release
dotnet run --project Crossing/NorthStar.Crossing.csproj -c Release --no-build
```

The consumer connects two encounters. Prepare **Anchor/Lure** and **Plate/Trail**,
complete a survey, receive XP and earned allocation points, spend them on Vitality
or Focus, then enter a harder crossing. Health, resolve, distance, deadlines and
completion are actual state. There is no automatic strategy, saved progress or
network trust boundary. EOF/`quit` closes without writing a save.

| Choice | Actual experimental consequence |
|---|---|
| Anchor skill | Spend 2 resolve to stop a bolt in place |
| Lure skill | Spend 3 resolve to draw a bolt while advancing one position |
| Plate | Start with 14 health and 6 resolve before earned bonuses |
| Trail | Start with 10 health and 10 resolve before earned bonuses |
| Vitality | Each earned point adds 2 starting health to later encounters |
| Focus | Each earned point adds 2 starting resolve to later encounters |

Both skills remain exposed to ground pulses; their forward/defensive behavior does
not provide pulse immunity. `walk` advances one position, recovers two resolve and
leaves a pulse; `dash` advances two positions and spends one resolve. Moving on a
bolt exposes health. `wait` advances time without protection. The corridor is bounded to positions 0–8; exit requirements are minimum positions
2/4 for the two encounters. Pulse avoidance requires actual position change: an
attempt to walk/dash against the far bound still takes damage. The threat is shown
before each action. Insufficient resolve rejects the whole action without changing
health, position or time. Preparation/allocation/restart are locked during play;
failed encounters allow preparation/retry and pay no reward. A completed encounter
pays once, and a completed two-stage session cannot restart or pay again.

The original destination curve is deliberately small: levels 1–4 at 0/10/25/45 XP,
with two allocation points and one health/resolve bonus per gained level. Completing
the survey grants 10 XP; completing the crossing grants 15. These names/numbers are
**experimental proposals**, not approved class identities, canonical attributes,
a balance recommendation or a migration of the legacy 180-level game.

The measured Focus policy can afford all four Lure skills and both dashes. A
Vitality allocation survives a different, more exposed walking policy that defeats
Focus. Vitality cannot afford the entire Focus skill sequence without choosing a
different action; the rejected spend and a damaging wait remain real alternatives.
These are fixed policies, not optimal play or independent player evidence.

## Domain and compatibility boundary

[Progression.cs](Domain/Progression.cs) adapts the useful legacy threshold-lookup and
per-gained-level budget contracts. Its project compiles with **C# 8** against
**.NET Standard 2.1**, without UnityEngine, RGSS, UI, JSON or NuGet dependencies.
That compilation establishes a portable API/language boundary; **it does not prove
Unity API/compiler/import compatibility**. The terminal application and JSON study
host target .NET 10 and are not offered as Unity runtime assemblies. No particular
Unity Editor version/module is pinned until it can be verified and exercised.

Tables require consecutive levels, a zero first threshold and strictly increasing
bounded XP. Per-level budgets are nonnegative/bounded. Initial XP determines the
starting level; only later crossed levels grant budgets. Level-one budget metadata
is retained but never automatically paid. Maximum level stops new budget grants
while bounded total XP may continue increasing.

The historical helper silently clamps some invalid XP and reads missing HP/SP columns
as zero. This domain deliberately rejects invalid input and the laboratory binds the
actual HP_Gain/SP_Gain headers; those lossy fallback behaviors are not carried forward.

Rewards have local identity and transactional validation. Repeating the same ID and
amount is a no-op; substituting another amount rejects. Allocation obeys earned minus
spent conservation. This is an in-memory, single-owner ledger—not durable idempotency,
authentication or server authority. The encounter keeps its progression state private
and exposes immutable observations, so consumers cannot bypass active allocation locks.

Existing Eclipse/Cinder C# was inspected before implementation. Their net10 classes
use newer language/runtime APIs; directly importing them would not establish Unity
compatibility. The reusable invariant—validate a whole resource transaction before
mutation—is adapted without copying their game fiction or dependency graph.

## Reproduce and inspect

```bash
dotnet run --project Checks/NorthStar.Checks.csproj -c Release --no-build -- native /tmp/north-star-native.json
dotnet run --project Crossing/NorthStar.Crossing.csproj -c Release --no-build -- --demo /tmp/north-star-journey.json
```

The native controls cover thresholds, multi-level/partitioned XP, cap behavior,
transactional rejection/overflow, local replay/collision, conservation, strict study
schema, actual preparation locks, distinct abilities/outfits and connected journeys.
The demo executes the **actual consumer program** through survey, earned Focus and
crossing completion. It does not launch a graphical or Windows player.

The [RPG Systems laboratory](../../labs/rpg-systems/README.md) runs the same compiled
domain against preserved historical vectors and independent boundary controls.
It also retains the historical HP/SP header mismatch and rejects silent zero-budget
interpretation. Detailed execution and negative results live in
[its evidence](../../evidence/rpg-progression/RUN.json).

`NorthStar.Checks.dll study input.json output.json` accepts a bounded strict batch protocol:
`schema_version: 1`, `levels` rows with `level,total_xp,main,hp,sp`, and `cases` rows
with `id,start_xp,awards`. Results contain `rows` with actual total XP, level, gained
levels and main/HP/SP budgets. Source data is adapted outside the protected snapshot;
no historical Ruby/RGSS script is executed by this tool. Invalid or duplicate/missing
fields are rejected instead of creating success evidence.

Unity Editor, activation/license and Windows build modules are unavailable in the
current execution environment. No Unity or Windows validation is claimed. The next
migration step must execute a real Editor/import/scene and relevant platform checks;
existing Godot consumers retain their unresolved behavior/regression obligations.

## Scarce crafting preparation experiment

[Forge](Forge/README.md) composes the actual connected Crossing encounters with a
finite material inventory, original recipes and one-encounter rig consumption. It
exercises the [Economy & Simulation laboratory](../../labs/economy-simulation/README.md).
The standalone Crossing remains unchanged; Forge's supply gate is an explicitly
experimental scenario rule, not approved profession/class canon. Its new contribution
is resource ownership and consequential production, not a new combat model.

## Prepared identity and action slots

[Loadout](Loadout/README.md) layers a transactional original identity/action preparation
onto the actual Forge/Crossing consumers. Approach and outfit have independent owners;
a small experimental skill catalog controls available verbs and earned-level entry.
The [World & Gameplay method](../../labs/world-gameplay/README.md) distinguishes source
contracts from helper defects and from the unimplemented historical skill catalog.
No final class/background canon, Unity scene or Windows/Steam execution is implied.
