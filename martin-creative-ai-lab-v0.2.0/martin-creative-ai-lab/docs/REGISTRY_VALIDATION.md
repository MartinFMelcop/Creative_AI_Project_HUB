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
