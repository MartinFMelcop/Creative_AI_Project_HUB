#!/usr/bin/env python3
"""Verify routing against current consumers, graph changes and unsafe narrow plans."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import csharp_scope as scope


def w(name):return scope.WORKSPACE+name

def chosen(*names):return {k for k,v in scope.classify([w(n) for n in names]).items() if v}

class CurrentContracts(unittest.TestCase):
    def test_field_book_selects_one_atomic_existing_wrapper(self):
        p=scope.plan([w('north-star/field-journey/preparations.json')])
        self.assertEqual(p['suites'],['field']);self.assertTrue(p['browser']);self.assertFalse(p['full_fallback'])
        self.assertEqual(len(p['wrapper_coverage']['field']),6)

    def test_field_sources_and_memory_remain_inside_maximal_wrapper(self):
        for path in ['north-star/field-journey/Preparation/Cards.cs','north-star/field-journey/Sampling/SampleCase.cs','north-star/memory-study/Conditions/Conditions.cs']:
            with self.subTest(path=path):self.assertEqual(chosen(path),{'field'})

    def test_intake_reaches_standalone_and_field_consumers(self):
        self.assertEqual(chosen('north-star/intake/Host/Room.cs'),{'intake','field'})

    def test_domain_reaches_real_reverse_consumers(self):
        self.assertEqual(chosen('north-star/csharp/Domain/Progression.cs'),set(scope.SUITES)-{'input_timing','reputation','combat'})

    def test_session_link_reaches_presentation_and_audio(self):
        suites=chosen('north-star/csharp/Crossing/Session.cs')
        self.assertTrue({'presentation','audio','authored_scene','recipient','intake','field','tooling','availability','narrative'}<=suites)
        self.assertTrue(set(scope.WHOLE_CSHARP_BINDINGS)<=suites)
        p=scope.plan([w('north-star/csharp/Crossing/Session.cs')])
        links=p['graph']['presentation']['linked_inputs']
        self.assertTrue(any(x['kind']=='Compile' and x['input']=='north-star/csharp/Crossing/Session.cs' for x in links))

    def test_whole_tree_identity_gates_are_not_pruned(self):
        self.assertEqual(chosen('north-star/csharp/InputTiming/WorkRoom.cs'),set(scope.WHOLE_CSHARP_BINDINGS)|{'input_timing'})

    def test_narrative_reaches_actual_scene_and_recipient(self):
        self.assertEqual(chosen('north-star/csharp/Narrative/RequestExpedition.cs'),set(scope.WHOLE_CSHARP_BINDINGS)|{'narrative','authored_scene','recipient'})

    def test_loadout_reaches_existing_prepared_consumers(self):
        self.assertEqual(chosen('north-star/csharp/Loadout/PreparedExpedition.cs'),set(scope.WHOLE_CSHARP_BINDINGS)|{'intake','field'})

    def test_actual_packager_and_runtime_lock_are_recipient_only(self):
        for path in ('delivery/authored-scene/package.py','delivery/authored-scene/runtime-lock.json','delivery/authored-scene/bundle/run-demo.sh'):
            with self.subTest(path=path):self.assertEqual(chosen(path),{'recipient'})

    def test_independent_combat_and_reputation_remain_separate(self):
        self.assertEqual(chosen('north-star/combat-study/Rules/Passives.cs'),{'combat'})
        self.assertEqual(chosen('north-star/reputation-study/Rules/Standing.cs'),{'reputation'})

    def test_shared_browser_lock_reaches_all_actual_browser_groups(self):
        self.assertEqual(chosen('projects/realtime-integration-lab/package-lock.json'),set(scope.BROWSER))

    def test_external_origin_recovery_dependency_is_not_lost(self):
        self.assertEqual(chosen('projects/realtime-integration-lab/rooms-backup.cjs'),{'recovery'})
        self.assertEqual(chosen('projects/eclipse-fair/Cli/Journal.cs'),{'crafting','recovery'})
        self.assertEqual(chosen('north-star/authored-scene/README.md'),{'authored_scene','recipient'})
        self.assertEqual(chosen('north-star/csharp/Narrative/SCENE.md'),{'narrative','authored_scene','recipient'})

    def test_external_input_source_reaches_actual_timing_consumer(self):
        self.assertEqual(chosen('projects/tokyo80s/dist/review.js'),{'input_timing'})
        self.assertEqual(chosen('projects/waystone-dialogue/browser/dist/deferred-request.js'),{'narrative'})

    def test_unrelated_known_application_and_docs_do_not_trigger_csharp(self):
        for name in ['projects/realtime-integration-lab/public/client.js','docs/STATE.md','knowledge/README.md']:
            self.assertEqual(chosen(name),set())

    def test_unknown_missing_and_protected_source_inputs_fail_broad(self):
        for name in ['north-star/future/Program.cs','shared/future.cs','north-star/field-journey/deleted.js','references/rave-master/future.csv','tools/csharp_scope.py','north-star/csharp/global.json']:
            with self.subTest(name=name):self.assertEqual(chosen(name),set(scope.SUITES))

    def test_workflows_manual_empty_and_union(self):
        self.assertTrue(all(scope.classify(['.github/workflows/lab-checks.yml']).values()))
        self.assertTrue(all(scope.classify([]).values()))
        self.assertTrue(all(scope.classify(['README.md'],full=True).values()))
        self.assertEqual(chosen('north-star/combat-study/Rules/Passives.cs','north-star/field-journey/preparations.json'),{'combat','field'})

    def test_noncanonical_paths_are_not_treated_as_documents(self):
        for value in ['', '../README.md','/README.md','./README.md',w('docs/../future.py'),'x\0y']:
            with self.subTest(value=value),self.assertRaises(ValueError):scope.classify([value])

    def test_cli_fixed_output_and_machine_readable_selected_keys(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'out';report=Path(td)/'report';out.write_text('previous=value\n')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(scope.main(['--path',w('north-star/field-journey/preparations.json'),'--output',str(out),'--report',str(report)]),0)
            values=dict(line.split('=',1) for line in out.read_text().splitlines())
            self.assertEqual(set(values),set(scope.SUITES)|{'previous','suites','browser','required'})
            self.assertEqual(json.loads(values['suites']),['field']);self.assertEqual(values['browser'],'true');self.assertEqual(values['required'],'true')
            self.assertFalse(json.loads(report.read_text())['full_fallback'])

    def test_unknown_suite_and_removed_runtime_or_wrapper_contract_reject(self):
        extra=copy.deepcopy(scope.EXTRA);extra['surprise']=('x',)
        with self.assertRaises(ValueError):scope.validate_contracts(extra=extra)
        extra=copy.deepcopy(scope.EXTRA);extra['field']=tuple(x for x in extra['field'] if x!='north-star/memory-study/')
        with self.assertRaises(ValueError):scope.validate_contracts(extra=extra)
        with self.assertRaises(ValueError):scope.validate_contracts(coverage={'field':('preparation-verify.py',)})

class BuildGraph(unittest.TestCase):
    def fixture(self,root):
        (root/'host').mkdir();(root/'rules').mkdir()
        (root/'host/App.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><ItemGroup><ProjectReference Include="../rules/Rules.csproj"/><Compile Include="../rules/Shared.cs" Link="Shared.cs"/><Content Include="book.json" CopyToOutputDirectory="PreserveNewest"/></ItemGroup></Project>')
        (root/'rules/Rules.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"/>')
        (root/'rules/Shared.cs').write_text('class Shared {}');(root/'host/Program.cs').write_text('class Program {}');(root/'host/book.json').write_text('{}')

    def test_transitive_reference_link_and_runtime_content_are_real_inputs(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root);g=scope.project_inputs(root,['host/App.csproj'])
            self.assertEqual(set(g['inputs']),{'host/App.csproj','host/Program.cs','host/book.json','rules/Rules.csproj','rules/Shared.cs'})
            self.assertEqual(g['project_edges'],[['host/App.csproj','rules/Rules.csproj']])
            self.assertTrue(any(x['kind']=='Content' and x['input']=='host/book.json' for x in g['linked_inputs']))

    def test_missing_runtime_and_reference_are_not_silently_omitted(self):
        for filename in ['host/book.json','rules/Rules.csproj']:
            with tempfile.TemporaryDirectory() as td:
                root=Path(td);self.fixture(root);(root/filename).unlink()
                with self.assertRaises(ValueError):scope.project_inputs(root,['host/App.csproj'])

    def test_conditions_imports_packages_and_unreviewed_globs_fail_closed(self):
        for tag in ['<ProjectReference Include="../rules/Rules.csproj" Condition="true"/>','<Import Project="x.props"/>','<PackageReference Include="x" Version="1"/>','<Compile Include="../rules/*.cs"/>','<Target Name="x"/>']:
            with tempfile.TemporaryDirectory() as td:
                root=Path(td);self.fixture(root);(root/'host/App.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><ItemGroup>'+tag+'</ItemGroup></Project>')
                with self.assertRaises(ValueError):scope.project_inputs(root,['host/App.csproj'])

    def test_linked_runtime_or_parent_directory_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root);(root/'host/book.json').unlink();(root/'host/book.json').symlink_to(root/'rules/Shared.cs')
            with self.assertRaises(ValueError):scope.project_inputs(root,['host/App.csproj'])
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);self.fixture(root);(root/'linked').symlink_to(root/'host',target_is_directory=True)
            with self.assertRaises(ValueError):scope.project_inputs(root,['linked/App.csproj'])

    def test_in_root_reference_and_compile_symlinks_are_not_dereferenced_first(self):
        for relative in ('rules/Rules.csproj','rules/Shared.cs'):
            with tempfile.TemporaryDirectory() as td:
                root=Path(td);self.fixture(root);path=root/relative;data=path.read_bytes();path.unlink();real=root/('real-'+path.name);real.write_bytes(data);path.symlink_to(real)
                with self.assertRaises(ValueError):scope.project_inputs(root,['host/App.csproj'])

    def test_unsupported_build_graph_selects_all_existing_contracts(self):
        with mock.patch.object(scope,'project_inputs',side_effect=ValueError('unsupported fixture')):
            result=scope.plan([w('north-star/field-journey/preparations.json')])
        self.assertTrue(result['full_fallback']);self.assertEqual(set(result['suites']),set(scope.SUITES))

if __name__=='__main__':unittest.main()
