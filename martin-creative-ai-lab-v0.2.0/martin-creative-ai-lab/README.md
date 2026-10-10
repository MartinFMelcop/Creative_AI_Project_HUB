# Martin Creative AI Lab

An evolving laboratory of games, narrative, images, audio, data, and AI
evaluation by **Martin Melcop Neto**. Projects are adaptable seeds: build small
slices, verify behavior, record decisions, and test reuse in actual destinations.

**Current seed: v0.3.1.** The lab includes eleven project lines, 178 preserved
historical texts, and one working local text-chat adaptation. No game migration,
model benchmark, finished music catalogue, or public deployment is claimed.
The containing directory keeps its original v0.2.0 package name.

## Start here

- [State](docs/STATE.md): completed increment, limits, and next action.
- [Assessment](docs/ASSESSMENT.md) and [improvement plan](docs/IMPROVEMENT_PLAN.md): evidence and selected priorities.
- [P11 — Live exchange](projects/realtime-integration-lab/README.md): install, run, test, provenance, and contribution.
- [Current execution evidence](evidence/realtime-chat/POLLING_SEND_RUN.json): transport regressions, source versions, environment, and artifact hashes.
- [SEED.md](SEED.md), [agent instructions](AGENTS.md), and [decisions](docs/DECISIONS.md): direction and operating context.
- [Project registry](registry/projects.json) and [legacy inventory](registry/legacy_sources.json): IDs and evidence boundaries.
- [Recovered sources](docs/LEGACY_REPOSITORIES.md): historical snapshots and their limitations.

Original creative titles include Artemyra / ArtemiZ4, Tokyo 80s,
O Lich mais velho da tumba mais antiga, The Dark Knight, and Véu Partido.
Their complete runtime baselines are not present here. Rave Master supplies
selected narrative, combat, and production material; planned art/audio indices
do not establish available masters. [The assessment](docs/ASSESSMENT.md) states
what was actually inspected or executed.

## Verify the lab

From this lab directory, with Python 3.9+:

```bash
python3 tools/validate_repo.py
python3 tools/test_validate_repo.py
sha256sum -c MANIFEST.sha256
```

The first check validates registries, local Markdown file links, and preserved
source hashes, excluding dependency documentation under `node_modules`. The
regression suite checks that maintained broken links and archive corruption still
fail. The manifest covers maintained files inside this lab, excluding
itself, ignored dependencies, and generated outputs. Neither check runs projects.
P11 has its own installation and test commands; other projects do not need to
be installed to develop it.

The original delivery test failed on the preserved source and passed on 0.1.0.
Two further send-path regressions fail on that committed client and pass on 0.1.1.
Seventeen current automated tests verify the local contract, including connected
polling congestion and stale-state reconnect buffering. New
documentation, UI, code comments, and evidence are in English; historical texts
remain in their original language. Martin supplied direction and authorization;
Codex performed this increment. Manual usability review by Martin is pending.

Candidate transfers remain candidates until a destination uses and verifies
them. Publication and deployment require separate authorization; this session
produces a local working sample and resumable repository state.
