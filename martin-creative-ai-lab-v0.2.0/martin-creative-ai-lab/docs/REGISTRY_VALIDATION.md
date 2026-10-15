# Registry reference validation

Run `python3 tools/validate_repo.py` from the lab directory. Run the regression
suite with `python3 -m unittest discover -s tools -p 'test_*.py' -v`.

The gate now checks project and transfer `evidence` lists, optional asset
`evidence`, project `working_path`, and project `source_id`. An evidence entry
must be a nonempty string naming an existing file relative to the lab root.
URLs, absolute paths, directories, missing files and resolved paths outside the
lab fail. Symlinks are allowed only when the resolved target remains inside the
lab. Working paths must resolve to existing directories; source IDs must match
the legacy-source registry. Empty evidence lists remain valid for seeds and
candidate transfers. Existing asset records need not introduce an evidence field.

These checks retain registry schema version 1 and use Python's standard library.
They share one path checker rather than separate field-specific implementations.
Markdown checks still exclude dependency documentation, and preserved archive
integrity remains mandatory. Evidence path checks do not parse the referenced
report, prove its claims, impose a maturity threshold, or execute its project.

The original recorded validator passed malformed references rejected by eight
regressions added alongside the three original methods.
[Execution evidence](../evidence/registry-validation/RUN.json) records the base,
source hashes, raw baseline/current output and existing project regression runs.
The baseline failure is intentional defect reproduction, not a current failure.

That registry-validation increment did not change project maturity, task contracts,
dependencies, transfer status or historical sources.

## HUB entry navigation — v0.32.3

In the maintained `martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/` wrapper,
the Markdown gate also scans the repository root's `README.md` and `AGENTS.md`.
Lab documentation can link back to those HUB entry files; resolved Markdown targets
must stay within the repository. Standalone lab checkouts/fixtures retain their
lab-only boundary. Registry evidence and working paths remain strictly lab-local.

The validator suite now has 13 test methods. Its wrapped-HUB regression verifies
a valid entry link and lab backlink, and rejects missing targets and repository
escapes. Historical snapshot links and dependency documentation remain excluded;
their existing integrity rules still apply. The gate checks file/directory targets,
not fragments, external URLs, rendering or claims in reports. Review changed anchors
and presentation separately; the existing root workflow runs this gate in CI.

## Complete manifest coverage

Run `python3 tools/check_manifest.py` from the lab directory, and
`python3 tools/test_check_manifest.py` for its 11 regressions. Git is a prerequisite;
a missing inventory fails rather than checking only whatever rows are supplied.
The existing documentary validator remains a separate gate.

The required inventory is Git-tracked plus nonignored untracked files under the
lab root, with `MANIFEST.sha256` excluded to avoid self-reference. Root repository
files outside this nested lab, including the GitHub workflow, are outside this
manifest's scope. Ignored dependency/cache outputs are excluded; tracked ignored
files still require coverage. Stage intended deletions before regenerating the
manifest so deleted index entries cease to be required. Regenerate the manifest
after final maintained content changes, then run both integrity checks.

Require one lowercase SHA-256 digest, two spaces and a canonical relative POSIX
path per line. Spaces inside filenames are supported. Duplicate, malformed,
absolute, traversal, self-reference and stale entries fail. Every maintained file
must be listed and readable as a regular file within the lab; symlink substitution
and mismatched file bytes fail. Escaped/newline filenames are unsupported.
`--root PATH` selects a lab checkout; `--manifest PATH` inspects an alternative
list without replacing the maintained manifest. Both retain the same coverage rule.

The former `sha256sum --strict -c` command accepted a list omitting `scene.py`.
The new gate rejects that same omission and accepts the complete list.
[Actual execution](../evidence/continuous-integration/MANIFEST_RUN.json) records
the comparison and real nested-Git fixtures. Matching hashes establish file
integrity against this list, not authenticity or product runtime behavior.

## Reference library and North Star foundation — v0.32.0

`validate_repo.py` now calls the stdlib `reference_library.py` gate. Its independent
`check` / `find` commands validate and discover the same catalog, without executing
historical scripts or downloading sources. Project `reference_collection_ids`
are optional known catalog IDs; existing source/transfer/maturity schemas remain.
The old source archive metadata/hash and selected per-file checks are retained.

Require unique collection/source/topic/capability IDs; canonical local paths;
no symlink substitution; exact imported inventory coverage/counts; SHA-256/size/
Git blob agreement; UTF-8 text-only payloads; inert control-file mappings; explicit
excluded payload reasons and prior withheld digests. Discovery targets must name
actual imported sources. Unavailable attachments cannot invent a hash, inventory,
version, imported count or ratified authority. Historical reports are not payload.

Raw source documents below **validated catalog snapshot roots** are historical
data: their old links are not current HUB navigation. Their original bytes remain
checked against inventories and the global manifest. Maintained reference/library/
program documents and existing working-project links are still checked. Negative
tests demonstrate this distinction, source omission/tampering/escapes, duplicate
records, bad discovery, unsafe imports, old archive corruption and invented claims.

The North Star stage is `foundation_only`, with no chosen engine or consumer.
Only candidate/origin-verified contribution states are valid; adapted/integrated/
external claims fail. A later real consumer needs an intentional contract/stage
update and destination evidence. Origin report paths establish structured
traceability, not independent verification of every reported result, rights,
fictional authority, player experience or market demand. These checks do not
prove source authenticity beyond the recorded Git/hash provenance.
