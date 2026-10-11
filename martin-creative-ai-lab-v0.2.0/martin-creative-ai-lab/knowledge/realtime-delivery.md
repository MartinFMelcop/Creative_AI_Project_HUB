# Trace the complete delivery path

Context: P11's original form emitted a message and its server logged it, but
neither browser displayed it. The same browser delivery check failed against
the preserved source and passed against the working adaptation. See
[execution evidence](../evidence/realtime-chat/RUN.json) and
[the event contract](../projects/realtime-integration-lab/README.md).

A server log proves receipt at one boundary. It does not prove transmission
to peers or rendering in their UI. Write acceptance around the whole visible
path, and include the sender: optimistic append plus an inclusive broadcast
can create duplicates. Here, all clients render one broadcast path.

Server acceptance and reliable delivery are different. A timeout can occur
after a broadcast was delivered. This prototype avoids automatic retry,
preserves the draft, and tells the participant that delivery is uncertain.
A durable system would require an explicit message identity, idempotency, and
recovery contract, rather than inferring exactly-once behavior from one happy
path. The offline guard prevents intentional disconnected submissions, but is
not sufficient for heartbeat races: `connected` can lag behind the emitter's
connection check.

## Separate live congestion from reconnect buffering

P11 0.1.1 corrects two behavior gaps in 0.1.0. The pinned Socket.IO client drops
volatile events when the transport is not writable, even if connected. A real
polling write followed immediately by a form submission reproduced that loss.
Separately, a controlled heartbeat-expiry check retained a packet for replay even
with the earlier volatile flag. Both regression tests fail on the recorded
0.1.0 client and pass on 0.1.1; see
[current evidence](../evidence/realtime-chat/POLLING_SEND_RUN.json).

Ordinary emission lets the live Engine.IO write queue drain. Clearing the distinct
Socket.IO reconnect `sendBuffer` immediately after emission preserves the
prototype's no-replay policy when connection state is stale. The existing
timeout and draft feedback still apply; no automatic retry or persistence was
added. Recheck these semantics when upgrading Socket.IO: a property name or
an online flag alone does not establish a queue's lifetime.

The heartbeat test pins a specific internal predicate in Socket.IO 4.8.4, restores
it immediately, and then uses a real transport reconnect. This proves the policy
at that boundary, not every timing/packet-loss scenario or distributed delivery.

TR-009 now consumes this defect in [P02 EVAL-001](../evaluations/chat-send-buffering/README.md), with a calibrated export/checker and destination-specific gates. That bounded adaptation is verified; no independent model evaluation is implied. TR-010 remains a candidate for P01 event ownership. A chat is not a game
lobby or authoritative multiplayer system. A public reference solution must
not be treated as private evaluation material. No component was promoted to
`shared/` in this session.

## Receiving text must respect reading position

[P11 0.1.2 evidence](../evidence/realtime-chat/READING_RUN.json) shows a correct
broadcast can still interrupt reading if rendering always scrolls to the end.
Follow near the bottom; otherwise preserve the visible message and pixel offset.
A cap removes variable-height text before that anchor, so numerical scrollTop
alone is insufficient. If the anchor expires, show the retained-history boundary.

Browser scroll values quantize geometry: a measured 4.0625-pixel drift appeared
across ten evictions. Carrying fractional correction meets the one-pixel checks
here. Reuse in logs or narrative histories is a candidate until a destination
adapts and verifies it; no shared code is promoted. Human readability, resize/zoom
and other browsers remain separate. P02's pin detected changed runtime metadata;
recalibrate controlled inputs without adding UI requirements to its send task.
