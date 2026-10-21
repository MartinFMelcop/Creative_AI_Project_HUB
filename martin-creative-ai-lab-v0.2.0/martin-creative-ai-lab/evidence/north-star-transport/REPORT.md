# Controlled transport observations

Actual pinned Godot 4.6.3, unchanged source gameplay and fixed native-input policy.
Sixteen sequential source encounters, two takes per role/profile; alternate profile order.
A separate two-encounter existing-PCK relay smoke checks consumption, not the full impairment matrix.

| Approach | Intervention | Wins / takes | Final HP | Final cargo | Server stale clears |
|---|---|---:|---|---|---|
| Guardian | direct | 2 / 2 | [5.0, 5.0] | [3.0, 3.0] | [1, 1] |
| Guardian | relay_zero | 2 / 2 | [5.0, 5.0] | [3.0, 3.0] | [1, 1] |
| Guardian | delay_60 | 0 / 2 | [0.0, 0.0] | [1.0, 3.0] | [1, 1] |
| Guardian | batch_400 | 0 / 2 | [0.0, 0.0] | [2.0, 2.0] | [42, 42] |
| Duelist | direct | 2 / 2 | [5.0, 5.0] | [3.0, 3.0] | [1, 1] |
| Duelist | relay_zero | 2 / 2 | [5.0, 5.0] | [3.0, 3.0] | [1, 1] |
| Duelist | delay_60 | 2 / 2 | [5.0, 5.0] | [3.0, 3.0] | [1, 1] |
| Duelist | batch_400 | 0 / 2 | [0.0, 0.0] | [2.0, 2.0] | [42, 42] |

Each array retains its two actual takes. Wins/takes are observations, not population rates.
All received/forwarded frame and byte counts match; actual relay residence verifies intervention.

## Interpretation and next decision

Direct and no-added-delay controls finish with health 5/cargo 3 in both roles. With 60 ms retained
in each direction, the final Guardian policy loses both takes; Duelist finishes both with 5/3.
Both policies lose under 400 ms downstream grouping. An earlier exploratory Guardian delay take
won with 1 health/2 cargo; its older runner/observer/relay identities remain in pilot.json.
The common actual gameplay, View and input-policy hashes match the final study.
This variability precludes a universal player threshold or class balance conclusion.

Regular delayed arrivals do not necessarily trip the arrival-gap stale indicator. The client
measures time since receipt, not age of server state. Batching exposes the coupling between
sending intents only after new confirmations and the server 15-tick held-input lease.
Inspect actual stale clears, client status counts and paid-response counters in results.json;
they are bounded instrument observations, not human experience or measured RTT.
Stale-clear totals include terminal grace: the baseline clear need not be a live control failure.

Keep server-owned costs and fail-closed neutralization. Compare a bounded input heartbeat,
clearer freshness feedback and policy adaptation before committing to full prediction or
reconciliation. No need for an engine migration follows. Abilities/builds and independent
player observation remain credible competing work; this study does not choose that frontier.

## Controls and limits

Ten actual TCP/failure controls pass, including a disabled-delay mutant, plus three result/input
preservation controls. Missing/failed baselines would make comparison inconclusive; the actual
baseline flag is true. All 16 source terminals and 2 PCK smoke terminals match server results and
remain retained after socket closure. No costs, damage, windows, runtime or playable package changed.

Complete-frame retention/batching is not TCP loss, UDP behavior, WAN emulation, latency tolerance,
capacity, enjoyment/accessibility, security, production engine or MMO validation. Role-blocking
and reversed order do not provide randomized assignment. Two repetitions are not independent
participants. Raw schedules vary and are not exact golden equality gates.
