# Independent bounded input heartbeat

The remote client now sends at most once per 50 ms of monotonic time, independent of
snapshot receipt. During a stale interval it can send only an explicit neutral frame.
Server tick/sequence/rate/resource gates and the 250 ms action block remain unchanged.

| Approach | Profile | Living wins / takes | Server stale clears |
|---|---|---:|---|
| Guardian | direct | 2 / 2 | [1, 1] |
| Guardian | batch_400 | 0 / 2 | [1, 1] |
| Duelist | direct | 2 / 2 | [1, 1] |
| Duelist | batch_400 | 0 / 2 | [1, 1] |

Two additional actual PCK grouped-delivery takes also retain a single clear each.
All four ordinary source/PCK interactive journeys win with health 5/cargo 3; all 24 OS
controls pass. Native controls per delivery: 44 input, 82 transport, 6 pulse-presentation.

The historical controller recorded 42 clears in each grouped take; the current controller
records 1. Counts include terminal grace and are not a count of user-visible freezes.
Actual old observations fail the new repeated-expiry gate; they are not relabeled current
source evidence. The targeted rerun keeps the same model, policy, relay and profile bytes.
This is a temporal-contract fix, not a guarantee of success under grouped delivery.
All grouped scripted journeys still lose. The earlier 60 ms condition was not rerun and
its historical outcomes do not describe this new controller.

Regular delayed arrivals can still look live: Arrival gap means time since receipt, not
age of server state, RTT or prediction accuracy. The client stops active input after 250 ms
without updates, clears local pulses, and keeps only neutral intent alive. Returning
snapshots do not silently resume controls. Focus/Esc/release/reentry and terminal retention
remain deliberate. Extra neutral traffic is intentional; no bandwidth/capacity gain is claimed.

## Executed controls and limits

Real native TCP checks verify new snapshots cannot buy a second send, elapsed time can
enable a heartbeat without a new snapshot, stale active input is rejected, the shared
transmit helper cannot bypass neutral-only behavior, exact neutral wire fields and a
shared neutral/active rate bound. Five evidence regressions exercise actual pre/post rows,
missing exposure, omitted takes and changed identities. Existing malformed-frame, identity, visual and input
checks remain. OS window controls exercise actual keyboard/focus/release recovery and
disconnect. Agent inspected the retained images for Arrival gap readability and ongoing
world visibility. These are synthetic inputs and agent inspection, not independent humans.

Eight source takes use direct/grouped conditions twice per role with reversed profile
order; two PCK grouped takes check actual destination consumption. The post-execution
gate binds current identities, requested takes, actual stale exposure and at most one
server clear including terminal grace. Raw timing and gameplay outcomes remain observations.
There is no new combat rule, package, account, prediction/reconciliation, WAN, multiplayer
product, final canon, production-engine decision, lab or capability promotion.
