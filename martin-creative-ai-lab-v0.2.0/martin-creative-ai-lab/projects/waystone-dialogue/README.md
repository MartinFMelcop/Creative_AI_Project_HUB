# P10 — The Last Waystone

Version **0.1.2**. A short, playable terminal scene about persuading a distracted
Keeper to repair a crossing before dusk. Helping, lying, waiting and apologizing
change later responses. Four endings close the scene; restart clears the session.
This is P10's first working destination, adapted from the recovered NPC dialogue
material. The original creative title and archive remain historical provenance.

## Play and verify

Python **3.10+**, standard library only. From the lab directory:

```bash
python3 projects/waystone-dialogue/scene.py
python3 projects/waystone-dialogue/scene.py --trace
python3 projects/waystone-dialogue/test_scene.py
```

Choose a displayed number or action name. Numbers follow the current menu as
choices become unavailable. `status` shows state, `restart` starts over, and
`quit`, EOF or Ctrl-C closes the process. Nothing is saved to disk. The optional
trace prints the selected variant and its origin, eligible variants and before/after
state as one JSON record per accepted turn. Its `speaker` distinguishes Keeper
speech from wait narration. Variant origin identifies the rule record; all
displayed wording is this scene's English adaptation. Diagnostics and rejected input
consume no turns. `scene.py` can run alone from any working directory; the source
audit in the test suite needs this lab's registry and preserved ZIP.

Try `herbs`, `bargain` for cooperation; `leave` for another route; four `lie`
choices followed by `leave` for dismissal; or twelve `wait` choices for dusk.
After an ending, choose `restart` or `quit`. These are deterministic example
paths, not evidence of narrative balance or a human playtest.

After `lie`, `herbs`, `bargain`, the Keeper now asks you to correct the false
order. Choose `apologize`, then `bargain` to finish. Lying and apologizing repeatedly
cannot improve trust above the level before the unresolved fault began.

The loose rune and the herbs covering the repair bench now appear in the opening.
Help clears space without promising a repair; a later request acknowledges that
work. Agreement answers the village's crossing request. Repeated false orders,
a withdrawn order used again, and an apology after outburst receive distinct
responses based on existing memory. Five cooldown waits show physical recovery
and print as narration. These changes add no choices or numerical effects.

## Behavior and acceptance

The initial Keeper state is stress 20, trust 45, respect 55 and mood NEUTRAL.
Stress, trust and respect clamp to 0–100. Responses use closed action/state
predicates and priority, with variant ID as a deterministic tie break; the nine
selected legacy BaseScore values are zero. There is no expression evaluation.

- Sorting herbs reduces stress by 6 and supplies the one-time prerequisite.
  Agreement also needs trust at least 40 and no unresolved lie. A new scene
  response prioritizes correction of a false order; bargaining without help
  otherwise asks for it. Refusal is an accepted turn and can reach dusk.
- False orders increase stress by 22 while pre-turn stress is below 80. The next
  false order at stress 80 or above triggers an outburst, reduces stress by 5,
  trust by 12 and respect by 6, and records the lie/outburst in session memory.
- An unresolved lie permits one apology outside an outburst: stress -12, trust
  recovery up to +6, capped at trust before that fault began. Later lies during
  the same unresolved episode keep that original ceiling, including after an
  outburst. Apology clears the obligation/ceiling and preserves historical lie
  memory. A new fault remembers the current trust level, preventing farming.
- Outburst starts a five-turn cooldown. Only waiting or leaving is then offered.
  Five subsequent accepted waits restore WARY; entry and invalid input do not
  decrement the counter. Departure during outburst selects the avoidant response.
- Cooperation, departure and dismissal are terminal. Otherwise the twelfth
  accepted action ends at dusk. A successful agreement or departure on that last
  turn takes precedence over dusk. Restart restores all initial state and trace.

The 29 checks cover these gates, boundary values, clamping, terminal behavior,
isolated sessions, replay, invalid input, real subprocess CLI flows and source
identity, plus contextual responses and speaker attribution.
[Current dialogue evidence](../../evidence/waystone-dialogue/DIALOGUE_RUN.json)
records six new methods failing on committed 0.1.1, all 29 checks passing on 0.1.2,
five before/after CLI comparisons, and identical rules across all 6,131 reachable
states and 17,994 transitions from the default initial state. Four endings remain
reachable. This comparison excludes wording and the new trace speaker field.
[Previous trust evidence](../../evidence/waystone-dialogue/TRUST_RUN.json)
records four new regression methods failing on committed 0.1.0 (five failures,
including two trust subtests), all 23 checks passing on 0.1.1, and actual old/new
CLI decisions. [Initial execution](../../evidence/waystone-dialogue/RUN.json)
remains historical. Technical M4 is
limited to this CLI contract; narrative quality and human usability await review.

## Origin and accepted changes

[Provenance](provenance.json) identifies LEGACY-001 commit
`36af1651271422ae33856e8b5d7b45702215f165`, the unchanged archive and five source
file hashes: dialogue variants, initial state, relations, profile and personality
specification. Tests compare all nine retained priorities, numeric effects,
moods, flags and events with the preserved NPC-0007 rows, and check baseline
state/relations and the five-turn cooldown. QA-only rows are excluded. The new
`SCENE_BARGAIN_UNRESOLVED_LIE` response has a scene origin in traces and is separate
from those nine preserved records. The retained apology delta +6 is a maximum
recovery; the new episode ceiling limits its effective result.

Codex wrote this English framing, responses, CLI and tests under Martin's
direction. Original tags become action-specific gates. The herbs prerequisite,
four endings, turn budget, one-apology-per-fault rule, capped trust recovery,
unresolved-lie agreement gate and cooldown expiry to WARY
are new scene rules. The stress-80 trigger follows the selected catalog; the
profile's separate threshold of 88 is deliberately unused. This is an adaptation
with recorded differences, rather than equivalent execution of the legacy RPG.
The 0.1.2 wording, including the Keeper's attendance at a council meeting, is new
scene fiction; it is not recovered canon. A pure renderer reads existing pre-turn
state, historical lie flags and outburst events without changing the selected
legacy effects. Traits and respect do not constitute a full personality system.

No fear/debt simulation, weighted trait or faction scoring, TTL memory, persistence,
assets, combat, multiplayer, Unity/RGSS binding or full game is delivered. The
historical scenario runner was inspected, not copied or rerun. No cross-project
transfer or shared library is promoted. Next: have a reader compare cooperative and
conflict paths, review clarity, repetition and the five-wait pacing, then revise only what that feedback
supports. P02 independent-candidate and P11 human-review gates remain separate.
