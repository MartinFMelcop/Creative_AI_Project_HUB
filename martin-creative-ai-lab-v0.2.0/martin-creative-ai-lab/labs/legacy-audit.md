# Accessible origin audit and consumption boundaries

This initial transformation audit enumerates the actual P01–P11 source roots,
assets, controls, recorded evidence and retained ZIP/PCK files. It does not equate
an inventory, old QA result or source function with newly executed behavior.
[The reproducible inventory](source-inventory.json) owns counts, byte sizes,
classification and ordered tree hashes. Existing `MANIFEST.sha256` owns individual
maintained-file identities. Run from the maintained workspace:

```bash
python3 tools/inventory_origins.py --check labs/source-inventory.json
python3 tools/inventory_origins.py --files --output /tmp/origin-files.json
python3 tools/test_inventory_origins.py
```

`--files` emits the complete classified file/owner/hash listing to scratch; the
maintained summary avoids duplicating the entire manifest. Every selected file is
read for identity, every ZIP member for payload comparison. Semantic reading is
selective and recorded below. P07/P08 share files with other origins; their per-origin
counts intentionally overlap, while the unique-source count does not. They are not
independent effort measurements. P09 has no supplied historical delivery case;
current HUB CI/build tools are available production methods, not recovered P09 history.

## Material implementation checkpoints across all origins

| Origin → responsible laboratory | Actual inspected implementation/data | Available behavior and consumption decision |
|---|---|---|
| P01 → Economy & Simulation | `projects/eclipse-fair/Core/Game.cs`, `rules/baseline.json`, `Checks/Program.cs` | The complete transaction is validated before changing movement, currency or turn; minted/spent/stolen counters and deterministic forecasts are explicit. **UNRESOLVED** for a North Star economy/ownership consumer; its contemporary C# records/immutable collections cannot be presumed Unity-compatible. |
| P02 → AI Evaluation & Quality | `evaluations/chat-send-buffering/run.py`, `test_runner.py` | Pinned starter/evaluator Git snapshots, compatible dependency-lock checks and 17 evaluator-owned outcomes exist. **UNRESOLVED** for a newly adapted lab instrument; retained calibrated CI use is real origin evidence, not autonomous quality judgment. |
| P03 → Input, Timing & Interaction | `projects/tokyo80s/dist/core.js`, timing/hold/review tests | Scoring uses song seconds, ordered due events, explicit head/tail states and finite-input validation. **UNRESOLVED** for another consumer; song-time judgment is not authoritative realtime combat timing or measured human latency. |
| P04 → Narrative & Continuity | `projects/lich-cistern/tools/check_editions.py`, manuscript/edition definitions, pinned literature sources | Complete manuscript/order is checked against EPUB/PDF output; bilingual authorial works and rights/provenance remain separate. **UNRESOLVED** for a new narrative continuity method; exact text verification is not literary quality or canon approval. |
| P05 → RPG Systems & Progression | `projects/cinderwatch/Core/Content.cs`, `Game.cs`, recovery checks | Explicit row screening, shared supplies, locked enemy intentions and save/recovery contracts are available. **UNRESOLVED** for direct domain reuse; the new XP study below consumes P10 knowledge across laboratory boundaries. |
| P06 → Combat & Responsiveness | `projects/veil-arena/tests/parry.gd`, `arena.gd`, existing `labs/combat-response/run.py` | Paid contact/timing methods already have a lab pilot and real North Star crossing evidence. Existing scoped **INTEGRATED** action/contact adaptation remains recorded in `north-star/capabilities.json`; it does not consume all P06 content or close research. |
| P07 → Visual Identity & Animation | Art/atlas catalogs and `projects/cinderwatch/Native/Presentation.cs` | Original paintings, state atlases and inset portraits have actual origin consumers. **UNRESOLVED** for a new visual laboratory instrument; supplied asset provenance does not approve North Star identity or exclusive commercial rights. |
| P08 → Audio & Adaptive Music | `projects/tokyo80s/tools/render_track.py`, `projects/cinderwatch/tools/render_feedback.py`, audio catalogs | Seeded original synthesis, score-aligned charts and PCM cue identities are executable production methods. **UNRESOLVED** for an adaptive North Star music consumer; regenerated signals do not establish physical listening quality. |
| P09 → Build, Release & Operations | Actual `.github/workflows/lab-checks.yml`, export/check tools and package members | Pinned tools, source/delivered/rebuilt checks and real pipeline consumers exist in the HUB. **UNRESOLVED** for the mandatory Windows/Unity release method; no historical case, Unity build or Windows execution is inferred. |
| P10 → World & Gameplay Systems | Preserved XP corpus below; `projects/waystone-dialogue/browser/dist/deferred-request.js` | Real adaptation freezes prior receipts, refreshes current world facts and requires fresh voluntary offers. XP knowledge spans World, RPG, Combat, Economy and Narrative labs. The typed progression contract is selected for actual lab/C# destination evaluation, not a Ruby/franchise port. |
| P11 → Networking & Persistence | `projects/realtime-integration-lab/server.cjs`, room/storage tests; three pinned `websocket/` ZIP files | Historical server only logs received messages; the historical HTML emits without displaying incoming messages. The maintained server validates/acknowledges/broadcasts, with later room/save consumers. **UNRESOLVED** for new extraction; chat acknowledgements are not authenticated game authority. |

