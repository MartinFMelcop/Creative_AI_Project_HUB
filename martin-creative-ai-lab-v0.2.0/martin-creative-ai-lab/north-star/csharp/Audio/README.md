# Consequence-owned audio and original composition

`NorthStar.Audio` is a C#8/netstandard2.1 library with two separate responsibilities:
an original editable PCM composer and a read-only semantic plan. It imports no Domain
rules, samples, score, historical characters or fictional world. The host passes
actual accepted Crossing consequences; audio never determines damage, cost or time.

`Plan.Observe` maps actual contact to block/draw, hurt or evade, followed by the next
actual bolt/pulse. Terminal outcome exclusively selects won/lost. Begin announces the
next threat; preparation, restart and refusal produce no cues. Active first/second
encounters select quiet/crossing music; inactive state selects silence. Plans contain
at most two cues. The client must consume observation sequence even while muted or
suspended: repeated GET is the same observation, not permission to replay its sound.

`Composer` emits ten deterministic mono PCM16/22050Hz WAVs. Quiet and crossing are
eight-second stems sharing one transport and harmonic phase; original short cues
distinguish low resonant protection, airy draw, rough harm, light evasion and outcome
contours. Both stems must start together; adaptation changes equal-power gains,
without restarting either transport. Source amplitude deliberately reserves cue
headroom. The composer fails on excessive sample amplitude instead of hiding clipping.

Methods adapted from preserved P08/Veil `sound.gd`, synthesis and AudioServer controls
include phase-aligned transport, bounded voices, signal observation and explicit
mute/suspend/reset. The North Star Godot sound observer contributes accepted-event
ownership and consume-while-muted behavior. These technical contracts do not import
their music, source fiction or gameplay. Existing sources remain unchanged.

```sh
dotnet build north-star/csharp/AudioChecks/NorthStar.AudioChecks.csproj -c Release -m:1 --disable-build-servers
dotnet north-star/csharp/AudioChecks/bin/Release/net10.0/NorthStar.AudioChecks.dll /tmp/audio-checks.json /tmp/audio-assets
```

The native consumer writes actual WAV previews, identities, signal measurements and
actual Crossing event plans. The Presentation host caches those WAVs at startup and
serves only exact `/audio/NAME.wav` routes. Browser playback/capture and lifecycle
controls establish their own narrower execution facts. PCM headroom and technical
signal separation do not establish human recognition, absence of perceptual masking,
comfort, quality, hardware latency or physical playback. No Unity/Windows/Steam
execution, commercial clearance or independent listening validation is implied.
