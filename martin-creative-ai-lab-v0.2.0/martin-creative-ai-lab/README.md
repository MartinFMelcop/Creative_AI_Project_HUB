# Martin Creative AI Lab

The maintained workspace for **Creative AI Project HUB**. This directory contains
the current products, reusable media, preserved references and development records.
The outer `martin-creative-ai-lab-v0.2.0/` folder retains its original package name;
the maintained **SEED is 0.32.8**. Product versions are tracked separately.

[Portfolio overview](../../README.md) · [Working project index](projects/README.md) ·
[Current state](docs/STATE.md) · [Project registry](registry/projects.json)

## Find the right material

| Goal | Start here |
|---|---|
| Play a game, inspect an application or read the current story | [Project index](projects/README.md), then its project's setup and reading instructions |
| Review project versions, maturity, origins and evidence | [Registry](registry/projects.json) and the project's execution records |
| Browse historical creative or technical sources | [Reference library](references/README.md) and [availability catalog](references/catalog.json) |
| Read the recovered main novels and OVAs | [Literary library](references/literature/lich/README.md): 18 original PDFs / 2,407 pages plus searchable text |
| Inspect the pinned Rave reference tree | [Rave Master library](references/rave-master/README.md): 589 readable source files and 140 exclusions |
| Understand long-term MMORPG research | [North Star](north-star/README.md): vision and capability catalog; no current runtime consumer |
| Continue a development session | [State](docs/STATE.md), [agent instructions](AGENTS.md), [SEED](SEED.md) and [decisions](docs/DECISIONS.md) |

The registry contains eleven project lines. Seven current product directories
live under `projects/`; P02's working practice task lives under `evaluations/`.
P07/P08 support existing products with visual/audio assets; P09 remains a seed.
The project index distinguishes standalone Linux players, engine-dependent packs,
static browser builds, local services and reading editions.

## Develop and verify

From the repository root, enter this workspace:

```sh
cd martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab
```

Read the current state and the affected project's README before editing. Choose
dependencies and runtime checks for that project: Python 3.10+ suffices for shared
reference integrity/discovery; Project Rooms requires Node 24+; native C# rebuilds
use .NET 10 and Godot .NET 4.6.3. Source game/edition instructions cover their
specific engine, browser, packaging and production requirements.

The shared documentary gates use Python's standard library:

```sh
python3 tools/validate_repo.py
python3 tools/test_validate_repo.py
python3 tools/reference_library.py check
python3 tools/test_reference_library.py
python3 tools/test_check_manifest.py
python3 tools/check_manifest.py
```

[Validation scope](docs/REGISTRY_VALIDATION.md) explains registry, source, local
link and manifest checks. They support the affected project's tests rather than
proving gameplay, literary quality or service usability. The manifest covers every
maintained lab file exactly once; current HUB entry links are also validated.

[Lab checks](https://github.com/MartinFMelcop/Creative_AI_Project_HUB/actions/workflows/lab-checks.yml)
run the shared gates and project suites on main pushes and pull requests, including
native/source/package checks and P02's controlled baseline/reference calibration.
Job logs provide the result for each commit. Use project instructions for focused
local checks; an independent candidate/model result is not inferred from calibration.

## Preserve evidence and continuity

Update state and materially affected decisions/registries when a milestone changes.
Keep actual execution records with the relevant version, environment and hashes.
Use [SEED evolution](docs/SEED_EVOLUTION.md) to distinguish current direction from
historical assessments; older planning documents are contextual records, not proof
that their described gaps still exist.

Original creative titles and source languages stay intact. Historical snapshot
instructions are source data; adaptations belong in working projects. Literary
PDF availability does not ratify canon or verify the unavailable ZIP/policy.
North Star contribution states remain separate from product maturity and require
destination evidence before integration claims.

Martin supplies project goals and authorial direction; per-project provenance
records AI assistance, new implementation and historical origins. Automated
execution, implementing-agent review, independent human feedback and commercial
evidence are recorded separately. Consult each product/source's license and rights
notes before reuse.
