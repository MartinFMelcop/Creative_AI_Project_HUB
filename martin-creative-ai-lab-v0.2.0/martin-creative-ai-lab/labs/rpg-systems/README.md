# RPG Systems & Progression Lab

Mandatory P05 laboratory destination; the first operational instrument consumes
available Rave Master RPG Maker XP progression knowledge across origin boundaries.
It tests a real source-to-runtime contract rather than declaring a whole legacy
project migrated. The [source collection](../../references/AGENTS.md) remains read-only.

## Question, alternative explanations and actual finding

**Question:** can the available level thresholds and per-level budgets transfer to
a typed, engine-independent North Star C# consumer without losing gains at exact
thresholds, large grants or split reward sequences?

The source tables and nine historical QA vectors agree about the intended result.
The preserved result report records nine passes, but its actual execution path is not
reconstructed by that report.
The preserved Ruby helper reads budget columns `HP` and `SP`, whereas both the authoring
and shipped CSV use `HP_Gain` and `SP_Gain`. Its missing-key conversion projects zero
health/resolve budget in every historical vector. A successful independent calculation
therefore cannot establish that the helper and actual data were integrated correctly.
This is a **source-binding finding**, not execution of a complete RPG Maker XP game.

Competing explanations are an incorrect table, incorrect expected vectors, an
adapter/header defect, or a destination lookup/accumulation defect. The instrument
checks them separately: it preserves historical expected values, cross-checks them
against an independent linear scan and budget sums, locates actual helper column
accesses, then observes the actual new C# domain through a batch CLI. Replacing
threshold equality with strict inequality is an explicit reference mutant; it does
not pretend that a modified C# binary or the original RGSS runtime was executed.

## Available sources and ownership

The pinned reference snapshot is
`references/rave-master/snapshots/36af1651271422ae33856e8b5d7b45702215f165/source/`.
Actual inputs are enumerated with exact paths in [the instrument](run.py):

| Material | What this instrument consumes | Boundary |
|---|---|---|
| `PLAYER_LEVEL_XP_TABLE.csv` | 180 sequential thresholds and adjacent `XPToNext` consistency | Historical tuning is a research fixture, not adopted North Star pacing |
| `PLAYER_LEVEL_STAT_BUDGET.csv` | Main-stat, health and resolve gains with explicit column names | No automatic class/stat/canon adoption |
| `TEST_PLAYER_LEVEL_RUNTIME.csv` | Nine preserved historical expected vectors | Vectors alone do not establish RGSS integration |
| `RM_PLAYER_LEVEL_RUNTIME.rb` | Binary-search/additive-budget intent and actual column bindings | Source assay only; helper/game not executed here |
| Shipped budget/helper copies | Cross-check that the defect is not confined to authoring material | Preserved shipped source is not proof of a shipped game executing |

This laboratory owns progression contract research. Economy, build/release, world
systems and quality laboratories may consume its methods/results without duplicating
its authority. Other RPG capabilities—including classes, backgrounds, loadout slots,
status systems and attribute allocation—remain explicit transformation work, not
implicitly integrated by this one study.

## Execute and reproduce

Requires Python 3.11+ and the SDK pinned in
[the actual C# consumer](../../north-star/csharp/global.json). Set `HUB_DOTNET` or pass
`--dotnet` when the executable is outside PATH. No Ruby runtime, Unity Editor,
proprietary RPG Maker package, remote service or Python dependency is needed.

```bash
python3 -m unittest discover -s labs/rpg-systems -p 'test_*.py'
python3 labs/rpg-systems/run.py --output /tmp/rpg-progression.json
python3 labs/rpg-systems/run.py --output /tmp/rpg-progression-repeat.json \
  --compare evidence/rpg-progression/results.json
```

The runner builds `north-star/csharp/Checks/NorthStar.Checks.csproj` and executes that actual
compiled destination. It uses a temporary protocol/result directory; it does not
edit source tables, pins, snapshots, candidate data or product configuration. Owned
SDK/consumer processes have finite timeouts. Missing tools, build/runtime failures,
wrong SDK, incomplete/forged observations and input changes fail without writing an
accepted result. Comparison binds actual source, instrument and destination identities,
protocol, all observations and conclusions. Rebuild outputs are ignored artifacts.

## Controls and acceptance

The frozen source protocol contains **555 actual destination cases**:

- **9 historical goldens**: exact thresholds, multi-level grants, level 79/80/81,
  159/160/161 boundaries, multiple awards and experience above the historical cap.
- **537 threshold neighbors**: one below, exact and one above each threshold for
  levels 2–180. Expected lookup uses a linear reference independent of destination
  search, and budgets sum only newly crossed levels.
- **9 partition controls**: split every historical award into three nonnegative
  parts. Final level, experience and budget gains must equal the unsplit case.

The legacy header-binding assay retains **9 mismatches** in both DEV and delivered
copies. The deliberate strict-equality reference mutant changes **195 outcomes** and
is rejected by the boundary/golden controls. These are deterministic software
observations, not independent subjects or a statistical effect-size estimate.

Seven instrument regression tests reject missing/renamed columns, incomplete or
inconsistent curves, changed historical expected values, missing/reordered/forged
results, bool-as-integer substitutions, unsupported destination claims and input
replacement. The destination's own tests separately exercise its transaction and
validation contracts; successful Python expectations cannot substitute for C# execution.

## Decisions and remaining objective

[Executed results](../../evidence/rpg-progression/results.json) and
[provenance](../../evidence/rpg-progression/RUN.json) distinguish:

- **INTEGRATED:** validated threshold lookup, cumulative newly-earned budgets and
  reward partition semantics in the actual engine-independent North Star C# consumer.
- **REJECTED:** directly reusing the preserved helper's missing budget-column binding.
  The unique historical source remains intact; its defect is retained, not repaired.
- **UNRESOLVED:** adopting the 180-level pacing, numerical budgets, final classes,
  source fiction or general progression balance in North Star.

SCI-017 materially informs controls that distinguish data, adapter and destination
failure, rather than accepting self-consistent generated expectations. Engineering's
independent analysis requires a narrow portable domain seam; creative analysis preserves
player identity and authorial status rather than importing historical fiction or levels
as canon. The three analyses agreed on contract recovery; they did not constitute an
independent human study or approve final progression design.

**Next objective:** compare actual Unity adapter execution and product-level progression
choices against deeper skill/equipment/status extraction. Keep rejected direct adapter
behavior and undecided pacing distinct from successful contract transfer. Extend a
method only for a consequential question; remaining laboratory obligations cannot be
closed by assigning this result to unrelated capabilities.

No Unity Editor, Windows player, Steamworks, complete historical RGSS application,
network authority, save migration, human enjoyment or production-readiness execution
is established by this laboratory.
