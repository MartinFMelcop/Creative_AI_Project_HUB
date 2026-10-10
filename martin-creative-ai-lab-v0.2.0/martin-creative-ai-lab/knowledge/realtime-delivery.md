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
path. Volatile emission and an offline guard prevent buffered offline sends in
this bounded prototype. They do not guarantee delivery during transport races.

Candidates: TR-009 could turn the reproduced defect into a P02 evaluation task;
TR-010 could inform P01 event ownership. Both require destination-specific
criteria and tests before claiming a completed transfer. A chat is not a game
lobby or authoritative multiplayer system. A public reference solution must
not be treated as private evaluation material. No component was promoted to
`shared/` in this session.
