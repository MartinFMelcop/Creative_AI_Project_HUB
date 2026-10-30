#!/usr/bin/env python3
"""Independently protect actual workflow routing and retained wrapper coverage.

This is a bounded reader of this workflow's indentation, not a general YAML parser.
It does not execute or claim completion of the workflow.
"""
import ast
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT.parents[1] / '.github/workflows/lab-checks.yml'
EXPECTED = {
    'Verify portable gameplay owners in actual existing consumers': 'intake',
    'Execute recovered progression and original C# destination': 'progression',
    'Execute crafting source assay and connected preparation consumer': 'crafting',
    'Execute identity intake and transactional prepared actions': 'loadout',
    'Execute persistent joint-state recovery and process failures': 'recovery',
    'Execute narrative continuity and event-owned outcomes': 'narrative',
    'Execute input timing and actual C# work consumer': 'input_timing',
    'Execute visible confirmed identity and its actual owned journey': 'intake',
    'Execute authored preparations and affected sampling/conditions/memory/field consumers': 'field',
    'Exercise actual visual C# input lifecycle': 'input_timing',
    'Execute embodied Crossing presentation and actual browser controls': 'presentation',
    'Execute original C# composition and actual real-time playback': 'audio',
    'Execute coherent authored C# scene and actual browser consequences': 'authored_scene',
    'Execute exact item identities and actual retained-tool output use': 'tooling',
    'Execute selected reputation source contracts and actual service consumer': 'reputation',
    'Execute source-bound status, selected passives and actual C# practice consumer': 'combat',
    'Execute actual repair-to-watering journey and affected availability controls': 'availability',
    'Rebuild and execute the actual recipient demonstration without SDK on its PATH': 'recipient',
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def steps(text):
    match = re.search(r'^  north-star-csharp:\n(?P<body>.*?)(?=^  [A-Za-z][\w-]*:\n|\Z)', text, re.M | re.S)
    require(match is not None, 'Missing C# job')
    job = match.group('body')
    chunks = re.split(r'(?=^      - )', job, flags=re.M)
    rows = {}
    for chunk in chunks[1:]:
        name = re.search(r'^      - name: (.+)$', chunk, re.M)
        if not name:
            continue
        label = name.group(1)
        require(label not in rows, 'Duplicate step: ' + label)
        rows[label] = chunk
    return job, rows


def run_body(chunk):
    match = re.search(r'^        run: (.*)$', chunk, re.M)
    require(match is not None, 'Missing actual command')
    if match.group(1) != '|':
        return match.group(1)
    following = chunk[match.end():].splitlines()
    lines = []
    for line in following:
        if not line:
            continue
        if not line.startswith('          '):
            break
        lines.append(line[10:])
    return '\n'.join(lines)


def validate_workflow(text):
    job, rows = steps(text)
    require("if: needs.scope.outputs.north_star_csharp == 'true'" in job, 'C# job gate changed')
    require('timeout-minutes: 8' in job, 'C# timeout changed')
    require("north_star_csharp: ${{ steps.affected.outputs.north_star_csharp == 'true' || steps.csharp.outputs.required == 'true' }}" in text,
            'New C# selection may not suppress old required job scope')
    for output in ('suites', 'browser'):
        require(f'csharp_{output}: ${{{{ steps.csharp.outputs.{output} }}}}' in text, 'Missing routing output')
    executed = {name for name, row in rows.items() if re.search(r'^        if: contains\(fromJSON\(needs.scope.outputs.csharp_suites\)', row, re.M)}
    require(executed == set(EXPECTED), 'Actual guarded verification steps differ')
    for name, key in EXPECTED.items():
        row = rows[name]
        require(f"        if: contains(fromJSON(needs.scope.outputs.csharp_suites), '{key}')\n" in row,
                'Wrong suite guard: ' + name)
        body = run_body(row)
        require(body.strip() not in ('', 'true', ':', 'echo skipped'), 'Verification command removed: ' + name)
    require(run_body(rows['Verify portable gameplay owners in actual existing consumers']) == 'python3 labs/build-operations/portable-core/verify.py --dotnet dotnet --output "$RUNNER_TEMP/portable-core"', 'Portable owner instrument missing')
    field = run_body(rows['Execute authored preparations and affected sampling/conditions/memory/field consumers'])
    require(field == 'python3 north-star/field-journey/tools/preparation-verify.py --dotnet dotnet --output "$RUNNER_TEMP/preparation-authoring"',
            'Field wrapper no longer supplies declared nested coverage')
    sdk = rows['Require the pinned SDK for every selected C# suite']
    require('\n        if:' not in sdk and run_body(sdk) == 'test "$(dotnet --version)" = "10.0.401"', 'SDK pin is conditional or missing')
    for name in ('Install existing locked browser instrument', 'Install matching browser for C# interaction verification'):
        require("        if: needs.scope.outputs.csharp_browser == 'true'\n" in rows[name], 'Browser setup guard differs')
    diagnostics = [row for name, row in rows.items() if name.startswith('Retain ')]
    require(len(diagnostics) == 9, 'Retained C# diagnostic steps differ')
    require(all('\n        if: failure()\n' in row and 'actions/upload-artifact@' in row for row in diagnostics),
            'Failure diagnostics were weakened')
    return {'verification_steps': len(EXPECTED), 'suite_keys': len(set(EXPECTED.values()))}


def command_strings(path):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'commands' for t in node.targets) and isinstance(node.value, ast.List):
            return [v.value for v in ast.walk(node.value) if isinstance(v, ast.Constant) and isinstance(v.value, str)]
    raise ValueError('No retained command list: ' + str(path))