These checkpoints inspect actual implementations rather than relying exclusively on
project summaries. Existing origin results remain linked through the project registry;
this audit reruns inventory controls, not every historical consumer. Formal ongoing
consumption states and their consumer/evidence bindings belong in
[the origin record](origins.json), rather than a second competing registry here.

## Mandatory RPG Maker XP investigation

All paths below are inside the pinned [readable XP source tree](../references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/).
That collection preserves 589 readable files out of 729 observed paths, with 140
explicit exclusions. It is not a complete playable RPG Maker XP installation.
The three other archived P11 source files and 175 selected XP extracts remain in the
pinned preservation ZIP; those XP files overlap the readable snapshot.

`ScriptsCustom` and `RM_ACT1/DATA/DEV/RGSS` identify project-specific helper locations
and declared RGSS1 APIs. They do not prove exclusive authorship of every algorithm.
Engine classes such as `Game_System`, `Window_Command`, `Graphics` and `Input` are
bundled/proprietary runtime dependencies, not supplied original HUB technology.
Excluded `.rxdata`, `Game.exe`, `RGSS104E.dll` and graphics are not silently recovered.
Historical franchise names, character rosters and old CANON declarations are source
context, never North Star approval or redistribution clearance.

| Investigated domain / material sources | Actual finding | Bounded disposition and next owner |
|---|---|---|
| Flow, initiative, targeting, formation: `RM_CORE/DATA/CORE/REGRAS_DE_COMBATE.csv`; `RM_ACT1/DATA/DEV/RGSS/RM_COMBAT_RUNTIME.rb` | The table specifies global rounds, one ordinary action, AGI extra turns, three lines, paid commitment/fizzle and two debuff gates. The Ruby header explicitly says full battle-loop integration is follow-up work. | **UNRESOLVED** for adaptation in Combat/RPG labs. A helper's existence does not verify the timeline, intercept, reaction stack or actual RMXP battle loop. Current realtime movement is not automatically replaced by these turn-based rules. |
| Formulas and mitigation: `COMBAT_FORMULAS.csv`, `RM_COMBAT_RUNTIME.rb` | ACC/(ACC+EVA) and efficacy/resistance ratios have clamps/epsilon; mitigation uses level-scaled K and rounded damage. CSV is optional in the helper header, while embedded defaults actually drive its formulas. | **UNRESOLVED** for calibrated Combat evaluation. Data/runtime synchronization must be tested before claiming data-driven formulas; numbers are historical hypotheses. |
| Buffs/debuffs/status: `STATUS_EFFECTS.csv`, `REGRAS_DE_COMBATE.csv`, `RM_QA/DATA/QA/TEST_COMBAT_REAPPLY.csv` | Poison 6%, bleed/burn 3% max-HP ticks, heal/attack multipliers, two gates, minimum-one rounded duration and additive reapplication are specified. The helper computes ticks/duration but leaves the actual status container to its caller. | **UNRESOLVED** in Combat/RPG labs: evaluate stacking bounds, tick order and direct-hit versus DOT defense before integration. Three reapply vectors are offline expectations, not an engine status test. |
| Classes/backgrounds: `RM_CHARACTER_CREATE_RUNTIME.rb`; `ACT1_CLASSES_CANON.csv`, background/relation tables | The UI helper contains malformed/incomplete inserted source (a stray `/)` after its CSV split expression and broken local-variable context), substring matching for initial-kit backgrounds and fallback resources. Its header says no mechanical loadout effect, while later functions grant items/money. | **REJECTED** as a direct-port implementation, based on inspected source inconsistency, without executing it. Class/background requirements remain **UNRESOLVED** in World/RPG/Economy; use typed IDs, explicit validation and original North Star author choices. |
| Skills/passives/equipment slots: `RM_UI_SKILL_EQUIP_RUNTIME.rb`, `RM_UI_PASSIVE_EQUIP_RUNTIME.rb`, `CLASS_SKILLS_MASTER.csv` | Four debug skill slots filter by class and sanitize unknown equipped IDs to nil. The master has 350 rows with learn levels and technical prose; row presence is not an implemented ability. | **REJECTED** direct adoption of silent save/loadout deletion; requirements remain **UNRESOLVED** in World/RPG. Require explicit compatibility/migration and actual ability execution. |
| Levels/attributes/XP: `PLAYER_LEVEL_XP_TABLE.csv`, `PLAYER_LEVEL_STAT_BUDGET.csv`, `RM_PLAYER_LEVEL_RUNTIME.rb`, nine `TEST_PLAYER_LEVEL_RUNTIME.csv` rows | There are 180 threshold and budget rows. Binary search uses inclusive TotalXP thresholds and cumulative gained-level budgets. The budget CSV names `HP_Gain`/`SP_Gain`, while Ruby reads `HP`/`SP`, coercing absent values to zero. Historical test expectations contain nonzero bonuses. | The uncorrected field-binding path is **REJECTED** for reuse. The validated threshold/cumulative-budget contract proceeds to the [RPG Systems lab](rpg-systems/README.md) and real C# consumer; actual INTEGRATED claims require its recorded execution. The 180-level pacing, respec costs and fiction remain **UNRESOLVED** author/design work. |
| Equipment/inventory/crafting: `ITENS_MASTER.csv`, `CRAFTING_RECIPE.csv`, `CRAFTING_STATION.csv`; loadout helper | The item master has 372 rows; 21 recipes and 15 stations name inputs/outputs/unlocks. Inspected recipes say `Implementar`/`Em análise`. A station row has shifted fields after an unquoted comma (access type becomes `mostra DC/risco.` and implementation status becomes `CAP-0001`). Free-text matching/fallback grants are not transactional ownership. | **UNRESOLVED** in Economy/RPG/World: validate IDs, atomic spend/output, unlocks and failure behavior against an actual consumer. Do not present data tables as implemented crafting. |
| NPC personalities/dialogue: `SF-0310_NPC_PERSONALITY.md`, `NPC_PROFILE.csv`, `NPC_STATE.csv`, `RM_DIALOGUE_SCORING_RUNTIME.rb` | Thirty profile/state rows, ten axes, contextual conditions, weighted scores and score→specificity→priority→ID tie-breaks are present. Inspection of `choose_variant` also finds test-context `idx`/`r` references in its main path; deterministic scoring is not a validated psychology model. | **UNRESOLVED** in Narrative/World; isolate the selector, validate scope/effects and compare authored variants. A direct blind port is inappropriate; current Waystone causal choices do not establish the entire original scorer's execution. |
| Reputation/factions: `RM_REPUTATION_RUNTIME.rb`, `REPUTATION_RULES.csv`, `FACTION_NORMS.csv` | The helper clamps −3…3, excludes zero, requires a magnitude-two sign crossing and supplies hard-coded seeds. `effects_for` returns an empty array despite 420 effect-table rows; 18 faction-norm rows are separate data. | **UNRESOLVED** in World/Narrative/Economy. State arithmetic exists, but faction consequences/effects and original North Star social meaning still need a real consumer. |
| Quests/events/world: `QUEST_STEPS.csv`, `RM_UI_QUEST_JOURNAL_RUNTIME.rb`, `RM_FLAGS_EVENTS_RUNTIME.rb` | Seventy-three quest-step rows declare triggers. The debug journal can manually activate/complete; flag stores have global/NPC/relation scopes, and recent events expire at `exp <= turn`. | **UNRESOLVED** in World/Narrative/Networking. Debug advancement is not proof that authored world events execute triggers, rewards or persisted progression correctly. |
| Historical QA/helpers: `RM_QA/DATA/QA/TOOLS`, combat/level/dialogue vector CSVs and reports | Python offline runners and Ruby debug helpers exist, while inventory reports name excluded RMXP bundles/backups. The level header discrepancy demonstrates why reports cannot replace actual destination tests. | Reuse appropriate vectors as controls; **UNRESOLVED** cases require execution/negative controls. Existing missing runtime data is an explicit gap, not an instruction to recover indefinitely or claim full game execution. |

