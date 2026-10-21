# Authoring local equipment

[fittings.json](fittings.json) is the live fitting catalog. The same
[runtime contract](../fittings.gd) validates it for combat, workshop presentation and
the authoring tool. No generated copy or second schema is maintained.

Copy the catalog outside the consumer, edit a candidate, then run from the maintained lab:

```bash
python3 north-star/prototype/tools/fittings.py check --catalog /tmp/candidate-fittings.json --output /tmp/fitting-report.json
```

The tool stages current source and candidate data in a temporary project. It never
replaces the maintained catalog. Godot validates the candidate, executes the real
workshop and crossing scene, measures actual effects, and runs both approaches through
escort and return objectives for each fitting. Reports distinguish schema rejection
from failed execution. Fixed-policy failure is a reason to inspect the design/method,
not proof that a mechanically valid item is impossible or unbalanced for people.

The JSON object contains exactly `schema_version: 1` and a `fittings` array. Each row
has exactly these fields:

| Field | Current consumer contract |
|---|---|
| `id` | Unique lowercase identifier, letters/digits/underscore, starts with a letter, at most 24 characters |
| `name` | 1–22 printable ASCII characters for this finite room's labels |
| `health` | Integer 3–7; health and maximum health at a fresh fitting |
| `movement` | Multiplier 0.6–1.3 for walking, guarded walking and paid-step distance |
| `recovery` | 10–30 energy per simulated second while unguarded, including movement; cap remains 100 |
| `visual` | `plain`, `plates`, `strips` or `sash`; original procedural presentation, never a script path |
| `station` | `[x,y]` inside x=220–930, y=390–470; benches at least 220px apart |

The room supports one to three craftable benches plus required `standard` clothing.
Standard retains 5 health, movement 1, recovery 18, plain visual and a null station.
Catalog size is bounded to 16 KiB. Unknown fields, wrong types, invalid JSON, duplicate
IDs, unavailable data and invalid placement block play; there is no silent fallback.
Bounds constrain this prototype, not a general RPG item schema or a balance guarantee.

The shipped Field sash trades one health for 26/s unguarded recovery without changing
movement. Riveted/trail/default values retain their earlier contracts. Guard drain,
impact/ability costs, cooldowns, damage, courier rules and rewards are unchanged.
One completion spends one session-only blank; explicit recycling restores it. Gear
cannot be swapped during play, does not persist to disk and cannot heal at return entry.

Inspect a successful candidate's actual scene before replacing the maintained data.
Close the running consumer before replacement; live catalog reload is unsupported.
Names, numbers and motifs remain experimental creative proposals. Additional stat
axes, silhouettes, translations or a larger room need deliberate implementation and
verification; this tool does not generate arbitrary effects or approve canon.

After adoption, rebuild the PCK and Linux delivery. Their source identities include
the JSON, so stale/missing/modified catalog payloads fail delivery verification:

```bash
python3 north-star/prototype/tools/fittings.py verify --output /tmp/fitting-delivery.json
python3 north-star/prototype/tools/test_fittings.py
```