def validate_wrappers(overrides=None):
    contracts = {
        'north-star/field-journey/tools/preparation-verify.py': ['tools/sampling-verify.py'],
        'north-star/field-journey/tools/sampling-verify.py': ['north-star/memory-study/tools/conditions-verify.py'],
        'north-star/memory-study/tools/conditions-verify.py': ['tools/verify.py', 'north-star/field-journey/tools/presentation-verify.py'],
        'north-star/field-journey/tools/presentation-verify.py': ['tools/verify.py'],
    }
    for name, expected in contracts.items():
        values = overrides[name] if overrides and name in overrides else command_strings(ROOT/name)
        for child in expected:
            require(values.count(child) == 1, f'Nested wrapper obligation missing/duplicated: {name} -> {child}')


class WorkflowContract(unittest.TestCase):
    def test_actual_workflow_has_all_guarded_existing_commands(self):
        self.assertEqual(validate_workflow(WORKFLOW.read_text()), {'verification_steps': 18, 'suite_keys': 16})

    def test_wrong_guard_and_removed_field_command_are_rejected(self):
        text = WORKFLOW.read_text()
        for before, after in [("'field')", "'reputation')"),
                              ('run: python3 north-star/field-journey/tools/preparation-verify.py --dotnet dotnet --output "$RUNNER_TEMP/preparation-authoring"', 'run: true')]:
            with self.subTest(defect=after), self.assertRaises(ValueError):
                validate_workflow(text.replace(before, after, 1))

    def test_legacy_job_scope_sdk_browser_and_failure_diagnostics_stay_required(self):
        text = WORKFLOW.read_text()
        mutants = [text.replace("steps.affected.outputs.north_star_csharp == 'true' || ", '', 1),
                   text.replace('run: test "$(dotnet --version)" = "10.0.401"', 'run: true', 1),
                   text.replace("if: needs.scope.outputs.csharp_browser == 'true'", 'if: false', 1)]
        job, _ = steps(text)
        mutants.append(text.replace(job, job.replace('if: failure()', 'if: false', 1), 1))
        for mutant in mutants:
            with self.assertRaises(ValueError):
                validate_workflow(mutant)

    def test_nested_wrapper_obligations_exist_once_and_false_coverage_fails(self):
        validate_wrappers()
        name = 'north-star/field-journey/tools/preparation-verify.py'
        for values in ([], ['tools/sampling-verify.py', 'tools/sampling-verify.py']):
            with self.assertRaises(ValueError):
                validate_wrappers({name: values})

    def test_shell_failure_is_not_a_successful_noop(self):
        # Shell semantics only: not a claim of executing GitHub Actions.
        r = subprocess.run(['bash', '-e', '-c', 'false\nprintf false-success'], capture_output=True)
        self.assertNotEqual(r.returncode, 0)
        self.assertEqual(r.stdout, b'')


