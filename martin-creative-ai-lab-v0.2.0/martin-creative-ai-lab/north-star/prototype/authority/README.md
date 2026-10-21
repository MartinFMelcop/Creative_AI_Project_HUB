# Loopback server authority experiment

This developer-only architecture consumer runs the existing escort Combat model in a
separate Godot process. The remote policy client receives snapshots and submits intents;
it never constructs or steps Combat. The shipped local scene, PCK and Linux 0.5.0 remain
unchanged. Production engine selection remains open.

From the maintained workspace, with pinned standard Godot 4.6.3 on PATH:

```bash
python3 north-star/prototype/tools/test_verify_authority.py
python3 north-star/prototype/tools/verify_authority.py --output /tmp/authority.json --compare evidence/north-star-authority/results.json
```

Use `CROSSING_GODOT` for the regression executable or `--godot` for the runner.
The runner owns and bounds all processes and creates temporary loopback ports/profiles.
Expect about two minutes: 42 live controls in source and existing PCK, then Guardian
and Duelist living escort wins in each delivery. The external authority script loads
actual `res://` model resources from the selected source/PCK; executed hashes must match.
The remote policy is a fixed instrument with eased arrival movement, not a player study.

## Ownership and protocol

The server binds only 127.0.0.1 and permits one started session per process. It owns
catalog validation, health, energy, positions, costs, progression and 60 Hz simulation.
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
Session secrets are omitted from persisted observations. Terminal completion waits for
an explicit rejection of the reset probe, even when duplicate terminal snapshots arrive.

## Evidence and limits

[Execution](../../../evidence/north-star-authority/RUN.json) records 42 controls per
delivery, four real remote wins and nine regressions. Real clock/schema mutants must
fail; mismatched PCK resources are rejected. Pilot failures exposed integral JSON
normalization and stale/duplicate observer state handling; those were corrected and
controlled before the successful full run. `--compare` compares identities and contract
checks exactly, **not packet schedules or raw observation equality**. Every run must
independently satisfy the live assertions; samples retain timing variation.

This establishes a bounded authority seam with actual gameplay costs. It does not
provide an interactive network frontend, prediction/reconciliation, multiple players,
account authentication, encryption, WAN service, persistence, reconnect, capacity or
latency guarantees. Do not expose it publicly. There is no multiplayer product release,
capability promotion, human validation or production-engine decision. Compare interactive
reconciliation against abilities/builds and independent player observation before
extending it; distribution is justified by ownership needs, not by fashion.
