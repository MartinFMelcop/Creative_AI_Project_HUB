# Crossing presentation host

This bounded .NET10 loopback host executes the existing `Crossing.Session` source
and Domain project unchanged. Browser presentation observes actual accepted outcomes;
it owns no gameplay clock, resource, reward or contact. This is Linux/.NET/browser
evidence, not Unity Editor, Windows, Steam, production networking or human validation.

```sh
dotnet build north-star/csharp/Presentation/NorthStar.Presentation.csproj -c Release
dotnet north-star/csharp/Presentation/bin/Release/net10.0/NorthStar.Presentation.dll --serve 8766 north-star/csharp/Presentation/web --seconds 120
dotnet build north-star/csharp/PresentationChecks/NorthStar.PresentationChecks.csproj -c Release
dotnet north-star/csharp/PresentationChecks/bin/Release/net10.0/NorthStar.PresentationChecks.dll /tmp/presentation-checks.json
```

`GET /state` never advances a beat. `POST /command` accepts exact JSON fields:
`{"op":"prepare","approach":"anchor","outfit":"plate"}` (also `lure`/`trail`),
`{"op":"begin"}`, `{"op":"action","action":"walk"}` (also `dash`, `skill`,
`wait`), or `{"op":"restart"}`. Unknown, repeated, missing or invalid fields fail
before owner mutation. Structurally valid owner refusals return `accepted:false`,
`pose:rejected`, no contact/deltas, and the actual owner state.

Responses contain flat authoritative state plus `before`/`after`, monotonically
increasing `sequence` (including refusals and restart), `command`, `accepted`, `pose`,
`contact`, `damage`, `cost` and `moved`. Contact is derived from accepted owner
consequences: hurt, protected against a bolt, evaded pulse, or none. Poses describe
the observed command; final won/lost overrides the action pose. Presentation does not
imply that a requested or rejected skill landed. Restart creates a fresh local session,
retaining observation ordering. Sessions remain ephemeral and preparation uses only
the existing approach/outfit choices; this host adds no point allocation or save format.

The sequential host binds only `127.0.0.1`, has a 1–600 second lifetime, allowlists
static files, bounds JSON bodies and rejects cross-origin browser command requests.
It is a developer demonstration with no authentication or account-security claim.

Open the printed loopback URL before the bounded host closes. Apply Anchor/Lure and
Plate/Trail independently, enter, then choose one action per beat. The actual NEXT
THREAT is shown before acting; bolt movement risks health, while a pulse requires
actual displacement. Both encounters require enough distance and survival at their
real deadline. A failed action budget advances nothing. Restart explicitly discards
this ephemeral experiment and creates a fresh session; it is not save recovery.

The original vector body changes outfit silhouette independently of approach gesture.
Static poses show the last accepted event, not continuous action animation. The goal
marker follows actual required position. Clear last gesture, focus loss and disconnect
hide stale pose/contact without changing owner state. Reduced motion disables position
interpolation while preserving text/shape information; no human accessibility claim.
No preserved PNG, Runner/Warden identity or outside art/package was imported.

[Visual method and reproduction](../../../labs/visual-animation/README.md) and
[actual execution](../../../evidence/visual-animation/RUN.json) retain47 native controls,
four complete choice journeys, failed policies/successful rivals,20 actual Chromium
controls, detected source/renderer mutants and inspected captures. Technical fidelity
is distinct from independent recognition, art approval, experience or commercial rights.

## Original audio with explicit control

Enable audio explicitly after connecting. Music and effects have independent sliders;
mute consumes current events without replay on unmute. Playback suspension, focus loss
and disconnect stop voices/transports. Resume is explicit and establishes the current
observation baseline; lost events are intentionally not replayed. Restart clears old
cue/async ownership and silences music while both aligned clocks continue; a later
encounter fades to its actual arrangement. Suspend/resume recreates both at one start.

The host caches ten original WAVs from the portable [C# composer](../Audio/README.md),
served only at exact `/audio/NAME.wav` routes. Response and next-threat meaning comes
from the actual C# `audio:{cues,music}` plan, not a click-side JavaScript prediction.
Terminal won/lost stops prior threat voices. Visual/text consequences remain available
with sound disabled. The browser is a local developer observer, not a production engine.
[Audio evidence](../../../evidence/audio-music/RUN.json) binds real digital playback,
phase/silence/overlap/lifecycle controls; no listener recognition or physical latency claim.
