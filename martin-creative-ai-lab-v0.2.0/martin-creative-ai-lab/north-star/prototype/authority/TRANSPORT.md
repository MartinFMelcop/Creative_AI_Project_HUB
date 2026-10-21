# Controlled transport study

Question: **does this snapshot-driven input policy retain its costs and feasible
living escort outcomes when delivery is delayed or grouped?** The actual graphical
pilot previously differed from headless outcomes; no transport envelope had been
measured. This instrument informs whether to investigate control policy, snapshot
freshness and prediction/reconciliation before committing to a larger network stack.
It does not estimate what players tolerate.

## Execute

From the maintained workspace with pinned standard Godot 4.6.3:

```bash
python3 north-star/prototype/tools/test_impairment.py
python3 north-star/prototype/tools/test_evaluate_transport.py
python3 north-star/prototype/tools/evaluate_transport.py --output /tmp/transport.json
```

The default study takes several minutes: four profiles, two roles and two takes,
**16 actual encounters**. Use `--profiles relay_zero --repetitions 1 --packed` for
an actual existing-PCK integration smoke (two encounters). `--godot` selects an
explicit executable. Repetitions are bounded to 1–3; profiles are unique nonempty
members of the finite set below. No implicit download or dependency installation.
Outputs inside prototype input paths are rejected. Invalid protocol/runtime/native
execution/identity/stream checks preserve previous result bytes. Study losses are
observations and remain in a successfully completed result.

## Intervention and controls

| Profile | Client to server | Server to client | Purpose |
|---|---|---|---|
| `direct` | Direct connection | Direct connection | Fresh positive baseline without the relay |
| `relay_zero` | No added delay | No added delay | Instrument overhead/byte-transparency control |
| `delay_60` | Retain each complete frame at least 60 ms | Same | Delayed observation and action |
| `batch_400` | No added delay | Release queued frames on 400 ms boundaries | Gaps followed by grouped updates |

The standard-library relay binds only 127.0.0.1 and forwards exactly the original
newline frame bytes in FIFO order. It never parses/mutates gameplay, stores session
tokens, drops bytes to pretend TCP packet loss, or changes server time. A frame is
scheduled after its complete newline arrives. Batching is anchored to relay startup,
not to a gameplay phase. Handshake and terminal frames undergo the same intervention.

Both approaches use standard clothing and the unchanged Guardian Steady/Duelist
native-input policy. The observer subclass only records it. It goes through View,
input latches, transport, real TCP and real Combat. Server time, paid actions, stale
quarantine and terminal results remain authoritative. The existing driver explicitly
resumes controls after delay; this scripted recovery is not human adaptation.

The first take uses the listed profile order within each role; the second reverses
profile order. This blocks by role and reduces a simple order confound, but is not
randomized assignment. All cases execute sequentially. Source/loaded-resource hashes
and the pinned engine are checked; `--packed` loads actual existing PCK resources.
No combat, client policy, engine, balance or playable package is altered for the study.

## Measurements and failure conditions

The relay records complete received/forwarded frames and bytes per direction; equality
is required. Actual first-send residence and scheduling lateness use monotonic time.
These are **relay residence**, not ping, RTT, client rendering delay or server reaction
time. A configured delay must actually appear in measured residence; actual grouped
frames must be observed for batching. The native outcome must match the real server
terminal, and the client must retain it after socket closure. Loss is valid; omitted
reports, malformed native execution, byte loss and inconsistent identity are failures.

Queues are bounded to 128 frames/256 KiB per direction, receive buffer 64 KiB, complete
frame 16 KiB. Partial frames are supported; truncated/oversized frames fail closed.
Writes are nonblocking. One connection is owned, with a 70 s relay deadline, 65 s native
policy deadline and 68 s process bound. Context exit stops owned threads/sockets/processes.
Tests include partial framing/FIFO/half-close, actual delayed and grouped delivery,
queue/truncation failures, cleanup, and a disabled-delay mutant that must be detected.

Results retain each take's living/lost outcome, health/cargo, actual paid-response
counters, input events, server stale clears/rejections and client state observations.
Client frame visits are callback counts, not elapsed time, rendering performance or
**samples from independent participants**. Distinct tick
gaps also include native observer scheduling. Only the first 48 status transitions are
retained; total/truncation fields make that boundary explicit. Baseline failure or
absence marks comparative interpretation inconclusive; all observations are retained.
Server stale-clear totals also include terminal grace; a baseline clear need not mean
a live control failure. Raw timing and outcomes are not exact golden equality gates.

## Decision scope

[Recorded execution](../../../evidence/north-star-transport/RUN.json) and its result
summaries distinguish configuration from observed schedules and retain losses.
Use the small repeated study to choose the next concrete experiment; it cannot
establish a universal latency threshold, class balance, enjoyment/accessibility,
capacity, WAN reliability, security, production engine or MMO readiness. A policy
failure alone does not justify prediction, rebalancing, extra invulnerability or a
relaxed stale-input gate. Compare policy/interaction changes and independent observers
against production needs before broadening conditions.

## Controller continuation

The [independent heartbeat execution](../../../evidence/north-star-heartbeat/RUN.json)
now reruns a targeted direct/grouped slice with current controller identities. The
original 16-take study above remains historical. The new client renews intents on a
monotonic bound and sends only neutral during stale intervals; actions remain blocked.
The targeted slice does not replace the earlier 60 ms observations with current claims.
Use `python3 north-star/prototype/tools/check_heartbeat.py RESULT.json` after a study containing grouped takes for
both roles to verify current identities, complete cases, actual stale exposure and
the bounded lease condition. Losses remain valid.
