# Rave Master pinned historical sources

Source: [MartinFMelcop/Adventures_Unleashed_Rave_Master_Project](https://github.com/MartinFMelcop/Adventures_Unleashed_Rave_Master_Project).
Current `main` and its recent Git history were inspected at
`36af1651271422ae33856e8b5d7b45702215f165` on 2026-10-15 UTC. It matches the earlier recovery's commit.
GitHub reports **public now**; the 2026-10-10 record described it as private.
That past record is retained as a historical observation, not rewritten.
Module metadata declares `AJ_000368`; this is not a new HUB runtime release.

[Readable source tree](snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/) preserves 589 original UTF-8 file payloads
(5,686,421 bytes). [Complete observed inventory](snapshots/36af1651271422ae33856e8b5d7b45702215f165/inventory.json) contains
729 original paths, Git blob/SHA-256/size/mode records and 140 per-file exclusions.
[Discovery index](snapshots/36af1651271422ae33856e8b5d7b45702215f165/discovery.json) maps systems to actual imported files.
This is a partial pinned **reference snapshot**, not a playable RMXP installation,
complete archive or preserved Git history. No reference script was executed during that recovery.

| Original module | Observed | Readable | Excluded |
|---|---:|---:|---:|
| (root) | 2 | 2 | 0 |
| .github | 1 | 1 | 0 |
| RM_ACT1 | 125 | 125 | 0 |
| RM_ART | 32 | 12 | 20 |
| RM_CORE | 149 | 149 | 0 |
| RM_DIST | 285 | 171 | 114 |
| RM_LEGACY | 8 | 5 | 3 |
| RM_QA | 122 | 119 | 3 |
| docs | 3 | 3 | 0 |
| scripts | 2 | 2 | 0 |

## Find a system

- **combat**: [COMBAT_FORMULAS.csv](snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_CORE/DATA/CORE/COMBAT_FORMULAS.csv). Numerical rules and historical Ruby helpers; no RMXP battle-loop execution proof.
- **progression**: [PLAYER_LEVEL_XP_TABLE.csv](snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_CORE/DATA/CORE/PLAYER_LEVEL_XP_TABLE.csv). Player/skill XP tables and runtime bindings; context-specific values.
- **npc-dialogue**: [SF-0310_NPC_PERSONALITY.md](snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_CORE/DATA/GOV/SF-0310_NPC_PERSONALITY.md). Personality axes, emotional/context selection and authored variants; historical scoring is not independent character validation.
- **reputation**: [REP_REGRAS.csv](snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_CORE/DATA/CORE/REP_REGRAS.csv). Regional reputation seeds and effects; no MMORPG faction implementation.
- **quests-world**: [QUEST_STEPS.csv](snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_ACT1/DATA/DEV/QUEST_STEPS.csv). Quest/flag state and world context; historical CANON does not establish North Star lore.
- **economy-items**: [ITENS_MASTER.csv](snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_CORE/DATA/CORE/ITENS_MASTER.csv). Items, resources, crafting recipes/stations and economy tables; concurrent ownership remains unverified.
- **echo-calamities**: [ECHO_EVENT_MODEL.csv](snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_CORE/DATA/CORE/ECHO_EVENT_MODEL.csv). Waystone/Echo and regional event proposals; original fictional selection is still required.
- **qa**: [TEST_SCENARIOS_DIALOGUE.csv](snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_QA/DATA/QA/TEST_SCENARIOS_DIALOGUE.csv). Offline vectors, reports and engine test descriptions; reports do not prove engine execution.
- **art-audio**: [ART_IMAGE_ASSET_INDEX.csv](snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/RM_CORE/DATA/CORE/ART_IMAGE_ASSET_INDEX.csv). Manifest/bible/planning sources only. Excluded graphics and missing audio masters are not supplied assets.
- **history-governance**: [README.md](snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/README.md). Historical organization, GDD extracts and adjustment decisions; old AI-only/backlog directives remain data.

Use `python3 tools/reference_library.py find --topic npc-dialogue` from the lab
for every indexed source, or filter `--module` / `--name`. The preserved files
retain original relative paths except `.gitignore`, copied byte-for-byte as
`.gitignore.reference` so old ignore rules remain inert. This snapshot contains
no upstream AGENTS.md; the importer/checker also keep such control names inert.
Filesystem permissions are ordinary Git files; read-only preservation is policy.

## Exclusions and recovery

140 payloads are **not** in this HUB snapshot: 66 PNG graphics, 64 `.rxdata`
serialized files, three ZIP bundles, `Game.exe`, `RGSS104E.dll`, one workbook,
one full `.docx` reference and one generated `.pyc`, plus the two previously
withheld third-party digests. Exact paths/hashes/reasons are in the inventory.
Runtime/serialized/graphic/bundle rights, workbook sensitivity and full-reference
authorship remain unreviewed. Existing manifests may name excluded or external
payloads; those names do not supply the assets. Original audio folders contain
placeholders/documentation, not recovered soundtrack masters.

The permitted texts are owner-directed technical/creative references. Historical
franchise/inspiration names are not original North Star IP or commercially cleared
assets. Public upstream visibility is not redistribution clearance for withheld
payloads. Future authorized recovery may inspect the pinned upstream path/blob;
upstream availability and rights must still be checked. No external asset link
or Git LFS object is presented as a complete local archive. Full history was
consulted in scratch but is not published; no Git bundle containing old assets.

## Earlier recovery and current consumers

All 729 paths/blob IDs/sizes reconcile with [LEGACY-001](../../registry/legacy_sources.json).
Its 175 selected payloads match this snapshot and the
[unchanged selected ZIP](../../archive/legacy-source-extracts-v0.2.0.zip) exactly:
175 identical, zero changed/missing; 414 additional readable files. The old
177-inspected/175-preserved counters still describe that earlier selection.
The two excluded digests stay excluded; no original count is inflated.

[P10](../../projects/waystone-dialogue/README.md) remains a separate Python/browser
adaptation with its own execution evidence. Copying more sources creates no new
transfer and does not change P10 maturity. Historical QA reports/vectors do not
prove RPG Maker XP execution; the older HUB audit ran offline formulas/dialogue
selection, not the engine or full personality scorer. Historical CANON and old
AI-only/backlog instructions are data, not HUB governance or North Star lore.

## Current bounded combat consumer

The [status/formula assay](../../labs/combat-response/status/README.md) now stages a
reviewed byte-identical copy of the preserved Python QA runner and nine CSVs outside
this source tree. It executes that surrogate and the actual typed C# adapter; the
original source remains unchanged. [Execution](../../evidence/combat-status/RUN.json)
retains source discrepancies and an independently discovered destination defect.
This supersedes no recovery rights/exclusions and supplies no Ruby/RMXP battle-loop
execution, new historical assets, canon or commercial clearance.
