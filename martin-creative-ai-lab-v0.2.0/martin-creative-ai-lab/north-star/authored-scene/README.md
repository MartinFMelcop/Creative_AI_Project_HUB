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

## Play locally

Use the existing pinned SDK10.0.401. Run from the maintained workspace:

```sh
cd north-star/csharp
dotnet build ../authored-scene/Host/NorthStar.AuthoredScene.csproj -c Release -m:1 --disable-build-servers
dotnet ../authored-scene/Host/bin/Release/net10.0/NorthStar.AuthoredScene.dll --serve 8768 ../authored-scene/web --seconds 300
```

Open the printed loopback URL. Start with local work, consultation or survey; the
announced threat and explicit encounter actions own the actual survey and delivery.
The scene uses fixed Lure/Trail preparation. It does not offer the separate
Crossing presentation's free outfit/approach choices. New day explicitly discards
this ephemeral session. Browser refresh reads current facts; it does not save them.

Sound is deliberately absent. Text, shape and static staging expose actual facts;
reduced motion removes interpolation. Focus loss and disconnect quarantine a pending
response: an action may already have committed at the host. Reconnect explicitly to
inspect current facts; the client never automatically retries an uncertain action.
No claim about human accessibility, recognition, comprehension or enjoyment follows.

## One owner, separate application

[Room](Host/Room.cs) owns one unchanged `RequestExpedition`. It calls its existing
commands and captures its `Last` plus exact `Snapshot`; the private actual Crossing
encounter is the only encounter owner. The browser owns no clocks, turns, costs,
rewards, completion or contact. It never parses dialogue to invent gameplay state.
No `Presentation.Room`, second session, quest framework, persistent narrative format,
new sound policy or historical fiction is introduced.

The .NET10 application lives beside the existing C# library/consumer tree and refers
to its unchanged Narrative project. The separate root reflects a reverse dependency:
this application consumes Narrative/Crossing/Domain; those owners do not consume it.
The verifier traverses actual forward project references and compile inputs, plus
web/instrument sources. Existing origin closures remain exact. Their historical
results remain intact; unrelated study matrices need no identity-only refresh.

The bounded host binds127.0.0.1, allows only four static files, accepts exact
`{"command":"open"}` JSON and rejects extra/duplicate/invalid fields before mutation.
Valid owner refusals are observed separately. Sequence remains monotonic across an
explicit new day. Body size, request-read deadline and host lifetime are bounded;
this local developer host has no authentication or production-network claim.

## Execute and inspect

From the maintained workspace, with existing locked browser dependencies installed:

```sh
python3 -m unittest discover -s north-star/authored-scene/tools -p 'test_*.py'
python3 north-star/authored-scene/tools/verify.py --dotnet dotnet --output /tmp/authored-scene-execution
```

Use a fresh output directory outside maintained sources. The instrument builds the
actual application and checks, executes the real host/browser, retains meaningful
negative journeys and isolates a renderer that fabricates observed return. Runtime
paths/timing differ; source identities and actual outcome contracts are checked.
[Execution](../../evidence/authored-scene/RUN.json) owns precise results and inspected
captures. Software fidelity is separate from human experience and author approval.

This is real Linux/.NET/Chromium execution, not Unity Editor/import, a packaged
Windows player or Steam integration. The SDK was restored from official pinned
release metadata with its archive SHA512 checked; no Unity patch/license is invented.
The existing terminal, audiovisual Crossing and Godot consumers retain unique behavior,
formats, media and notices; this scene does not justify removing them or their gates.

Next acceptance depends on actual player/author observation, delivery access and
consequential production needs. Durable narrative, NPC schedules, quest/reputation
catalogs, full effects, source rights clearance and production ownership remain open.
