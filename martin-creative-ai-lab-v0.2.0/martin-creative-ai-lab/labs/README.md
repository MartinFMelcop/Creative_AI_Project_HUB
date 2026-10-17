# Applied research laboratories

The HUB remains a **Design-Driven technology portfolio developed with generative
AI**. Laboratories turn existing capabilities into instruments for explicit
questions, with most new investment directed toward demonstrable benefit to
**Virgo Diamond: The North Star**. A laboratory is an executed research unit,
not a renamed game directory or a promise of MMORPG readiness.

[The origin inventory](origins.json) records P01–P11's reusable capabilities,
actual source/evidence paths, existing consumers, dependencies, preservation
risks and next extraction boundary. It complements the
[project registry](../registry/projects.json), which retains historical versions,
technical maturity and execution records. Historical M4 does not mean a new
laboratory is calibrated or the MMORPG has consumed its code.

## Working pilot: combat response

[Combat response](combat-response/README.md) instruments the **unchanged P06
native encounter**. Its 28 fixed cases run twice through real Godot physics and
contact code, contrasting parry, directional dodge and a single seal under the
same phase-one sweep warning. Negative controls cover timing, range, resolve
and a separately imposed echo overlap. The
[56 outcomes](../evidence/combat-response/results.json) repeat exactly in a
separate engine invocation; [the execution record](../evidence/combat-response/RUN.json)
identifies inputs, environment, hashes, failures and limits.

The close live parry opens a 24-damage early counter at tick 52, compared with
ordinary recovery at tick 62. Outward dodge avoids these traces but spends a
movement commitment and ends farther away; a single seal does not interrupt
the sweep. At 110px, guard succeeds while the shorter blade misses. These are
measured mechanical tradeoffs, not evidence that players perceive distinct
classes. No North Star destination consumes the instrument or its mechanics.

From the maintained lab, using Python 3.11+ and Godot 4.6.3:

```bash
python3 -m unittest discover -s labs/combat-response -p 'test_*.py'
python3 labs/combat-response/run.py --godot godot \
  --output /tmp/combat-response.json \
  --compare evidence/combat-response/results.json
```

The runner bounds and closes its owned engine processes. Results come from
scripted headless scene execution; there was no physical input/listening,
independent human evaluation, multiplayer or new class implementation.
[The contextual finding](../knowledge/combat-response.md) separates observations,
interpretation and the next validity boundary.

## Controlled transition

| Origin | Preserved capability | Transition |
|---|---|---|
| P01 — Eclipse Fair | C# transactions, policy comparison, replay, native local ownership and saved slots | Preserve consumers; select a bounded economy or persistence question before extraction. |
| P02 — AI Evaluation & QA | Artifact export, pinned checks, timeout/environment evidence and control calibration | Preserve the existing task; independent candidate/model evaluation remains absent. |
| P03 — Tokyo 80s | Web Audio timing, charts, phrase rehearsal and head/tail diagnostics | Preserve songs/fixtures; candidate timing, input and feedback research. |
| P04 — Darsen / Lich | Bilingual scene/source comparison and checked EPUB/PDF production | Preserve texts, editions and rights; candidate narrative/production research. Fiction is not Virgo Diamond canon. |
| P05 — Cinderwatch | Deterministic tactical rules, response forecasting, replay recovery and native packaging | Preserve consumers/formats; candidate combat-choice, recovery and distribution research. |
| P06 — Veilbreak | Native contact, telegraphs, commitments, guard/dodge, practice and audiovisual timing | Instrumented by the executed combat-response pilot; original encounter and tests preserved. |
| P07 — Visual assets | Generated original paintings, motion regions and portrait atlas | Distributed across P06/P05; preserve exact pixels and provenance, rather than inventing a standalone application. |
| P08 — Audio production | Original synthesis, adaptive loops, semantic cues and tempo derivatives | Distributed across P03/P06/P05; preserve masters, scores, producers and real consumers. |
| P09 — Operations cases | Reported case themes only; no executable capability/evidence | Seed only. Recover an authorized source before claiming a case or instrument. |
| P10 — Waystone | NPC state, consequential quests, fresh consent, versioned replay and Python/JS comparison | Preserve source mappings and save fixtures; candidate narrative/behavior research. |
| P11 — Project Rooms | SQLite/idempotent delivery, bounded reading, backup, search and portable reports | Preserve trusted-local consumers and evaluator snapshots; candidate persistence/evidence tooling. |

All eleven are **historical origins in controlled transition**, with no obligation
to ship independent game/tool releases. Their source, media, tests and old delivery
artifacts remain available; this transition moves no source directory and deletes
no runtime. P02's old laboratory label and P07/P08's production labels are historical
provenance, not additional implemented laboratories. Existing validated transfers
and integrated assets retain their named **origin** consumers and scope.

## Candidate questions

These are research destinations, not created laboratories or a mandatory backlog:

- **Evaluation methodology — P02/P11:** can defective/reference controls detect
  intended behavior without leaking evaluator context or inventing model scores?
- **Economy/simulation — P01/P05:** which bounded ownership and expenditure rules
  produce distinct viable choices under matched scenarios?
- **Narrative agency — P04/P10:** can players understand costs while characters
  retain distinct motives, voice and causal continuity?
- **Audiovisual perception — P03/P06/P07/P08:** which cues expose contact and recovery
  without hiding the character or threat?
- **Persistence/delivery — P01/P05/P11:** which retry/recovery contracts preserve
  accepted progress under bounded failures without trusting client state?

## Evidence and reuse boundary

Before improving an instrument, complete the three-brain activation in
[AGENTS.md](../AGENTS.md): classify engineering/science/creative relevance,
retrieve complete pertinent chapters and consult contextual findings in
[knowledge/](../knowledge/README.md). Keep derived observations and their validity
limits there; do not rewrite or duplicate the durable source volumes.

Each implemented instrument needs a question, refutable prediction, identified
inputs, appropriate control, executable collection path, actual results and
limits. Prefer the smallest intervention in an existing capability. Keep negative
and inconclusive outcomes; a simulation or scripted runtime is not a human study.

[North Star's capability catalog](../north-star/capabilities.json) separately
tracks origin verification and destination use. A laboratory consumer is not a
Virgo Diamond game consumer. Actual destination execution is required before an
integration claim; this transition does not choose the MMORPG engine or prove
networking, scale, player enjoyment, accessibility or commercial demand.