No preserved script was executed by this inventory/audit. The separately executed
progression study distinguishes its source-model comparisons and C# destination
execution from missing Ruby/RGSS/Unity/Windows execution. A static rejection above
rejects the named adoption path, not preservation of the source or every idea in it.

## Artifact lifecycle audit

The actual inventory contains **27 ZIP/PCK packages**, **583,126,530 bytes** of tracked
package blobs (about **556.11 MiB**). ZIP members total **1,410,613,373 uncompressed
bytes**; this different metric must not be described as repository size or savings.
There are **zero byte-identical whole packages**. Large identical embedded runtimes
are detected (including roughly 71 MB runtime payloads across releases), but each
version can still contain distinct PCKs, source, assemblies, metadata and notices.

Consequently this audit proves **no safe whole-package deletion**. It performs no
removal and no history rewrite. Actual consumers include source/delivered/rebuilt CI,
release download links, package provenance/source-identity checkers, prior-version
comparison fixtures, standalone players, and pinned archive cross-checks in
`tools/reference_library.py`. Old save schemas/source copies/notices can be unique
without appearing as a direct import in current source.

The selected preservation ZIP is not an obsolete release: source-integrity contracts
bind its 175 XP and three P11 files. The five original Brains, literature works,
reference snapshots and their pins remain untouched. An external URL/Git history
alone is not verified preservation or clearance.

