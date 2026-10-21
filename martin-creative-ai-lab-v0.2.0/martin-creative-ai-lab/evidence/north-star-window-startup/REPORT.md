# Rendered readiness before the bounded authority fixture

The prior CI run passed all native remote controls and four living journeys, then
failed with `Remote window unavailable`. Five other jobs passed. Its renderer logs
were not retained, so the exact startup cause is unknown. The source verifier allowed
about 4.5 seconds for window discovery while the already-running authority had a
nine-second total lifetime. Graphics startup therefore consumed the interaction fixture.

The new verifier reserves the future loopback port, starts the actual source/PCK
window and waits at most 15 seconds for discovery. A rendered F12 capture must confirm
a closed, unconnected consumer before the authority starts. The server then receives
the same nine-second lifetime. A colliding selected port fails rather than silently
selecting a different authority. No model, protocol, input, cost or release is changed.
Native server/client/window resources remain byte-identical to the preceding commit.

Failures retain bounded tails of six known native/display logs, at most 64 KiB each;
protocol/capture JSON is not collected by this mechanism. CI uploads those logs only
on failure, for seven days. Missing or stopped windows remain failures. The startup
regression owns its wrapper/processes, delays only graphical startup by six seconds,
and still requires every actual source/PCK movement, cost, focus, release and disconnect
control. Version/headless server execution passes directly to the pinned engine.

## Executed comparisons

The actual prior verifier, recovered byte-for-byte from c5ea1ae, fails window discovery
with the controlled six-second delay and writes no accepted result. The new verifier
passes 34 OS controls normally and 34 with that delay, including rendered readiness
before authority startup in both deliveries. Delayed preflight observations are about
6.8 seconds for source and 6.6 seconds for PCK; these describe this verification setup,
not renderer speed, player latency or general performance. Complete observed values
remain in `delayed.json` and `keyboard.json`.

The current native remote suite passes 197 controls per delivery and four living
journeys. Current authority verification passes 42 live controls per delivery and four
headless living journeys. Current source/PCK grouped-delivery takes retain terminal
and stream checks; losses remain observations, not a win target. These reruns bind the
changed Python instruments and CI comparisons, not a new gameplay delivery.

Four startup regressions cover the real delayed windows, bounded absence, stopped
process diagnostics and known-log tail limits. Eleven authority regressions include
actual selected-port success and occupied-port rejection. Ten relay, three result-boundary
and five lease-evidence regressions also pass. The startup checks deliberately add a
second complete OS pass to CI; no test-runtime saving is claimed.

An intermediate delayed run failed the existing guard-advice conjunction. Its snapshot
was not retained, so no individual cause is asserted. The final verifier waits up to
one second for confirmed LIVE guard outside a ground pulse, then retains the original
LIVE/cost/drain/counter checks. Future failures include the captured context. No guard
window, model clock or payment is relaxed. `development-observation.json` records this
limit rather than inventing a missing observation.

## Selection, knowledge and limits

Compared coherent abilities/build work, independent player observation, additional
network architecture and production/creative alternatives. Fixing an actual required
CI consumer failure takes priority over expanding content on an unverified delivery.
This is executable verification reliability, not new player functionality or a new
governance program. ENG-015 informs temporal responsibility and explicit readiness;
SCI-017 informs the actual old/new delayed control and retained unsuccessful observations.
No new creative canon or player-benefit claim is made; creative authority is preserved.

The original CI failure and the controlled reproduction establish an exposed startup
limit, not an isolated diagnosis of the original runner. Startup beyond the new bound
still fails with diagnostics. Historical interaction/visual evidence remains available
because the actual consumer code is unchanged. No new images duplicate those artifacts.
Production engine, packages, capability states, protected sources, pins and licenses
remain unchanged. A later CI result is separate from these local observations.
