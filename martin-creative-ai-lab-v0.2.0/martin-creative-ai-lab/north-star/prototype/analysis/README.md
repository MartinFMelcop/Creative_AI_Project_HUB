# Return encounter evaluation

This author-facing instrument measures a concrete content question using the actual
North Star rules: **how do an initial idle delay, approach, fitting and prepared aid
change the outcome of each current return policy?** It exposes failures hidden by a
small happy-path regression set. It changes neither the shipped game nor its balance.

## Run

From the maintained workspace, with the pinned standard Godot 4.6.3 editor:

```bash
python3 north-star/prototype/tools/test_evaluate_return.py
python3 north-star/prototype/tools/evaluate_return.py --output /tmp/envelope.json --report /tmp/envelope.md --compare evidence/north-star-return-feedback/envelope.json
```

The [default protocol](return-envelope.json) crosses three approaches (Steady,
Riposte, Duelist), four current outfits, three aid choices, three resolution policies
and five idle delays (0, 30, 60, 90, 120 ticks). Each of **540 conditions** executes
twice in source and twice against the delivered PCK: **2,160 matrix takes**. Controls
and arrival preparation are additional executions, not added to that condition count.

Use `--protocol candidate.json` to select a bounded subset or other supported delays
and budgets. Fields are exact: version 1; nonempty unique string axes; sorted unique
integer delays 0..600; 2..3 repetitions; observation budget 60..7200 ticks exceeding
the last delay; at most 600 conditions. No case is sampled or omitted. Requested
outfits must be accepted by the real runtime. This is not an arbitrary skill/quest DSL.
`--timeout 180` bounds each owned native process (1..300 seconds). `--godot` selects an
explicit editor and `--pack` checks an explicit PCK; identities must match current
source. No implicit download, release build, network call or dependency installation.

The runner clears profile/capture environment overrides, uses isolated temporary XDG
paths, never runs the interactive main scene, and does not rewrite profiles or inputs.
Outputs inside the prototype/input paths are rejected. Native/schema/identity/control/
repeatability/comparison failures leave existing result files untouched. JSON and optional
Markdown are prepared before replacement. A filesystem failure during replacement is
not a cross-file transaction. Keep candidate output separate from published evidence.

## What actually executes

[The probe](return_envelope.gd) preloads `combat.gd`, `return_gate.gd`, the fitting
catalog and maintained fixed policies from the selected source/PCK. Python validates,
compares and renders; it does not duplicate combat rules. Each approach/outfit first
runs a real escort, deliberately withholding actions for 170 ticks to take damage,
then using the maintained policy. Riposte withholds guard until bolt clock 0.76s,
matching its existing regression policy. All twelve actual wounded arrival checkpoints
retain measured health, energy and gear. Return aid uses the real `Gate.begin` path.
No free healing, fabricated escort win or hand-set matrix health is used.

For each return, idle input lasts the specified number of ticks, then:

- **work:** the existing catch-work policy protects against bolts/pulses while working.
- **quiet:** the existing counter policy first disables the ward, then works the catches.
- **ground:** walk directly to the lever, hold interact until grounded, then use work.
  This policy does not invent an emergency fallback when integrity drops below cost.

The initial position stays the normal return spawn. Both catches, living exit,
resource costs, movement speed, actual threats, damage interruption and terminal rules
remain active. Takes stop on win/loss or the explicit budget; live budget exhaustion is
retained as `play`/`budget`, not silently treated as a loss or removed. The report keeps
health, integrity, final/minimum energy, action counters, first work/winch-hit/grounding
ticks, grounding interruptions, catches, exit and a full final-state trace digest.
Repeatability compares every native field and full trace identity before compressing
identical takes. Source/PCK reports must agree exactly. Input hashes are checked again
after execution to detect concurrent edits. No wall-clock timing enters observations.

Controls independently verify ordinary idle body interception/player death, off-line
fixture winch destruction, positive grounding and both legacy resolutions, insufficient
integrity rejection and paused-state immobility. The off-line control alone deliberately
places the player away from the bolt; matrix positions are never moved by fixtures.
An initial prediction that default idle would destroy the winch was contradicted: the
body intercepts the bolts. The final control retains that result and adds the separate
exposed-winch fixture; the original matrix did not change after the pilot.

Current consumer feedback adds preparation previews and grounding-attempt review.
[Current execution](../../../evidence/north-star-return-feedback/RUN.json) rebinds the
same 540 mechanical outcomes to that delivered source; only identities/trace digests
change. The original study below remains its published baseline.

## Observed result and production consequence

[The complete outcomes](../../../evidence/north-star-return-envelope/results.json),
[readable matrix](../../../evidence/north-star-return-envelope/report.md) and
[execution record](../../../evidence/north-star-return-envelope/RUN.json) preserve
all **418 wins and 122 losses**, including four zero-delay work-policy failures.
These counts describe selected deterministic conditions, not player success rates.

| Policy / aid | Won | Lost | Budget exhausted |
|---|---:|---:|---:|
| work / none | 46 | 14 | 0 |
| work / heal | 50 | 10 | 0 |
| work / brace | 52 | 8 | 0 |
| quiet / each aid | 60 | 0 | 0 |
| ground / none | 15 | 45 | 0 |
| ground / heal | 15 | 45 | 0 |
| ground / brace | 60 | 0 | 0 |

All twelve no-delay grounding combinations succeed. At 30 idle ticks, only the three
Trail wrap approaches still ground without brace; at 60/90/120 none do. In the matched
Steady/standard/no-aid case, immediate work grounds at tick 140 and wins at 534;
30 idle ticks let the first winch hit interrupt at 169, leaving insufficient integrity.
Brace permits a new full commitment: grounding at 259 and exit at 653, with one integrity
left. Healing changes health but cannot replace missing winch integrity.

The slow riveted coat's **work policy** loses at zero delay without brace, for both
Guardian techniques (heal does not change that); grounding and quiet alternatives still
win. This is a policy/geometry result, not proof that the outfit or encounter is impossible.
The counter-first policy succeeds throughout this matrix but can require substantially
more time/energy: Steady/standard/no-aid uses 1,221 ticks and reaches 54.3 minimum energy,
versus 534 ticks and no combat energy cost for immediate grounding, which spends integrity.
There is no single scalar ranking of these resource commitments.

Use this instrument when changing encounters, fitting movement or aid consequences;
expand policies and conditions deliberately when a real authoring question requires it.
The immediate design consequence is to treat brace as a meaningful recovery enabler,
and to investigate clarity/alternative work paths before adding more items or silently
retuning the cost. No runtime tuning or automatic rejection of player builds follows.

ENG-004 distinguishes verification of these rules from experience validation;
SCI-017 informs controlled factors and repeatability; SCI-050 supports an instrument
without claiming a new implemented laboratory; CRE-005 informs examining actual costs
and recovery opportunities. No protected source, historical origin or final canon is changed.

## Limits

These are fixed, implementing-agent-selected policies at 60 Hz, not an optimizer,
reaction-time distribution, independent participants or human input. Perfect phase
knowledge and ideal vector movement differ from player behavior. Initial delay changes
phase/position/resource exposure; its selected range does not establish an exact deadline
or monotonic envelope outside the sampled points. Repeated takes and source/PCK execution
are consistency controls, not independent statistical samples. No random model is used.

The instrument uses actual models in the standard editor and engine-dependent PCK;
it does not execute this external script in the standalone release template. Existing
release evidence remains separate. There is no full scene/input/persistence, physical
controller, readability, accessibility, enjoyment, balance, hardware, engine selection,
network authority, final class/build system or MMORPG readiness claim.
