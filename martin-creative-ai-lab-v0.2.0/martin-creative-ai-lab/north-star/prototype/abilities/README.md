# Committed-rush ability bench

This source-only developer consumer tests a new behavior on the **unchanged real
crossing model**. It is separate from the local adventure and loopback authority.
It does not ship in their PCK/Linux player and does not select a production engine,
final Guardian ability, specialization tree or class canon.

From the maintained workspace, with pinned Godot **4.6.3 standard**:

```bash
godot --path north-star/prototype --script abilities/play.gd
```

Compare baseline, Snap rush and Reach rush with **Tab**; **Enter** commits once.
**WASD** moves, mouse aims, **K** guards, **J** counters, **Space** uses the existing
paid step, and **E** starts the selected rush on a fresh press. **Esc** pauses this
local consumer; focus loss pauses and clears controls, and Esc explicitly resumes.
**Q** closes. A terminal result permits Enter back to fresh preparation. There is
no active swap, mid-crossing restart, saved build, gamepad mapping or network input.

| Choice | Upfront resolve | Unobstructed travel | Locked travel | Action recovery | Cooldown |
|---|---:|---:|---:|---:|---:|
| Baseline | — | Existing walking/step | — | Existing rules | Existing rules |
| Snap rush | 20 | 78 px | 0.12 s | 0.10 s | 0.70 s |
| Reach rush | 30 | 240 px | 0.30 s | 0.35 s | 1.40 s |

Aim locks on activation (current facing if aim is absent). Rush cannot begin while
guarding, stepping, recovering, cooling down or below its cost. During travel, move,
aim changes, guard, step and strike are suppressed; resolve does not regenerate.
During recovery, walking and passive recovery resume, while guard/step/strike remain
blocked. Suppressed presses never queue. Rush wins a simultaneous rush/action press;
a previous active guard or step blocks it. Field bounds still limit distance. World
time, first-contact damage, pulses and courier deadlines continue; there is **no
invulnerability**, free hit or auto-counter. Damage applies normally and does not
cancel the committed travel. Counter still needs its ordinary 12 resolve, range and live opening after recovery.

The cyan segment shows the remaining committed trajectory. Status and timers distinguish
travel, recovery and cooldown. Longer reach has a real vulnerability/response cost:
the fixed complete-journey control finishes with 4 HP versus 5 HP for baseline/Snap.
This is a particular synthetic policy, not a class or balance ranking.

## Author a bounded candidate

[The catalog](catalog.json) is consumed by the same validator in the live window and
native probe. Copy/edit it outside the source, then execute without adoption:

```bash
python3 north-star/prototype/tools/abilities.py --catalog /tmp/rush-candidate.json --output /tmp/rush-report.json
godot --path north-star/prototype --script abilities/play.gd -- /tmp/rush-candidate.json
```

The tool never replaces live data. It reports actual travel, payment, an ordinary
fixed-policy living-crossing attempt per profile, input hashes and pinned runtime.
A journey loss remains an observation; schema acceptance is not balance approval.
Results must be outside prototype/candidate inputs. Exit 0 means the candidate
executed; 2 means schema rejection with a report; 1 means a runtime/tool failure.
Inspect the candidate's actual window before any deliberate adoption. Close the
consumer before replacing data; live reload is unsupported.

The exact JSON root is `schema_version: 1` plus `rushes`, with one or two profiles
(the finite preparation screen's capacity). Each row has exactly:

- `id`: unique lowercase ASCII letter then letters/digits/underscore, 1–24 chars;
  `none` is reserved for the immutable no-rush baseline.
- `name`: 1–24 printable ASCII chars.
- `cost`: integer 10–60 resolve; `speed`: finite 250–900 px/s.
- `travel`: finite 0.10–0.40 seconds; `recovery`: finite 0.05–0.80 seconds.
- `cooldown`: finite seconds, at least travel + recovery and at most 5.

Catalogs are bounded to 16 KiB. Unknown fields, duplicate/reserved IDs, wrong types,
bad bounds/versions, unavailable or malformed data block entry, with no silent
fallback. Only this implemented rush operation exists: data cannot name scripts,
arbitrary effects, prerequisites, damage or canonical class content. Preparation
rounds its displayed numbers; the model uses the validated values. Temporal execution
is quantized to the consumer's native 60 Hz; subframe travel distance is capped.
These constraints serve the current experiment rather than a general talent schema.

## Reproduce the controls

```bash
timeout 20 godot --headless --path north-star/prototype --script abilities/checks.gd -- /tmp/ability-native.json
python3 north-star/prototype/tools/test_abilities.py
python3 north-star/prototype/tools/verify_ability_input.py --output /tmp/ability-window
```

The [execution](../../../evidence/north-star-abilities/RUN.json) retains ten matched
opening fixtures, three complete model journeys, a changed candidate's measured
execution and actual OS input/inspected images. At 360 px with 0.7 seconds OPEN,
Reach can deliver a counter after recovery where the prescribed walking, ordinary
step, Snap and immediate-strike controls cannot. At 170 px with 0.4 seconds OPEN,
Snap, walking and the ordinary step succeed; Reach's longer recovery misses it.
These are explicit constructed initial states and fixed action policies, not natural
encounter frequency, optimal play or evidence that the shorter rush beats walking.
The baseline wrapper also matches the base model's entire living journey exactly.
No independent author/player comprehension, enjoyment, competitive-build diversity,
shared-world authority or production readiness is established.
