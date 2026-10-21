# Loopback server authority experiment

This developer-only architecture consumer runs the existing escort Combat model in a
separate Godot process. The remote policy client receives snapshots and submits intents;
it never constructs or steps Combat. An interactive developer window now consumes the
same authority through bounded keyboard/mouse intents and read-only snapshot
presentation. The shipped local scene, PCK and Linux 0.5.0 remain
unchanged. Production engine selection remains open.

From the maintained workspace, with pinned standard Godot 4.6.3 on PATH:

```bash
python3 north-star/prototype/tools/test_verify_authority.py
python3 north-star/prototype/tools/verify_authority.py --output /tmp/authority.json --compare evidence/north-star-action-feedback/authority.json
```

Use `CROSSING_GODOT` for the regression executable or `--godot` for the runner.
The runner owns and bounds all processes and creates temporary loopback ports/profiles.
Expect about two minutes: 42 live controls in source and existing PCK, then Guardian
and Duelist living escort wins in each delivery. The external authority script loads
actual `res://` model resources from the selected source/PCK; executed hashes must match.
The remote policy is a fixed instrument with eased arrival movement, not a player study.

## Play the separate developer window

From the maintained workspace, start the server in one terminal:

```bash
godot --headless --path north-star/prototype --script "$PWD/north-star/prototype/authority/server.gd" -- 47620 /tmp/north-star-server.json 120
```

Then open the remote window in another terminal:

```bash
godot --path north-star/prototype --script "$PWD/north-star/prototype/authority/play.gd" -- 47620
```

F2 selects Guardian/Duelist, Tab selects Guardian technique and C cycles the four
existing catalog outfits. Enter connects and locks preparation. WASD/arrows move,
mouse aims, K/right mouse holds guard, J draws the bolt, Space steps and L/left mouse
counters. These are fixed experiment bindings, separate from local remaps/gamepad.
Only server-confirmed costs and outcomes are displayed; input is not success.

The three action cards use server-authored snapshot advice: step cost/recovery,
Guardian guard state/drain/contact cost or Duelist draw conditions, and a counter
that needs an opening, range, resolve and a released guard/finished step. Teal dashed
130px and conditional amber dashed 340px rings show the server's counter/draw ranges;
the red pulse remains a separate damage telegraph. Empty strikes still cost resolve.
Guard LIVE describes its timing and locked facing, not protection from every origin;
ground pulses explicitly warn to move. Advice is for individual actions at the last
snapshot, not a reservation, prediction, combination budget or guaranteed admission.
Simultaneous commands and the next physics step can change eligibility. The server
continues validating every action. Cards mask availability on stale/error/terminal,
suspension, focus loss and local/server quarantine. During active play, costs remain
visible even when an action is unavailable.
No new ability, class, stat or local release is introduced.

Esc suspends/resumes controls, **not the world**. Loss of focus suspends immediately.
Release held controls and explicitly resume after returning focus. Releases missed
outside the window are reconciled only by removing absent controls; polling never
synthesizes a press. Brief action taps survive until an admissible send, with a false
packet between rising edges and a bounded pending queue. Initial/server quarantine
requires release before a fresh press; the footer explains this state.

Intent sends use monotonic time, at most once per 50 ms, without waiting for another
snapshot. Active sends require live updates. During stale intervals the window sends
only an explicit all-neutral intent at the same bound; it never repeats the old held
command or queues an action. Receipt bursts do not buy send credits. This keeps the
input lease distinct from snapshot delivery while retaining action suspension. Neutral
traffic during gaps is intentional; it grants no resource or prediction.

Positions interpolate between confirmations over 50 ms, never beyond the latest
position. Threat-phase changes, quarantine and terminal snap to confirmed geometry.
Resources, threats and results are never predicted; there is no local Combat model.
An arrival gap above 250 ms blocks intents and freezes presentation; this measures
time since receipt, not the age of server state or RTT. Disconnect preserves
the last known world; terminal results stay visible after the authority closes. Q
exits. A new attempt needs a new server process; this is intentionally not reconnect.
The suspension footer leaves ongoing threats visible. Pulse drawing is checked
against actual model damage, including the former falsely safe 78–90px annulus.