The Build & Operations lab must resolve version-by-version consumers, licenses,
required recovery and a verified retained artifact destination before artifact retirement.
Future North Star distributions prioritize Windows; old Linux origin exports do not
impose new independent product release duties. Current functioning Godot comparisons
remain preserved until their actual migration consumers/regressions are resolved.

This execution replaces unconditional historical runtime/Linux rebuild work with the
[changed-path CI selector](../tools/ci_scope.py). Its [12 local controls](../tools/test_ci_scope.py)
include actual Git addition, deletion and rename fixtures. Historical runtime jobs run
when their consumers or dependencies change; integrity remains unconditional, and the
new C# capability has a separate job. Workflow changes, unknown shared paths, manual
runs and empty diffs select the full relevant runtime suite conservatively. Thus an
unrelated increment no longer automatically rebuilds every historical Linux player;
retained packages, source and affected consumer checks remain intact. These local
selector results establish routing behavior, not a published CI result. Actual workflow
execution must be checked separately after publication. No artifact-deletion or storage
saving is claimed from the repeated embedded runtime bytes.

## Validity and continuing obligations

The inventory is reproducible discovery and the audit is implementing-agent technical
inspection, not an independent scientific/human review. Source presence, execution,
correctness, gameplay value, creative authority, rights and product integration are
separate claims. All eleven destinations remain mandatory; preserved-but-unconsumed
capabilities remain UNRESOLVED until an actual justified INTEGRATED/REJECTED outcome.
A new iteration must select consequential unresolved domains and improve operational
research or a real consumer, rather than repeatedly regenerating this inventory.
