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

Choose **1 Guardian** or **2 Duelist**. Press **T** for optional rehearsal, or
**Enter** to skip directly to the crossing. Keep the courier alive until it reaches
the far gate (30 simulated seconds). Losing all five player health or all three
courier health loses the attempt. Both approaches can complete the goal.

- **WASD:** move. **Arrow keys:** aim by logical navigation key; WASD uses physical positions.
  Facing otherwise follows movement.
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
  reject the request; it still needs 12 resolve. The OPEN ring shows the actual
  counter range, and its label shows the remaining window in seconds.
- **Red ground pulse:** leave the marked circle. A shield cannot block the floor.
- **Esc:** pause/resume. Focus loss pauses. **R** while paused abandons the attempt
  for approach selection; at the result screen it returns to selection. **Enter**
  retries from a clean state. The current attempt's result is session-only; earned
  cosmetic keepsakes use the separate local profile described below.

Pause and result screens retain the last contact's explanation and an actionable
tip, even after transient warnings or the final loss message replace the live
feedback. Diagnosis distinguishes facing, guard startup, insufficient posture,
unguarded contact, courier first contact, and pulse/bolt outcomes.

## Optional rehearsal

Three isolated exercises use the same `Combat` model as the normal crossing:

1. Protect against one bolt with Guardian's frontal guard, or draw and leave its
   locked line with Duelist. Personal survival without the required response does
   not pass the exercise.
2. Leave one ground pulse; holding a shield inside it still fails.
3. Move into the OPEN ring and land a close blade counter before the window closes.

Each exercise waits while its instructions are visible. **Enter** starts the trial;
the result then freezes for review. **Enter** after failure prepares a clean retry
of the same exercise; after success it prepares the next exercise. Press **Enter**
again to start that prepared trial. After the final success, **Enter** starts a
clean normal crossing. **T** repeats the current exercise from ready/review.
**R** abandons from ready/review or while paused, returning to approach selection.
**Esc** pauses/resumes a live trial; **Enter** also resumes, and focus loss pauses.

Scenarios deliberately reset positions, health and resources between attempts.
The counter exercise supplies an opening instead of requiring a preceding defense.
Costs, contact rules, range and live timing remain those of the real model; no
defense or successful input is supplied for the player. Rehearsal grants no crossing
reward or carried advantage. These controlled tasks do not establish sustained
resource management, learning transfer, unassisted comprehension or human accessibility.

## Keepsakes on this device

A full normal crossing can earn one experimental cosmetic mark for its approach:

| Mark | Required action during the successful crossing |
|---|---|
| **Held the Line** | Guardian: at least one frontal block. |
| **Drew the Danger** | Duelist: at least one drawn bolt. |

The courier must reach the gate with both courier and player alive. Rehearsal, defeat and
abandonment award nothing. Repeat wins do not duplicate marks or increase power.
Earning never equips automatically. **C** on title, result or normal pause cycles
**None → owned Held the Line → owned Drew the Danger → None**. Missing marks are
skipped. The chosen mark is drawn on the character and named in the HUD; it changes
no combat values, collision, threat timing or reward odds. These marks are experimental
identity proposals, not final item names or canon commitments.

The JSON profile defaults to **`user://crossing-keepsakes.json`**, resolved by Godot
inside this application's per-user data directory. **`CROSSING_PROFILE`** overrides
the file path for an isolated device-local profile; its parent directory must exist
and permit writing. The profile has schema version 1, owned mark IDs and the worn ID;
it contains no account, player identity or remote service credentials.

If saving fails, the mark and appearance remain usable for the current session.
**F5** on title/result/normal pause retries; closing before a successful save can lose
pending changes. A malformed, unsupported, oversized or unreadable existing profile
is preserved and blocks writes. Restore a valid file, or deliberately move/remove the
unavailable one, then press F5. Retry combines all currently known marks with that
accepted profile, retaining its chosen appearance unless C explicitly changed yours.
Writes use a same-directory temporary, flush/readback and final replacement. This
does not guarantee power-loss durability or concurrent-writer safety. The editable
local save is cosmetic continuity, not secure achievement proof, account progression
or MMORPG persistence.

## Execute checks and reproduce delivery

```bash
python3 north-star/prototype/tools/verify.py --godot godot --output /tmp/crossing-check.json --compare evidence/north-star-keepsakes/results.json
```

The stdlib runner bounds owned engine processes, uses writable temporary XDG paths,
loads the source project, executes positive/negative controls, both rehearsal sequences
and two complete repeatable crossing policies, plus keepsake eligibility and local
profile controls, then executes the **delivered PCK** and requires exact source/PCK
outcomes.
The current suite has 110 native controls. Eight further engine invocations (earn,
read, put away, read for each source/PCK) demonstrate actual process reentry with
the same local profile. New crossings remain fresh; only earned/equipped marks return.
It rejects script errors, missing reports, failed checks or changed packaged behavior.
It records hashes separately from gameplay observations. Native checks do not prove
perceived class identity, reaction fairness or accessibility.

The source pack is reproducible with the matching engine:

```bash
godot --headless --path north-star/prototype --script tools/pack.gd -- /absolute/path/crossing-drill.pck
```

[Current execution evidence](../../evidence/north-star-keepsakes/RUN.json) identifies
baseline, source/result hashes, commands, refinements and limitations. The preserved
[first-consumer record](../../evidence/north-star-crossing/RUN.json) documents the
original crossing delivery; the [rehearsal record](../../evidence/north-star-rehearsal/RUN.json)
preserves that feedback increment. The actual playable scene and rehearsal use `combat.gd`;
checks use that same implementation rather than a copied simulation. Optional rendered
journeys use controlled inputs, not human decisions.

## Provenance and limitations

New original vector geometry, interface and test fiction; no third-party media copied.
P06's paid commitment, timed contact and facing methodology informed the adaptation.
Its original arena, art, music, source and distributions remain unchanged. This is
**adaptation in a real destination**, not a shared-code import or fictional-universe
merger. See [provenance](provenance.json) and the laboratory
[finding](../../knowledge/combat-response.md).

Simple geometric beam/contact and bounded positions, no PhysicsServer body simulation,
networking or authoritative multiplayer. No audio or controller hardware validation,
player study, account/MMORPG progression, production scale or commercial claim. Only
editable device-local cosmetic continuity is stored. Candidate
character names/mechanics are experimental; Creative Brain source bytes stay untouched.
