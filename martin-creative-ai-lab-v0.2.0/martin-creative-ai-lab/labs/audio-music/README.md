# Audio & Adaptive Music Laboratory

P08 owns this mandatory destination. Its bounded question is whether aligned source
transports and semantic/lifecycle ownership preserve phase and truthful audible events
where shifted transports, malformed signals and intent-based playback fail. The
North Star consumer and browser execution are coordinated in `browser.mjs`; origin
execution alone does not establish destination integration.

## Actual preserved source method

```bash
python3 labs/audio-music/test_instrument.py
python3 labs/audio-music/run.py --output /tmp/audio-source.json
python3 labs/audio-music/run.py --output /tmp/audio-repeat.json --compare /tmp/audio-source.json
# Optional local regeneration using the existing producer dependencies:
python3 labs/audio-music/run.py --output /tmp/audio-source.json --producer
```

The core requires Python standard library and the repository's pinned Godot runtime,
not NumPy. Output stays outside maintained sources. It verifies all 18 preserved P06
catalog hashes, decodes 14 mono PCM16 cues and two 24-second masters, and measures
frames, endpoints, integer peak and RMS. Declared 80 BPM / eight four-beat bars must
match the 24-second transport. Equal duration is not itself a phase measurement.
Original masters, compressed derivatives, producer and provenance remain unchanged.

An isolated minimal Godot project loads the actual unchanged `sound.gd` and exact
preserved runtime media. Fourteen native controls execute post-limiter AudioServer
capture, audible output, phase crossfade, same-block alignment, suspended cue dropping,
muted event auditing, actual mute/suspend/stop silence, bounded eight voices and 64
history events, limiter gain stress, an atomic 100 ms phase injection and reset recovery.
The 15 ms alignment and greater-than-50 ms negative thresholds are retained source
policies. Injection is locked to one mixer instant; a stale main-thread seek target
would not reliably create the intended negative. This is not another fixture repair.

Three controlled PCM negatives independently fail endpoint, peak clipping and frame
count checks. They are in-memory defects, not modified historical files. Environment,
import or subprocess failures fail execution and cannot count as successful negatives.
Eight instrument regressions reject false signal acceptance, malformed format/empty
PCM and writes inside maintained sources. No new package is installed.

## Evidence and reproducibility boundary

The canonical result fingerprints exact source/instrument inputs and records deterministic
PCM measurements and actual native control identities. `--compare` requires exact
canonical equality. Real mixer measurements vary with scheduling: their actual values
are preserved in sibling `.measurements.json`, explicitly outside exact comparison.
The native controls still enforce their thresholds on every execution; variable samples
are never accepted merely because an earlier execution passed.

Optional `--producer` runs the preserved `render_audio.py` in an isolated copy with
existing NumPy/FFmpeg. Exact PCM reproduction is required; compressed encoding differences
are retained explicitly rather than rewriting source identities. Its actual file-by-file
results live in sibling `.producer.json` and are separate from the dependency-free core
contract. Producer execution does not replace actual source playback or destination
browser PCM evidence.

## Consumption, validity and next objective

Source synthesis, aligned adaptive transport, semantic dispatch, finite voice ownership
and explicit lifecycle are reusable methods. Destination audio must follow accepted
C# sequence/contact/outcome observations; clicks, stale snapshots and redraws cannot
manufacture consequences. The browser instrument owns that consumer acceptance and
actual rendered PCM. No P06 opponent/world fiction is implicitly imported.

SCI-014/017 separate operational measures and controlled defects from broad causal
claims. SCI-064/070 distinguish file identity, digital signal, timing and perception:
waveform correctness is not cue recognition, preference or comfort. SCI-049 keeps
multimodal task communication distinct from a general quality score. No physical
speaker/headphone, listener comprehension, accessibility, preference, exclusive rights,
Unity, Windows or Steam validation is claimed. Repeated samples are not participants.
Next: assess cue recognition/masking and mix comfort on documented devices with suitable
listeners and balanced presentation; validate real Unity/Windows output when available.

## Original destination and actual real-time acceptance

Independent Engineering, Scientific and Creative analyses compared three incomplete
labs and product/lifecycle needs. They selected audio after actual embodied Crossing
made consequences and stable observation identity available. Another public-task
calibration would not establish independent AI evaluation; bounded probes found no
usable licensed Unity/Windows tooling. Narrative persistence remains useful but does
not close one of those incomplete labs. This is coordinated specialist work, not
independent human listening or approval.

[The portable C# composer/plan](../../north-star/csharp/Audio/README.md) emits ten original
WAVs. No preserved source tune, voice, opponent or world is copied. The same actual
Crossing owner supplies accepted response then next threat; terminal outcome has
priority and refusal is silent. The Presentation host serves only cached named audio.
Use SDK10.0.401, Node24.19.0 and the existing locked playwright-core1.64.0:

```bash
dotnet build north-star/csharp/AudioChecks/NorthStar.AudioChecks.csproj -c Release
dotnet north-star/csharp/AudioChecks/bin/Release/net10.0/NorthStar.AudioChecks.dll /tmp/audio-native.json /tmp/audio-assets
node labs/audio-music/browser.mjs dotnet /tmp/audio-browser
```

Install the existing lockfile in `projects/realtime-integration-lab`; set CHROMIUM_PATH
to its installed matching browser (local default `/usr/bin/chromium`). No new browser
package is introduced. The bounded instrument closes its owned browser/host.

[Execution](../../evidence/audio-music/RUN.json) binds67 native controls and29 actual
Chromium/C# controls. A zero-output instrument-only ScriptProcessor branch taps actual
real-time AudioContext PCM after the product mix. Two simultaneously captured pre-gain
channels expose shared100/150Hz phase; an actual37ms delayed capture path fails that
criterion. This is a controlled signal-path negative, not a spontaneous engine defect.
A master-gain12 fixture exposes over-range float samples; nominal maximum UI gains and
rapid actual commands retain bounded voices/headroom. An isolated actual audio.js guard
mutant repeats a real accepted observation and is detected. Environment errors never
count as those negatives.

The instrument retains actual output measures, accepted states and bounded playback
traces. Mute measures zero PCM; disabled music retains actual effects. Explicit late
enable/resume consumes previous events without backlog. Blur during decode invalidates
its pending epoch; disconnect actually suspends the context. Suspended contexts produce
no capture callbacks: context/node/gain state is observed rather than inventing silent
samples that were not processed. Redraw/GET cannot emit a new observation or advance play.

The [public WAV](../../evidence/audio-music/crossing-output.wav) concatenates declared
actual output windows; it is not one continuous performance or a final master. Raw
browser timing/PCM varies across platforms; reproduction enforces properties instead
of requiring cross-host byte equality. Source canonical equality and variable capture
measurements retain distinct contracts. Physical listening, signal recognition,
masking, accessibility, quality, rights clearance, Unity/Windows/Steam remain open.
