# The coil and the shutters

One original visible scene joins local work, a person's limited offer and actual
crossing encounters. Edda has five shutter crates to secure before four shifts of
light end. A coil also needs a far-bank handoff. Rill keeps the guide line secured
until the route is surveyed and his current offer is explicitly accepted.

Work, refusal, tentative terms, reservation, departure and observed return change
what remains possible. Signing removes Rill from local work while he prepares; it
does not make him depart. Guided travel costs two shifts; solo travel costs three
and leaves him local. An actual failed crossing leaves delivery unchecked and a
guided Rill unaccounted for, without inventing his fate. No perfect free outcome,
moral score or automatic return is added.

This is experimental agent-authored North Star fiction under Martin's direction,
not approved cast/world canon or independent player validation. The original
[scene contract](../csharp/Narrative/SCENE.md) retains its authority and provenance.

## Play and continue locally

The [recipient package](../../delivery/authored-scene/README.md) includes its private
runtime and defaults to a local save outside its verified payload. To develop from
source, use the existing pinned SDK10.0.401 from the maintained workspace:

```sh
cd north-star/csharp
dotnet build ../authored-scene/Host/NorthStar.AuthoredScene.csproj -c Release -m:1 --disable-build-servers
dotnet ../authored-scene/Host/bin/Release/net10.0/NorthStar.AuthoredScene.dll --serve 8768 ../authored-scene/web --seconds 300 --new /tmp/north-star-scene.json
# After stopping or expiry, open the SAME existing file:
dotnet ../authored-scene/Host/bin/Release/net10.0/NorthStar.AuthoredScene.dll --serve 8768 ../authored-scene/web --seconds 300 --resume /tmp/north-star-scene.json
```

`--new PATH` refuses an existing file. `--resume PATH` requires a valid existing run;
missing, corrupt or incompatible data never silently starts a replacement. Preserve
such a file for inspection or explicit migration. Omitting both flags retains the
separate ephemeral development mode: stopping that host loses its in-memory attempt.
An old ephemeral session cannot be recovered retroactively.

Open the printed loopback URL. The page distinguishes local-save status from a
session-only launch. Start with local work, consultation or survey; announced threats
and accepted encounter actions still own survey, delivery and return. The scene uses
fixed Lure/Trail preparation; the separate Crossing presentation's free outfit/approach
choices are not added here.

In local-save mode, accepted choices commit before their response. Closing or expiry
keeps costs, signed commitments, unfinished work and the actual next encounter action.
A refused action changes no saved choice. New day explicitly appends a distinct day
identity while retaining earlier history; this page does not offer earlier-day browsing.
Offline time performs no work and invents no delivery, return or fate for Rill.

Sound is deliberately absent. Text, shape and static staging expose actual facts;
reduced motion removes interpolation. Focus loss and disconnect quarantine a pending
response: an action may already have committed at the host. Read the current board to
inspect facts; the client never automatically retries an uncertain action. If storage
reports a blocked owner, stop the host and resume the same file before further choices.
No claim about human accessibility, recognition, comprehension or enjoyment follows.

## One gameplay owner, durable local history

[Room](Host/Room.cs) retains the ephemeral observer of one unchanged `RequestExpedition`.
[SceneSession](Host/SceneSession.cs) selects ephemeral or local-journal transport;
[RequestJournal](Host/RequestJournal.cs) reconstructs the same actual narrative owner
from validated history. The private nested Crossing remains the only encounter owner.
Saved HP, delivery or return fields cannot independently mark an objective complete.
The browser owns no clocks, turns, costs, rewards or contact and never parses dialogue
to invent gameplay state. No second narrative game, quest catalog or historical fiction
is introduced.

The .NET10 application refers to unchanged Narrative/Crossing/Domain projects. Those
owners do not consume this host or its file/process APIs. This is not a Unity runtime
assembly, account system or shared-world persistence service. The existing Recovery
journal owns a different PreparedExpedition; its saved files are not interchangeable
with this narrative format.

The bounded host binds127.0.0.1, allows only four static files and accepts exact JSON.
Ephemeral commands retain `{"command":"open"}`. Local-save commands require exactly
`command`, `request_id`, `revision` and `run_id`. The browser captures the current run
and revision when intent is created, with a fresh request UUID; it does not silently
rebase an old queued intent onto a new day. Accepted duplicate requests do not repeat
effects; stale revision, conflicting content and wrong-day requests are refused.

History validation, source/rules identity, per-prefix actual state hashes and checksums
precede exposure of a recovered state. A local writer lease and commit-before-receipt
protect cooperating processes; uncertain writes block that owner until reopening.
Checksums are corruption detection, not authentication against trusted local users.
Process interruption is not power-loss testing; arbitrary filesystem, Windows and
Steam Cloud behavior are unvalidated. No online account or production-network claim
follows from this trusted-local observer.

## Execute and inspect

From the maintained workspace, with existing locked browser dependencies installed:

```sh
python3 -m unittest discover -s north-star/authored-scene/tools -p 'test_*.py'
python3 north-star/authored-scene/tools/verify.py --dotnet dotnet --output /tmp/authored-scene-execution
```

Use a fresh output directory outside maintained sources. The original
[scene execution](../../evidence/authored-scene/RUN.json) preserves its historical
in-session controls, fabricated-return negative and inspected captures; those records
are not relabeled as newly executed durable tests. Current continuity and publication
observations belong in [STATE](../../docs/STATE.md) and their linked execution records.
The actual forward-source closure and changed consumer determine affected regressions,
including rebuilding the current recipient artifact; unrelated study matrices do not
need an identity-only refresh.

This remains Linux/.NET/Chromium execution, not Unity Editor/import, a packaged Windows
player or Steam integration. The SDK was restored from official pinned release metadata
with archive SHA512 verification; no Unity patch or license is invented. Existing
terminal, audiovisual Crossing and Godot consumers retain unique behavior, formats,
media and notices; local narrative continuity does not justify removing them or gates.

The local narrative save is bounded continuity of this original scene, not complete
quest/reputation catalogs, NPC schedules, a persistent MMO campaign or commercial
clearance. Actual player/author observation, production ownership, supported Unity/
Windows delivery and broader storage behavior remain separate obligations.
