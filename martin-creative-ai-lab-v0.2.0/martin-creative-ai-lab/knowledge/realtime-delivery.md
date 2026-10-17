# Trace the complete delivery path

## Context and use

**Question:** Which boundary loses a message or disturbs the reader even when
the server has accepted it? **Origin:** P11's recorded early chat adaptations;
the linked records identify exact source hashes, versions and environments.
Later P11 releases retain this provenance, rather than extending these findings
automatically to their current code or to another destination.

| Observation / outcome | Interpretation and practical consequence | Validity boundary |
|---|---|---|
| Negative: the preserved source logged receipt while neither browser rendered the message. Positive: the recorded adaptation passes the same browser check. | Assert the sender-to-peer-to-render path, including sender duplication, rather than accepting a server log as delivery. | The recorded source/dependency setup and automated Chromium checks; not guaranteed delivery. |
| Negative: connected volatile emission dropped a polling write; a controlled stale-connection predicate allowed reconnect replay. Positive: the recorded correction passes both probes. | Distinguish live transport queues from reconnect buffers; recheck queue lifetime when dependencies change. | Socket.IO 4.8.4 and the declared real-polling/controlled-heartbeat boundaries; not all network failures. |
| Negative: unconditional scrolling and uncorrected fractional geometry disturbed the recorded reading anchor. Positive: bounded anchoring, unread navigation and activity checks pass. | Keep reading position, focus and page activity as separate conditions. | Recorded browser geometry and controlled visibility; no independent human or assistive-technology evaluation. |
| Unresolved: acknowledgement timeout can follow successful rendering. | Preserve the draft and report uncertain delivery; adding retries requires an identity/idempotency contract. | No exactly-once, durable or authoritative multiplayer claim. |

**Consumers:** P11 implements the recorded corrections. P02 EVAL-001 adapts only
the two send-buffering regressions through validated TR-009. P01 event ownership
(TR-010), broader laboratory reuse and Virgo Diamond remain candidate uses.
The following sections preserve the original explanations and evidence links.

## Receipt is only one boundary

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

## Make preserved reading position discoverable

P11's [unread-navigation checks](../evidence/realtime-chat/UNREAD_RUN.json) combine
anchoring with a bounded count and native return-to-live button. Hiding an
activated control requires an explicit focus destination; Enter and Space move
focus into the conversation before the button disappears. Returning manually
clears old counts. This is a local chat result, not a verified shared abstraction
or a human/assistive-technology usability finding.

## Scroll position does not establish page activity

P11's [activity checks](../evidence/realtime-chat/ACTIVITY_RUN.json) show that a
page can be at the live edge while its tab lacks focus. Keep arrival counts until
activity and reading position both permit clearing; show the same count in the
title without storing more history. Returning to earlier text preserves its anchor.
Playwright forces focus by default, so disable that override when testing native
tab transitions. Headless visibility still needs an explicitly bounded probe;
do not describe it as real minimized-window or human attention verification.