The documented PCK/Linux pipeline fresh-stages the explicit `tools/pack.gd` inventory,
which excludes these developer scripts. An arbitrary direct editor export is not that
pipeline. No new player archive or package is delivered here.

## Ownership and protocol

The server binds only 127.0.0.1 and permits one started session per process. It owns
catalog validation, health, energy, positions, costs, encounter progression and 60 Hz
simulation.
Packet count and client timing never determine model steps. Snapshots arrive at 20 Hz.
There is no client time/delta, position, health or arbitrary model assignment command.

Requests are sorted-key, compact, canonical ASCII JSON objects terminated by newline.
Version is integer 1. Hello has exactly `v,kind,role,style,outfit`; kind is `hello`, role
is Guardian or Duelist, style is Steady/Riposte for Guardian or none for Duelist, and
outfit is an actual server catalog ID. Welcome returns a random, connection-bound
session token. This token is freshness context, **not identity authentication**.
Input has exactly `v,kind,session,seq,move,aim,guard,feint,step,strike`; kind is `input`.
Vectors are two integer components in [-1000,1000], scaled and length-limited by the
server. Buttons are booleans. Sequences strictly increase, with a maximum forward jump
of 64; no replay. At most one valid sequenced intent is admitted per physics tick.
An admitted release-required intent advances its acknowledgement but cannot rearm.

Movement/guard are held; feint/step/strike are rising edges. Initial connection and
silence beyond 15 ticks require a released-button intent before rearming. Disconnect
neutralizes immediately while the model continues. Neither reconnect nor a second
hello, including after terminal state, can reset resources or change preparation.
Invalid frames cannot start the model. Maximum frame is 512 bytes, buffer 4096 bytes,
16 processed frames per tick, depth four; malformed/ambiguous JSON is rejected.
Partial frames are supported. Oversized unterminated frames close the peer. Output is
nonblocking and closes a peer that cannot accept a complete message.

Snapshots expose state/ack/tick/quarantine; final reports bind actual loaded resources.
Session secrets are omitted from persisted observations. The headless policy client waits
for an explicit reset-probe rejection even with duplicate terminal snapshots. The interactive
window instead retains the confirmed terminal result through actual socket closure.

## Evidence and limits

[Current execution](../../../evidence/north-star-action-feedback/RUN.json) binds the actual
interactive consumer, native event journeys, OS input/focus controls and inspected
images. [Earlier interactive execution](../../../evidence/north-star-remote/RUN.json) and
[original authority execution](../../../evidence/north-star-authority/RUN.json)
remain historical. Adding view fields changed the server identity; active authority
comparison uses the reexecuted current `north-star-action-feedback/authority.json` above.

```bash
python3 north-star/prototype/tools/verify_remote.py --output /tmp/remote.json --compare evidence/north-star-action-feedback/remote.json
python3 north-star/prototype/tools/verify_remote_input.py --output /tmp/remote-input
```

The first command runs native intent/transport/visual controls and Guardian/Duelist
living journeys in source and PCK through actual View input events and TCP. The second
requires Xorg dummy/libX11/libXtst and exercises an actual window using XTest, including
release outside focus and explicit recovery. Captures are opt-in through
`NORTH_STAR_REMOTE_CAPTURE` plus F12. An explicit `tests/remote_journey.gd` driver can
also render the real win and retained result when run without `--headless`; its three
arguments are port, Guardian/Duelist, output JSON. None of these policies is a player.

`--compare` binds identities and passed contracts, **not packet schedules or raw
observation equality**. Every execution must independently pass live controls.
Meaningful pilot failures and visual corrections are recorded in ADR-096. No guard,
cost, damage radius or timing window was relaxed to make the remote client succeed.

This establishes an interactive, bounded authority consumer. It does not provide
prediction/reconciliation, multiple players, account authentication, encryption, WAN
service, persistence, reconnect, capacity or latency guarantees. Do not expose it
publicly. There is no multiplayer product release, capability promotion, human
validation or production-engine decision. Compare a coherent abilities/build consumer,
independent observation and measured transport/reconciliation needs before continuing;
a larger network stack is not the automatic next task.

## Measured transport interventions

The [controlled transport instrument](TRANSPORT.md) now compares direct/no-added-delay
controls with delayed and grouped frames using the actual remote consumer. It retains
losses and measured relay residence; these are not player latency or balance estimates.
