# P10 — The Last Waystone: Flood Crossing

Browser campaign **0.5.0** connects rescue, relief morning and a consequential noon handover: hear the people present, keep resources, lend the ferry or accept Iven’s voluntary guide offer.
Night outcomes determine transport, clinical supplies and crew availability;
new decisions recover residents, deliver food, preserve seed and restore routes.
The complete operation is playable through
an illustrated map, connected flood/cargo feedback, a crossing journal, local
autosave and portable file saves. [Play and run the browser edition](browser/README.md).
No Python installation is needed by the player; its static source can be hosted
independently. The unchanged Python adventure **0.2.0** remains the rule reference
and terminal option. Choose equipment, negotiate or leave for the ferry,
reach the mill, rescue its workers, move people and medicine across the river,
and see what remains for the village tomorrow. The standalone scene **0.1.3**
is preserved and reused directly; the historical RPG sources remain immutable.

## Play in the terminal

Python **3.10+**, standard library only. From the lab directory:

```bash
python3 projects/waystone-dialogue/adventure.py
python3 projects/waystone-dialogue/adventure.py --trace
```

Choose a displayed number or action name. `look` repeats the situation, `status`
shows the full session state, `restart` starts over, and `quit`, EOF or Ctrl-C
closes the process. Invalid input and diagnostics cost no time. Nothing is saved.
Run from any working directory; keep `adventure.py` beside `scene.py`.

The game announces deadlines, consumptions, capacity and current before actions.
There are **nine flood-window beats**, including workshop choices and travel.
The workshop retains its separate twelve-turn dusk limit: continuing the talk
past the flood window cannot reopen tonight's crossing. Preparation, boarding,
unloading and ending the operation cost no beats. Rescue completed on its exact
deadline succeeds; otherwise Iven seeks the north shoal at beat five and the roof
workers leave for the north loft at beat six. They are stranded, not declared dead.

Pack two of **rope**, **timber**, **oil**. Items have competing uses; a listed
hand rescue lets you preserve rope at the cost of time. Agreement supplies the
Waystone light and opens the causeway. Ferry departure needs no agreement.
Workshop delays and lie/apology history persist into the operation and epilogue.

| Route | Decisions and consequences |
|---|---|
| Causeway | Replace boards for a permanent road, lash a temporary crossing, or mark a wet footpath. Rescue order competes with construction. Move people and cargo together or separately; medicine cannot follow the wet footpath. |
| Ferry | Choose cargo order, rescue Iven for three slots and one-beat trips, or row alone with two slots and two-beat trips. Slack/pull/surge repeats on the shared clock. Pull costs one hull; surge costs two and spoils aboard medicine. A rope guide line prevents both; timber adds buoyancy but does not waterproof cargo. Holding safely advances the current. |

Four residents, the clinic chest, Iven and next day's transport have separate
outcomes. Five ending labels summarize these facts; the epilogue distinguishes
intact medicine, spoiled cargo, stranded people, a permanent road and a retained
ferry. An early end preserves actual arrivals. Boat failure adds no arrivals and
closes the operation with an explicit emergency escape.

## Reproducible examples (spoilers)

Enter one action per line. The different outcomes are implemented behavior,
not a claim that players find the balance compelling.

- Permanent road, four residents, Iven and intact medicine:
  `rope, timber, ready, herbs, bargain, causeway, iven, roof, span, convoy`.
- Ferry with timber/oil: `timber, oil, ready, leave, ferry, iven, roof`.
  Continue with `load, board, row, row, board, row` to deliver medicine first
  and save everyone. `board, row, row, load, board, row` saves the same people
  but exposes the chest to the final surge and spoils it.
- A temporary road that saves everyone: `rope, oil, ready, herbs, bargain,
  causeway, iven_hands, roof, lash, lead, medicine`. Keeping the rope matters;
  tomorrow's crossing still needs proper boards.

## Verification and scope

```bash
python3 projects/waystone-dialogue/test_scene.py
python3 projects/waystone-dialogue/test_adventure.py
```

The unchanged scene's 32 checks cover trust, one-time help, capped apology
recovery, outburst/cooldown, four dialogue endings, CLI and archived source
identity. The adventure's 20 checks cover integrated routes, cargo-order
consequences, deadlines, shared clock/current, resource tradeoffs, capacity,
boat loss, atomic invalid input, isolated sessions, restart and actual CLI
execution outside the project directory. A graph check explores successors of
twelve real river-entry configurations, including free loading/unloading loops;
it is not exhaustive coverage of every possible workshop history.

[Milestone evidence](../../evidence/waystone-dialogue/ADVENTURE_RUN.json)
records twelve CLI playthroughs, before/after behavior, source hashes, executed
checks and a same-agent editorial/gameplay assessment. Automated contracts do
not establish enjoyment, accessibility, literary quality or commercial demand.
This is a complete **prototype operation**, not a finished commercial game.
The terminal remains session-only. The browser now supplies a graphical interface,
save/load and an original situational SVG diagram; no generated painting/audio,
combat or RPG engine binding is claimed. Browser verification and limits are in
[the new execution record](../../evidence/waystone-dialogue/BROWSER_RUN.json).

## Origin and continuity

[Provenance](provenance.json) traces NPC-0007's nine selected rule records and
five source files to LEGACY-001 commit
`36af1651271422ae33856e8b5d7b45702215f165`. Tests compare priorities, numerical
effects, moods, flags/events, initial relations and cooldown with the preserved
archive. The source archive is a selected text extract, not a complete RPG backup.
The existing scene uses closed predicates, a help prerequisite, unresolved-lie
gate and apology ceiling; it is an adaptation, not equivalent RGSS execution.

All Flood Crossing characters, English scenes, flood rules, equipment, river
routes and epilogues are new Codex-authored adaptation under Martin's direction.
No historical canon, art ownership or commercial license is inferred. The
adventure calls `Scene.act` and retains its trace rather than implementing a
second personality model. In adventure mode its cooperative ending grants the
rune, not an automatic crossing; the original `scene.py` ending remains unchanged.

The standalone conversation is still playable:

```bash
python3 projects/waystone-dialogue/scene.py
python3 projects/waystone-dialogue/scene.py --trace
```

[Prior dusk evidence](../../evidence/waystone-dialogue/DUSK_RUN.json),
[dialogue continuity](../../evidence/waystone-dialogue/DIALOGUE_RUN.json),
[trust correction](../../evidence/waystone-dialogue/TRUST_RUN.json) and
[initial scene](../../evidence/waystone-dialogue/RUN.json) remain historical.
Next: observe readers playing both days without the example sequences; refine
work-order comprehension, dramatic pacing and character scenes before expanding. No independent playtest has been
performed. A paid narrative game is a possibility, not validated demand.
