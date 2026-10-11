# P10 — The Last Waystone

Version **0.1.0**. A short, playable terminal scene about persuading a distracted
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
trace prints the selected source variant, eligible variants and before/after
state as one JSON record per accepted turn. Diagnostics and rejected input
consume no turns. `scene.py` can run alone from any working directory; the source
audit in the test suite needs this lab's registry and preserved ZIP.

Try `herbs`, `bargain` for cooperation; `leave` for another route; four `lie`
choices followed by `leave` for dismissal; or twelve `wait` choices for dusk.
After an ending, choose `restart` or `quit`. These are deterministic example
paths, not evidence of narrative balance or a human playtest.

## Behavior and acceptance

The initial Keeper state is stress 20, trust 45, respect 55 and mood NEUTRAL.
Stress, trust and respect clamp to 0–100. Responses use closed action/state
predicates and priority, with variant ID as a deterministic tie break; the nine
selected legacy BaseScore values are zero. There is no expression evaluation.

- Sorting herbs reduces stress by 6 and supplies the one-time prerequisite.
  Agreement also needs trust at least 40; bargaining without help asks for it.
- False orders increase stress by 22 while pre-turn stress is below 80. The next
  false order at stress 80 or above triggers an outburst, reduces stress by 5,
  trust by 12 and respect by 6, and records the lie/outburst in session memory.
- An unresolved lie permits one apology outside an outburst: stress -12, trust
  +6. Apology resolves the obligation without erasing historical lie memory.
- Outburst starts a five-turn cooldown. Only waiting or leaving is then offered.
  Five subsequent accepted waits restore WARY; entry and invalid input do not
  decrement the counter. Departure during outburst selects the avoidant response.
- Cooperation, departure and dismissal are terminal. Otherwise the twelfth
  accepted action ends at dusk. A successful agreement or departure on that last
  turn takes precedence over dusk. Restart restores all initial state and trace.

The 19 checks cover these gates, boundary values, clamping, terminal behavior,
isolated sessions, replay, invalid input, real subprocess CLI flows and source
identity. [Execution evidence](../../evidence/waystone-dialogue/RUN.json) records
actual commands, environment, hashes and selected play traces. Technical M4 is
limited to this CLI contract; narrative quality and human usability await review.

## Origin and accepted changes

[Provenance](provenance.json) identifies LEGACY-001 commit
`36af1651271422ae33856e8b5d7b45702215f165`, the unchanged archive and five source
file hashes: dialogue variants, initial state, relations, profile and personality
specification. Tests compare all nine retained priorities, numeric effects,
moods, flags and events with the preserved NPC-0007 rows, and check baseline
state/relations and the five-turn cooldown. QA-only rows are excluded.

Codex wrote this English framing, responses, CLI and tests under Martin's
direction. Original tags become action-specific gates. The herbs prerequisite,
four endings, turn budget, one-apology-per-fault rule and cooldown expiry to WARY
are new scene rules. The stress-80 trigger follows the selected catalog; the
profile's separate threshold of 88 is deliberately unused. This is an adaptation
with recorded differences, rather than equivalent execution of the legacy RPG.

No fear/debt simulation, weighted trait or faction scoring, TTL memory, persistence,
assets, combat, multiplayer, Unity/RGSS binding or full game is delivered. The
historical scenario runner was inspected, not copied or rerun. No cross-project
transfer or shared library is promoted. Next: have a reader play cooperative and
conflict paths, review dialogue/consequences, then revise only what that feedback
supports. P02 independent-candidate and P11 human-review gates remain separate.
