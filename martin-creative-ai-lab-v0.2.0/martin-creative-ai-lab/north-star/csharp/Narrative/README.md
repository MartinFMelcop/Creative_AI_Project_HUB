# The shutter list — bounded narrative consumer

[The visible authored consumer](../../authored-scene/README.md) now observes this
same owner, including its actual private encounters, work list, guide line and receipts.
The terminal remains usable; no narrative rule or persistent format was changed.

An original in-session request scene composes the unchanged actual
[Crossing encounter](../README.md). Edda needs five shutter crates carried
before four shifts of light end; a coil also needs a far-bank handoff. Rill will not
guide an unchecked route. His refusal physically keeps the line on its peg.
This is experimental North Star fiction, not final characters, geography or quest canon.

## Run the real consumer

Use the repository-pinned .NET SDK10.0.401, without substituting Unity execution:

```bash
dotnet build north-star/csharp/NarrativeChecks/NorthStar.NarrativeChecks.csproj -c Release
dotnet north-star/csharp/NarrativeChecks/bin/Release/net10.0/NorthStar.NarrativeChecks.dll /tmp/narrative-native.json
dotnet north-star/csharp/Narrative/bin/Release/net10.0/NorthStar.Narrative.dll --demo /tmp/narrative-demo.json
dotnet north-star/csharp/Narrative/bin/Release/net10.0/NorthStar.Narrative.dll
```

The interactive host accepts `open`, `hear`, `offer`, `terms dusk|open`, `confirm`,
`defer`, `decline`, `withdraw`, `work`, `survey`, `depart guided|solo`,
`skill`, `walk`, `dash`, `wait`, `show`, `quit`. EOF also closes it.
It creates no save file. `show` is a read-only exact projection, not an import or
quest-completion command. Invalid commands return refusal without changing gameplay state.

One actual guided journey is:

```text
survey
skill
skill
walk
skill
open
hear
offer
terms dusk
confirm
depart guided
skill
skill
walk
skill
walk
skill
work
quit
```

The first four encounter actions execute the actual survey; the next six execute
the actual delivery encounter. The result has two of five local crates carried,
zero shifts remaining, coil delivered and return observed. It does not erase the
three unfinished crates. `decline`, `work`, `work`, `work` instead completes all
five local crates without claiming coil delivery. After a successful survey,
`decline`, `depart solo` and the same six delivery actions permits the external
handoff without Rill's consent or departure; its three-shift travel cost leaves
no light for local work. No branch is labelled morally superior.

## Consequential contract and source decisions

* `open` obtains a current consultation; `hear` obtains Rill's bounded offer only
  after actual survey success and with at least two shifts remaining.
* A proposal and written terms transfer nothing. `confirm` reserves Rill for
  preparing the coil; local capacity changes immediately from two crates per shift
  to one. His location remains `local-preparing` until actual departure. The cost
  is previewed before confirmation.
* World facts changing through work/survey invalidate draft terms and consent.
  Reopening requires a new answer. `defer` promises no future loan. `decline` is
  final for this guide request; solo delivery and local work remain available.
* `withdraw` before departure restores availability and appends a withdrawal after
  the unchanged commitment receipt. Actual departure is irreversible here; no
  travel time is refunded.
* Guided travel costs two shifts, solo three; survey entry costs one. These are
  original bounded scenario values, not measured travel, fairness or final balance.
* A due-before-dark term is an obligation, not an observation. Passing the deadline
  never returns a guide, completes a quest or grants rewards. A failed guided
  crossing leaves the guide unaccounted for and preserves an overdue obligation.
* Only the private unchanged encounter's actual second-stage win sets delivery and
  successful return. For a guided journey `returned` covers player and Rill; for
  solo it covers the player only. This is a completed-journey receipt, not a universal
  player-presence flag: after a failed attempt the player retreats to the local board
  without a completed journey, while the guide may remain unaccounted for. `guide_available` and `guide_location` identify
  Rill independently. Failure does not infer death or a verified return. The local
  work list remains available after a failed attempt; there is no simulated rescue.
* Rewards remain the actual encounter's once-only XP10/15. Conversation, promises,
  deadlines, repeated commands and fabricated `complete` commands grant nothing.

P10's deferred-request consumer informed fresh consultation, no transfer before
terms and the difference between a due return and an observed return. P04's
source comparison informed refusal changing physical action before renewed limited
permission. The historical quest UI permits direct completion without objective
evidence; that behavior is rejected here. No historical fiction is imported.
[The narrative lab](../../../labs/narrative-continuity/README.md) owns source assay,
controls and evidence; [SCENE](SCENE.md) owns the bounded staging/creative critique.
ENG-005 informed the explicit finite state and state-preserving refusal contract.

## Limits and next question

The eight compiled demo journeys and native controls are synthetic executions of
real code, not participants, enjoyment findings or independent human review.
This is a .NET10 command-line consumer using the existing C# encounter. It is not
Unity Editor, a Windows player, Steam, an implemented general quest/NPC framework,
AI dialogue, final canon, reputational simulation or a persistent campaign.
The prior Recovery consumer remains separate and does not save this scene; no
journal migration or durable narrative claim is made. Whether readers understand
the costs and distinguish reservation, departure, commitment and evidence remains
an empirical question. Future authored scenes should establish consequence breadth
and useful presentation before extending schemas or introducing generic frameworks.
