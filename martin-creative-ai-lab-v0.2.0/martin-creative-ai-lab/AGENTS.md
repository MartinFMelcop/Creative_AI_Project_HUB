# Maintained workspace instructions

Read repository-root `AGENTS.md` and the complete current
[operating instructions](docs/prompts/CONTINUOUS_DEVELOPMENT.md), then
[STATE](docs/STATE.md). Those documents define safeguards, process and initiative
continuity respectively. This file owns local execution details, not a parallel plan.
Respond in Brazilian Portuguese. New technical documentation, persistent instructions,
code comments and Git messages use English; preserve creative/source languages.

## Local boundaries

Use relevant SEED sections, registries, product/design records and actual artifacts
selectively. P01–P11 registry entries retain historical source provenance; each has a mandatory
laboratory destination in `labs/origins.json`. Incomplete destinations are not
operational laboratories; origin execution is not destination integration. Track
legacy consumption as INTEGRATED, REJECTED or genuinely UNRESOLVED. The new production
stack is Unity/C#, with Windows priority and Steam intended; retained Godot execution
is migration evidence, not a competing undecided engine direction. Follow
[brains/README.md](brains/README.md) for proportional retrieval and
[references/AGENTS.md](references/AGENTS.md) for preserved source contracts. Knowledge
outside the five protected sources is contextual and revisable, with provenance and
limits. Keep meaningful negative/inconclusive results. Attribute human actions only
when observed; agent review is not independent human validation.

## Verification from this directory

Use Python 3.11+ and the actual affected consumer's documented runtime. Keep
tool/runtime/dependency versions pinned; diagnose the environment before intentional
upgrades. Required repository source/link/structure gates are:

```bash
python3 tools/validate_repo.py
python3 tools/reference_library.py check
python3 tools/brain_query.py check
python3 tools/check_transformation.py
```

Run affected regressions and actual laboratory instruments, plus C# domain/destination
checks where affected. Never replace Unity/Windows execution with a source build.
Run `python3 tools/test_transformation.py` for transformation-contract changes.
Run affected regressions and integration checks; the actual required CI jobs live in
`../../.github/workflows/lab-checks.yml`. For operating-validator changes run
`python3 tools/test_validate_repo.py`; source/query/manifest tooling has corresponding
`tools/test_*.py` suites. Unchanged product/engine suites need not be repeated locally
without an affected contract; CI gates remain intact.

After final intended content changes, regenerate exact maintained coverage using the
existing inventory, then check it:

```bash
python3 - <<'PYMANIFEST'
import hashlib
from pathlib import Path
from tools.check_manifest import maintained_files
root = Path.cwd()
(root / 'MANIFEST.sha256').write_text(''.join(
    f"{hashlib.sha256((root / name).read_bytes()).hexdigest()}  {name}\n"
    for name in sorted(maintained_files(root))))
PYMANIFEST
python3 tools/check_manifest.py
```

The manifest tracks maintained files, not authorization to alter pinned originals.
Keep scratch outputs outside this workspace, in the task's `work/` directory. Review
complete/staged diffs, commit only intended files and follow root Git safeguards.
Report real checks/limits, stored commit message, local/remote SHA and CI separately.
