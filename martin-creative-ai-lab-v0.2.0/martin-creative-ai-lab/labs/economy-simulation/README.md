# Economy & Simulation Lab — transactional crafting

Owner origin: P01; cross-origin source: P10 RPG Maker XP. This method investigates
whether typed source intake and whole-transaction validation protect resource ownership
while crafting produces a consequential original North Star preparation choice.

## Decision and independent specialties

Independent Engineering, Scientific and Creative analyses compared class/skill/loadout,
crafting, and the actual Unity tooling dependency. Crafting connects P01's complete-action
validation with P10's recipe/station data and an original C# consumer. It adds resource
conservation and scarcity beyond the existing approach/outfit and progression choices.
Class-filtered loadouts remain a valuable unresolved World & Gameplay obligation.
An empty Unity scaffold would not execute these player consequences.

Science inspected the original station and recipe bytes and applied SCI-017: hold source
bytes constant when comparing intake policies, retain meaningful failures, and distinguish
software observations from independent participants. Engineering inspects ownership,
atomicity, replay and existing implementation semantics. Creative review constrains the
original preparation alternatives and consequence; no inherited fiction or final class
canon is adopted. Specialist analysis is not independent human validation.

## Sources and reproducible method

`run.py` binds SHA-256 identities before and after execution for the preserved
`RM_CORE/DATA/CORE/CRAFTING_STATION.csv`, `CRAFTING_RECIPE.csv`, the P01
`Core/Game.cs` and `Cli/Journal.cs` validation/replay sources, the instrument and actual
C# destination files. Source provenance is the pinned Rave Master snapshot
`36af1651271422ae33856e8b5d7b45702215f165`. P01's modern .NET implementation is an
invariant source, not an assumed Unity-compatible dependency.

The CSV assay compares a width-only rival with typed station enums, bounded integer
difficulty/output/ingredient quantities, duplicate IDs, recipe-to-station references and
station-type agreement. Controlled fixtures include valid input, semantically shifted
equal-width data, missing headers, malformed widths, duplicate ingredients/IDs, invalid
quantities/enums and broken references. No recovery modifies preserved source bytes.

The runner then builds and executes the actual C# ForgeChecks and Forge demo under the
configured pinned SDK, collecting their complete JSON observations. Exact `--compare`
requires both identities and results to agree. Processes have bounded timeouts; outputs
must remain outside source inputs.

```bash
python3 -m unittest discover -s labs/economy-simulation -p 'test_*.py'
python3 labs/economy-simulation/run.py --dotnet dotnet \
  --output /tmp/economy-simulation.json
# Add --compare evidence/economy-crafting/results.json for recorded reproduction.
```

## Retained negative finding and decision

All 15 station rows match their 18-column header. All 21 recipe rows match their
20-column header. Nonetheless the station data contain **16 invalid typed fields across
six stations**, with **nine recipes referencing those stations**. Unquoted description
commas shift fields while missing trailing values conceal the problem from width checks.
For example, `WKS-VR-ALQ-01` parses access type as `mostra DC/risco.`, difficulty as
`15|20` and implementation status as `CAP-0001`.

Reject the **direct unvalidated station adapter**, not the whole collection or its
recipes. Preserve these failures and explicit implementation-status limits. Passing
recipe syntax and references does not prove historical gameplay execution or complete
item-catalog integrity. No inference is made that all referenced output items exist.

## Consumer and validity

The original North Star C# forge is the actual transactional consumer; its own README
and executed evidence own precise behavior, controls and outcomes. The library targets
C#8/.NET Standard2.1; command-line consumers execute with the pinned .NET SDK on Linux.
Compilation is not Unity import/API compatibility, Windows player, Steam distribution,
persistent or networked account ownership, production balance or player enjoyment.
The preserved RPG Maker/RGSS game is not executed by this method. Original destination
recipes and values are experiments, not approved professions, fiction or final economy.

Next: investigate persistent/server-owned transaction recovery and item/recipe catalog
integrity when a real consumer requires them; mature the other incomplete laboratories.
Preserve Godot consumers until their migration and preservation obligations are resolved.
