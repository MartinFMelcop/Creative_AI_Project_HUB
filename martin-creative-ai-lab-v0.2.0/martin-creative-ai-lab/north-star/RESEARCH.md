# First technical research direction

No experiment is implemented by this foundation. A promising candidate is a
small persistent **shared village state** whose supply or repair changes through
player actions. Start with one clear player interaction and consequence, not a
world renderer, account system, shard fleet or complete MMORPG skeleton.

## Gate 1 — specify a bounded command contract

Decide who owns resources, who may act, how costs/quantities are validated and
which action changes the village. Define receipts and idempotency keys scoped
to actor/command; reject key reuse with different payloads. Define observable
client state and conflicts before choosing transport, engine or database.
P01/P05 local transactions and P11 messaging/recovery are inspected candidates;
their schemas and chosen labels are not already authoritative game contracts.

## Gate 2 — implement and execute a real consumer

Choose language/storage/transport from actual consistency, latency, persistence,
deployment, license and tool requirements. A minimal process-level implementation
may precede an engine client. Verify two actors competing for the last resource,
repeated delivery, invalid/negative/unauthorized commands and no double spend.
Crash before/after acceptance: acknowledged costs/consequences survive exactly
once; incomplete writes cannot create resources. Reopening and reconnecting
clients must converge to accepted state with explicit conflict/receipt handling.

Only then record adaptation/integration against actual code, consumer and
execution evidence; evolve the catalog/validator together. A simulated fixture
checks specified behavior, not real player trust or production concurrency/load.
Keep deterministic replay/diagnostics useful without collecting unnecessary
personal data. A failure or unavailable dependency remains a failed/incomplete gate.

## Gate 3 — assess experience and continuation cost

Give independent participants a small shared goal and observe whether consequences,
cooperation and recovery are understandable. Assess abuse/authorization boundaries,
accessibility, moderation/operations ownership and production cost before public
use. Social benefit, enjoyment, infrastructure scale and commercial demand need
separate evidence. Expand only if the experiment supports it; compare current
independent products and creative opportunities before investing further.

Literary/Rave concepts remain optional. No village name, species, magic, historical
quest or class enters North Star canon through a technical transfer.
