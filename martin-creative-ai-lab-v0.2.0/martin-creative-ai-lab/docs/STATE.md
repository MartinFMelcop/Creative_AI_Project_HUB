# Lab state

**Updated:** 2026-10-12 (UTC). **Seed:** 0.17.0.
**Current milestone:** P06 Veilbreak 0.3.0 / P07 native motion 0.2.0.

[Play the native trial](../projects/veil-arena/README.md). Two actual corrected
RGBA atlases supply 32 poses: courier walk/blade/dodge/seal and Warden
walk/sweep/charge/wave. Native production derives isolated regions, foot pivots
and scale from alpha without editing PNG bytes. Displacement and combat clocks
choose poses; pause/result freeze them and restart clears them.

Blade aim locks, contact lands after 100ms, and recovery lasts to 320ms. Seal
release follows 75ms gather. One action starts at a time; movement slows while
committed. Dodge or damage cancels unfinished contact without refund. Facing,
pose and cue follow the actual emission event. Boss damage/costs/cooldowns,
patterns/echo, floor/portraits/audio and the complete native lifecycle remain.

[Execution](../evidence/veil-arena/MOTION_RUN.json) records source and shipped/
rebuilt PCK, complete fight, actual AudioServer and motion contracts. OpenGL
frames and a 7.2s Movie Maker demonstration come from the pack outside source;
fixtures/scripted input are not human play or a hardware performance benchmark.
The same controller wins both versions: 0.2.0 51.87s/2 health; 0.3.0 55.58s/1 health.
This comparison establishes completion/increased commitment risk, not balance.

Started clean at `eb474a5`, matching fetched main. Reviewed portfolio/seed/history
and actual native/comparison sources. Selected body-readable committed combat
over another P11 operation, speculative P05 recovery or automatic P03/P04 content.
Godot 4.6.3/GDScript fits the real native consumer; no engine/language rewrite.
Extend only P07-to-P06 TR-013, add VIS-002; original assets/archive/other projects
remain preserved. GitHub main is authorized; no hosting deployment.

Codex asset/pose review only. Four-keyframe clips and horizontal mirroring retain
some generated pose/proportion variation; no full directional/hand-animated set.
PCK requires Godot; no standalone OS build, independent player/artist approval,
physical input/listening or commercial clearance. Next compare actual committed
combat feedback with P01 strategy, P05's scoped turn-based destination, P03 physical
play/listening, P04 readers and P11 real recovery use before choosing again.
