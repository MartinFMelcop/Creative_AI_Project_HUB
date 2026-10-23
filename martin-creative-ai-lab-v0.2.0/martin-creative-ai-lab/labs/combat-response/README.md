# Combat response instrument

One working pilot laboratory instrument, using the **unchanged P06 Veilbreak
0.6.0 native scene** as its origin. It measures a bounded question about defense
and commitment; it does not implement North Star classes or select its engine.

## Question and design hypothesis

Do parry, directional dodge and a single seal produce different defensive and
offensive opportunities under the same phase-one sweep warning?

The hypothesis defined for the pilot is that these responses are mechanically
distinct: a close, live parry prevents sweep damage and opens an early blade
counter; dodge trades position and a movement commitment for avoidance; a
single seal applies pressure but does not interrupt this sweep. This would be
weakened if the same successful timing/position and early counter outcome held
across all responses, or if the controls could not detect real damage and
rejected inputs. It is a hypothesis about this origin's rules, **not** a test of
whether people perceive distinct classes or enjoy their choices.

North Star's direct character-identity objective motivates the question
(Creative Brain **CRE-001**). Differentiation through decisions, rather than
labels or stats, is the candidate design concern (**CRE-012**, **CRE-084**, both
hypotheses; **CRE-008** preserves that editorial status). Engineering
**ENG-004/015** separates verifiable needs from a premature engine/shared-module
choice. Scientific **SCI-005/017/050/051** supplies falsifiable predictions,
controls, bounded laboratory scope and preservation of the working origin.
All three indices and these complete chapters were consulted before coding.
The first exploratory matrix run informed additional event/resource reporting;
the input matrix stayed fixed. This protocol was not externally pre-registered.

## Run from the maintained lab

Requires Python 3.11+ and **Godot 4.6.3** standard or .NET. The tested standard
engine needs no SDK, Python package, remote service or vector database.

```bash
python3 -m unittest discover -s labs/combat-response -p 'test_*.py'
python3 labs/combat-response/run.py --godot godot \
  --output /tmp/combat-response.json \
  --compare evidence/combat-response/results.json
```

Pass an executable path to `--godot` when it is outside `PATH`. Omit `--compare`
to collect another bounded run without replacing the committed evidence. Use
`--protocol path.json` for an explicitly changed input matrix. `--timeout`
bounds each owned engine process (120 seconds by default, maximum 600). A
failure leaves the requested result unwritten. Output is deterministic JSON;
version, protocol, runner/probe and actual origin file hashes identify the run.

The runner imports the origin's existing assets into its ignored `.godot/`
cache, uses owned temporary XDG data/config/cache paths and closes each engine
process before returning. It does not edit origin source, media, distributions
or saves. Import and probe execution are separate checks: a successful import
alone is not an experiment result. A nonzero exit, script/parse error, missing
result, incomplete matrix, changed order or inconsistent repetition fails.
Comparison additionally rejects any changed result or pinned input/source hash.

## Protocol and controls

[scenarios.json](scenarios.json) contains **28 fixed cases**, each repeated twice.
No random seed is needed: the source sweep and these inputs are deterministic.
Two repetitions check repeatability; they are not independent participants or
a statistical sample of gameplay.

[probe.gd](probe.gd) loads `projects/veil-arena/arena.tscn` through the real Godot
resource importer. It disables only that scene's automatic physics callback
and calls its actual `step_fight` once per native physics frame at 60 Hz.
`move_and_slide`, warning/contact, costs, projectile collision, parry and blade
damage all remain in the origin. No extracted Python combat approximation or
copied rule kernel determines an outcome.

Each take resets the actual scene to its normal six health, 100 resolve and
160 boss health; the Warden starts at `(650,400)` and the player normally 85px
to its left. The real `_start_pattern` starts its 850ms phase-one sweep. A
neutral calibration observes first real damage, rather than assuming its tick.
All matrix responses are scheduled relative to that contact; observation lasts
100 ticks (1.667 simulated seconds). The same blade request at tick 53 probes
early opportunity and can be rejected or miss. It is not automatically delayed
until each response is ready.