class IndependentSourceSentinels(unittest.TestCase):
    # Literal expectations from inspected actual project/wrapper source, deliberately
    # independent of csharp_scope's own tables and graph-construction helpers.
    PREFIX = 'martin-creative-ai-lab-v0.2.0/martin-creative-ai-lab/'
    LEGACY_TREE_READERS = {'progression', 'crafting', 'loadout', 'recovery'}

    def selection(self, path):
        import csharp_scope
        return {name for name, enabled in csharp_scope.classify([self.PREFIX + path]).items() if enabled}

    def require_coverage(self, selected, required):
        require(required <= selected, 'Required independently observed source consumer omitted')

    def test_narrative_reaches_actual_scene_and_recipient_beyond_tree_fingerprints(self):
        selected = self.selection('north-star/csharp/Narrative/RequestExpedition.cs')
        self.require_coverage(selected, self.LEGACY_TREE_READERS | {'narrative', 'authored_scene', 'recipient'})
        with self.assertRaises(ValueError):
            self.require_coverage(selected - {'recipient'}, self.LEGACY_TREE_READERS | {'narrative', 'authored_scene', 'recipient'})

    def test_narrative_scene_document_is_an_actual_recipient_build_input(self):
        self.require_coverage(self.selection('north-star/csharp/Narrative/SCENE.md'),
                              {'narrative', 'authored_scene', 'recipient'})
        self.require_coverage(self.selection('north-star/authored-scene/README.md'),
                              {'authored_scene', 'recipient'})

    def test_in_root_linked_compile_input_is_not_erased_before_validation(self):
        import csharp_scope
        with tempfile.TemporaryDirectory(prefix='csharp-independent-symlink-') as folder:
            root = Path(folder)
            (root/'Real.cs').write_text('class Real {}')
            (root/'Hidden.cs').symlink_to(root/'Real.cs')
            (root/'Owner.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><ItemGroup><Compile Include="Hidden.cs" Link="Hidden.cs" /></ItemGroup></Project>')
            with self.assertRaises(ValueError):
                csharp_scope.project_inputs(root, ['Owner.csproj'])

    def test_loadout_reaches_actual_intake_and_field_transitively(self):
        selected = self.selection('north-star/csharp/Loadout/PreparedExpedition.cs')
        expected = self.LEGACY_TREE_READERS | {'intake', 'field'}
        self.require_coverage(selected, expected)
        with self.assertRaises(ValueError):
            self.require_coverage(selected - {'field'}, expected)

    def test_crossing_session_compile_link_reaches_presentation_audio_and_actual_consumers(self):
        selected = self.selection('north-star/csharp/Crossing/Session.cs')
        expected = self.LEGACY_TREE_READERS | {'narrative', 'intake', 'field', 'presentation', 'audio',
                                               'authored_scene', 'tooling', 'availability', 'recipient'}
        self.require_coverage(selected, expected)
        with self.assertRaises(ValueError):
            self.require_coverage(selected - {'presentation'}, expected)

    def test_domain_shared_change_cannot_drop_actual_dependents(self):
        selected = self.selection('north-star/csharp/Domain/Progression.cs')
        expected = self.LEGACY_TREE_READERS | {'narrative', 'intake', 'field', 'presentation', 'audio',
                                               'authored_scene', 'tooling', 'availability', 'recipient'}
        self.require_coverage(selected, expected)
        with self.assertRaises(ValueError):
            self.require_coverage(selected - {'field'}, expected)

    def test_external_field_book_runs_only_the_maximal_existing_wrapper(self):
        self.assertEqual(self.selection('north-star/field-journey/preparations.json'), {'field'})
        import csharp_scope
        result = csharp_scope.plan([self.PREFIX + 'north-star/field-journey/preparations.json'])
        self.assertTrue(result['browser'])
        self.assertTrue(result['required'])

    def test_shared_browser_lock_empty_unknown_and_manual_keep_safe_coverage(self):
        import csharp_scope
        browser_users = {'input_timing', 'intake', 'field', 'presentation', 'audio', 'authored_scene',
                         'tooling', 'reputation', 'combat', 'availability', 'recipient'}
        self.require_coverage(self.selection('projects/realtime-integration-lab/package-lock.json'), browser_users)
        for paths, full in [([], False), ([self.PREFIX + 'unknown-code/entry.cs'], False), (['README.md'], True)]:
            values = csharp_scope.classify(paths, full=full)
            self.assertEqual(set(values), set(EXPECTED.values()))
            self.assertTrue(all(values.values()))


if __name__ == '__main__':
    unittest.main()
