# Working projects

[P11 — Live exchange](realtime-integration-lab/README.md) is the first executable
adaptation: a local Socket.IO text chat with its own locked dependencies and
protocol/browser tests. It does not require installing the other project seeds.

[P10 — The Last Waystone](waystone-dialogue/README.md) adapts nine preserved NPC
responses into a playable Python dialogue scene with consequences, four endings,
restart and a decision trace. Version 0.1.1 has 23 behavior/CLI/source checks,
with unresolved-lie agreement refusal and capped apology recovery; human creative
review remains pending. No engine or external dependency is required.

The remaining lines are described in [the seed](../SEED.md) and
[project registry](../registry/projects.json). Historical sources remain in
the archive. Add a working project only when it has concrete material, a
defined scope, acceptance criteria, and its own execution instructions.

[P02 — EVAL-001](../evaluations/chat-send-buffering/README.md) is an executable
task harness under `evaluations/`, using P11's app and tests without duplicating
the application. Its calibrated artifact gates do not establish model performance.