- Neutral near/far cases verify damage detection and geometry.
- Parry, outward/inward dodge and seal are pressed 2, 5, 8, 12 or 18 ticks before
  calibrated contact. These are controlled traces, not reaction-time estimates.
- Parry at 110/111/150px tests range against the wider sweep and shorter blade.
- No-resolve controls set resolve to zero **at the response request**; ordinary
  regeneration and attempted movement still apply.
- One controlled echo is placed at the player's position to mature on the same
  contact tick. Its real `_update_echo` path tests whether a successful parry
  incorrectly implies general protection. This imposed overlap is not a claim
  that this phase-one encounter naturally schedules that echo.

Every outcome is retained, including failures. Events expose requested and
accepted actions, before-contact state, actual damage/parry transitions, boss
stage changes, resources and positions. `first_open_tick`, minimum resolve and
the remaining ward pressure complement the damage totals.

## Executed result

[Complete machine-readable outcomes](../../evidence/combat-response/results.json)
and [execution/provenance record](../../evidence/combat-response/RUN.json) identify
the baseline, engine, commands, environment failures and artifact hashes.

The unchanged origin alone provides play and regression fixtures. This pilot
adds repeatable cross-response measurement and explicit controls without
changing its game. The 56 final outcomes repeat exactly; neutral collision
calibrates at tick **52** (0.8667 simulated seconds).

| Response at 85px | Actual outcome under the fixed early blade request |
|---|---|
| Neutral | One health lost; 4 guarded blade damage. |
| Parry, lead 5 or 8 ticks | No health lost; real parry and 24 blade damage. |
| Parry, lead 2/12/18 | One health lost; guard too late/early, 4 guarded damage. |
| Dodge away, all five timings | No health lost; ends 219.333px away; early three blade requests rejected during dodge, later two miss. |
| Dodge inward, lead 2/5/8 | No health lost; ends about 42.012px away; early blade request rejected during dodge. |
| Dodge inward, lead 12/18 | Invulnerability has expired at contact; one health lost. |
| Single seal, all five timings | One health lost; the latest request is interrupted before release, other releases deal 8 damage without interrupting the sweep. The later common blade adds 4 guarded damage. |

At **110px**, parry succeeds but the 103px blade cannot reach; at **111px** and
150px the same guard fails against the sweep. Both no-resolve defenses are
rejected. In the controlled overlap, the sweep is parried but the echo still
takes one health. A successful parry opens the boss at tick 52; the ordinary
sweep recovers at tick 62, a measured 10-tick (166.7ms) earlier opportunity.
These observations support different response envelopes in
this bounded origin. They do not establish an optimal policy, overall balance
or a generally superior defense.

## Limits and destination

This is one stationary phase-one warning at 60 Hz on the recorded Linux engine.
The early-counter probe deliberately holds its request time fixed; it does not
compare the best later counter for each response. Distance, remaining resolve
and health are observed separately so a damage-only ranking cannot hide that
choice. No charge/wave/phase-two campaign, network, latency, accessibility,
physical controller or independent player test is implied. Visual/audio assets
are loaded but this headless run does not assess readability or listening.

The pilot has an actual laboratory consumer of P06; **North Star still has no
destination code consuming this instrument or its mechanics**. Guardião,
Duelista, multiplayer and class identity remain unimplemented/unvalidated here.
The actionable result is a measured set of distinct commitments and failure
cases for a future bounded character experiment, not permission to copy P06's
fiction or declare a final engine/class system.

## Additional source-bound status method

The [status/formula assay](status/README.md) now consumes selected P10/Rave Master
requirements into [The Treatment Line](../../north-star/combat-study/README.md),
an actual separate original C# encounter. [New evidence](../../evidence/combat-status/RUN.json)
binds 49 historical cases, strict destination controls and visible counterplay. This
does not rerun or replace the P06 native pilot above, nor claim that its parry method
has been ported. Existing Cinderwatch individual-turn scorch remains incompatible and
preserved. Full source combat/runtime, human experience and Unity/Windows remain open.
