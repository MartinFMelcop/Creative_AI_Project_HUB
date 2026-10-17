# Crossing Drill — local character prototype

The first executable **Virgo Diamond** destination consumer: a short original courier
crossing with two experimental approaches. This is a local DEVELOPMENT increment,
not a production MMORPG, final class system or final engine selection. See the
[living design record](../DESIGN.md) for author direction, experimental decisions,
revisions and rejected alternatives.

## Play

Requires **Godot 4.6.3 standard** (tested on Linux x86_64). No SDK, npm packages,
external assets or remote service. From the maintained laboratory directory:

```bash
godot --path north-star/prototype
# Or download the small engine-dependent PCK and run:
godot --main-pack north-star/prototype/dist/crossing-drill.pck
```

The [PCK](dist/crossing-drill.pck) includes the current source consumer and native
checks; it does not bundle Godot. Native source and the delivered PCK were both
executed. The project can also be opened in the matching editor.

Choose **1 Guardian** or **2 Duelist**, then **Enter**. Keep the courier alive until
it reaches the far gate (30 simulated seconds). Losing all five player health or
all three courier health loses the attempt. Both approaches can complete the goal.

- **WASD:** move. **Arrow keys:** aim; facing otherwise follows movement.
- **Guardian / hold K:** intercept the amber line between sentinel and courier,
  facing the sentinel. Guard starts after 60ms, locks facing, slows movement and
  drains posture. Impact costs another 22. Release K to recover and turn.
- **Duelist / press K:** during a bolt warning within the range ring, draw the
  locked aim onto your current position (16 resolve). Leave that line; redirecting
  across the courier can still hit it first.
- **Space:** directional paid step (25 resolve), with recovery. It grants **no
  invulnerability**. Walking is also a valid way out of a locked threat.
- **J:** a close blade counter during OPEN, within 130px, buys time before the
  next threat. Armor/short range gives no counter. Guard/step commitment can
  reject the request; it still needs 12 resolve.
- **Red ground pulse:** leave the marked circle. A shield cannot block the floor.
- **Esc:** pause/resume. Focus loss pauses. **R** while paused abandons the attempt
  for approach selection; at the result screen it returns to selection. **Enter**
  retries from a clean state. Results/tokens are session-only.

## Execute checks and reproduce delivery

```bash
python3 north-star/prototype/tools/verify.py --godot godot --output /tmp/crossing-check.json --compare evidence/north-star-crossing/results.json
```

The stdlib runner bounds owned engine processes, uses writable temporary XDG paths,
loads the source project, executes positive/negative controls and two complete repeatable
policies, then executes the **delivered PCK** and requires exact source/PCK outcomes.
It rejects script errors, missing reports, failed checks or changed packaged behavior.
It records hashes separately from gameplay observations. Native checks do not prove
perceived class identity, reaction fairness or accessibility.

The source pack is reproducible with the matching engine:

```bash
godot --headless --path north-star/prototype --script tools/pack.gd -- /absolute/path/crossing-drill.pck
```

[Execution evidence](../../evidence/north-star-crossing/RUN.json) identifies baseline,
source/result hashes, commands, refinements and limitations. The actual playable scene
uses `combat.gd`; checks use that same implementation rather than a copied simulation.
The optional rendered journey uses controlled inputs, not human decisions.

## Provenance and limitations

New original vector geometry, interface and test fiction; no third-party media copied.
P06's paid commitment, timed contact and facing methodology informed the adaptation.
Its original arena, art, music, source and distributions remain unchanged. This is
**adaptation in a real destination**, not a shared-code import or fictional-universe
merger. See [provenance](provenance.json) and the unchanged laboratory
[finding](../../knowledge/combat-response.md).

Simple geometric beam/contact and bounded positions, no PhysicsServer body simulation,
networking or authoritative multiplayer. No audio or controller hardware validation,
player study, persistent progression, production scale or commercial claim. Candidate
character names/mechanics are experimental; Creative Brain source bytes stay untouched.
