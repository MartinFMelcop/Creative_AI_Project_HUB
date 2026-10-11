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

The recorded validator passed malformed references that the new eight regression
methods reject. Together with the existing three methods, the suite has 11 tests.
[Execution evidence](../evidence/registry-validation/RUN.json) records the base,
source hashes, raw baseline/current output and existing project regression runs.
The baseline failure is intentional defect reproduction, not a current failure.

No project maturity, task contract, chat version, dependency, transfer status or
historical source changes in this iteration. Human P11 review and an independent
EVAL-001 artifact remain the next product/evaluation gates.

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
