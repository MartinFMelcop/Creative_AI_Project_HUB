# World & Gameplay Systems Lab — explicit preparation

Owner origin: P10. This bounded method investigates whether explicit class/background/
skill compatibility and whole-proposal validation can preserve identity while driving
actual original North Star encounter actions. It does not complete the wider NPC,
quest, profession, faction, reputation or world-state domain.

## Selection and independent analyses

Engineering, Scientific and Creative specialists independently compared loadout
constraints, durable transaction recovery and NPC/quest continuity against actual
C# consumers and unavailable Unity tooling. World & Gameplay remained incomplete;
Crossing/Forge already offered consequential encounters and resource ownership.
A preparation contract can mature this destination and exercise identity/action
prerequisites without repeating progression or crafting studies. Durable recovery
requires its own serialization/crash/ownership scope; NPC continuity requires distinct
state/expiry/content methods. Neither is declared consumed here.

SCI-017 influenced controlled comparisons: keep the same source bytes and scenario
when changing the eligibility contract, retain rival behavior and distinguish software
observations from independent participants. Engineering constrains ownership, cache
identity and atomic replacement. Creative analysis constrains original choice and
separates discipline, equipment, background metadata and approved canon. These agents
are not independent human validation or the protected Brain documents themselves.

## Actual sources and preserved variant differences

The pinned Rave Master snapshot is
`36af1651271422ae33856e8b5d7b45702215f165`. `run.py` binds the actual ACT1 class,
background, class/background relation and combat-skill CSVs; ACT1 and bundled
`RM_UI_SKILL_EQUIP_RUNTIME.rb`; and ACT1 `RM_CHARACTER_CREATE_RUNTIME.rb`.
No preserved byte is modified and no historical script is executed.

The inspected catalog has **10 classes, 11 backgrounds, 52 allowed relations and 166
unique skills**. These are design/contract data, not proof of 166 implemented abilities.
`ClassVariant`, source names, fiction, costs and descriptions are not adopted as new
restrictions or original North Star canon. In particular, the legacy helpers do not
supply a variant restriction to silently enforce.

The ACT1 helper filters skills by the current class but caches the result in an unkeyed
`@cache`; its sanitation assigns `nil` to incompatible equipped choices. The bundled
helper has the same global cache but lacks that class filter and sanitation. Bindings
are checked separately. The ACT1 creation helper contains a stray regex fragment and
permissive missing-relation fallback, plus generic supply fallback. These are static
findings, not claims that the complete historical game was run or broken everywhere.

Explicit Python counterexample models retain stale class-A cache after class B is
selected, silent erasure of a previous equipped choice, and missing-relation fallback.
The models are labeled; they are not results from executing Ruby/RGSS. The extracted
contract instead rejects an incompatible complete proposal and preserves prior identity.
A class change must explicitly supply a valid complete replacement; it cannot clear
slots or silently grant generic supplies to make invalid data appear valid.

## Executable method and actual consumer

The instrument validates exact row width, required/unique headers, unique IDs,
class/background/skill foreign keys, relation flags and bounded learning levels.
Indexed candidate intake is checked against a separately scanned source-row reference.
It builds the actual C# LoadoutChecks host and executes:

- 110 class/background compatibility cases;
- 1,660 class/skill ownership cases;
- 320 source learning-boundary cases: each exact level and each available positive
  level immediately below it. Level zero is not invented as a valid player state.

All **2,090 actual C# responses** must agree with independently constructed source
expectations, in order, with exact identities and boolean outcomes. Legacy skills use
one action token only to assay eligibility; this does not implement their historical
behaviors or import their names into the original interactive catalog.

The same run executes native domain/consumer controls and the actual original
[Loadout consumer](../../north-star/csharp/Loadout/README.md) demo. The protocol requires
two completed connected journeys with discipline/outfit combinations independent of
one another, an earned action prerequisite, an empty-loadout survey success, a retained
empty-loadout walking failure and an incompatible proposal rejected without gameplay
mutation. The consumer's README and executed evidence own its exact experimental rules.

```bash
python3 -m unittest discover -s labs/world-gameplay -p 'test_*.py'
python3 labs/world-gameplay/run.py --dotnet dotnet \
  --output /tmp/world-loadout.json \
  --compare evidence/world-loadout/results.json
```

The SDK must match the existing C# pin. Outputs are forbidden throughout the maintained
workspace; builds/native/demo/study processes have bounded timeouts. Input and code
fingerprints are compared before/after execution. `--compare` checks both exact
identities and complete observations. Instrument regressions retain malformed tables,
unknown/duplicate identities, invalid flags/levels, helper variant mutations, false
native/journey reports and fabricated study booleans/outcomes.

## Decisions, limits and next frontier

Integrate only the typed compatibility, level prerequisite and explicit atomic
preparation contract into the real original consumer. Reject unkeyed class-sensitive
cache reuse, silent destructive sanitation and permissive missing-identity fallback
as adaptation policies; preserve the source files and evidence. Full legacy action
semantics, kits/items, backgrounds, class fiction, NPC/quest state and runtime recovery
remain unresolved rather than consumed by table presence.

Execution uses the pinned .NET SDK on Linux and a C#8/.NET Standard2.1 domain boundary.
It does not establish Unity import/compiler/API compatibility, licensed Editor,
Windows player, Steam, persistence, server authority, human comprehension, preference,
balance or final class canon. Fixed policies and thousands of mechanical observations
are not independent players or population findings.

Next: compare another consequential unresolved World capability or incomplete
laboratory with actual production access; investigate durable ownership and authored
NPC/quest consequences with separate consumers and controls when selected. Do not
repeat this same compatibility matrix as a new substantive unit.

The instrument also submits six malformed payloads to the actual compiled study host:
boolean schema, duplicate/unknown/missing fields, fractional level and duplicate case
identity. Each must fail without creating success output. These are protocol controls,
not additional source compatibility cases or players.
