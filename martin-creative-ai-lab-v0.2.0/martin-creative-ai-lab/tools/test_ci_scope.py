#!/usr/bin/env python3
"""Protect affected-consumer coverage and retirement of unconditional rebuild duty."""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import ci_scope as scope


def w(path):
    return scope.WORKSPACE + path


class Classification(unittest.TestCase):
    def selected(self, *paths):
        return {name for name, enabled in scope.classify(paths).items() if enabled}

    def test_documentary_changes_do_not_rebuild_historical_players(self):
        paths = ['AGENTS.md', 'README.md'] + [w(path) for path in
            ('AGENTS.md', 'README.md', 'SEED.md', 'MANIFEST.sha256', 'docs/STATE.md',
             'registry/projects.json', 'registry/transfers.json', 'labs/README.md',
             'labs/rpg-systems/README.md', 'labs/narrative-continuity/README.md', 'labs/origins.json', 'labs/source-inventory.json',
             'north-star/DESIGN.md', 'north-star/capabilities.json', 'brains/integrity.json')]
        self.assertEqual(self.selected(*paths), set())

    def test_csharp_and_progression_only_do_not_rebuild_historical_consumers(self):
        for path in ('labs/combat-response/passives/assay.py', 'evidence/passive-response/RUN.json', 'north-star/combat-study/Rules/Passives.cs', 'north-star/field-journey/Host/Room.cs', 'evidence/field-journey/RUN.json', 'north-star/memory-study/Host/Room.cs', 'evidence/memory-study/RUN.json', 'labs/narrative-continuity/memory/run.py', 'north-star/intake/Host/Room.cs', 'evidence/intake/RUN.json', 'north-star/availability-study/Rules/Availability.cs', 'evidence/npc-availability/RUN.json', 'evidence/repair-hauling/RUN.json',
                     'labs/world-gameplay/availability/run.py', 'delivery/authored-scene/package.py', 'delivery/authored-scene/dist/authored-scene-demo-linux-x64.zip',
                     'north-star/tooling-study/Rules/Tooling.cs', 'evidence/tooling-study/RUN.json', 'north-star/reputation-study/Rules/Standing.cs', 'evidence/reputation-study/RUN.json', 'evidence/request-continuity/RUN.json', 'evidence/recipient-delivery/RUN.json', 'north-star/combat-study/Host/Trial.cs', 'labs/combat-response/status/run.py',
                     'evidence/combat-status/RUN.json', 'north-star/authored-scene/Host/Room.cs', 'north-star/authored-scene/tools/browser.mjs',
                     'evidence/authored-scene/RUN.json', 'north-star/csharp/Domain/Progression.cs', 'labs/rpg-systems/run.py',
                     'evidence/rpg-progression/RUN.json', 'labs/economy-simulation/run.py',
                     'evidence/economy-crafting/RUN.json', 'labs/world-gameplay/run.py',
                     'evidence/world-loadout/RUN.json', 'labs/networking-persistence/run.py',
                     'evidence/persistent-expedition/RUN.json', 'labs/narrative-continuity/run.py',
                     'labs/narrative-continuity/test_instrument.py', 'evidence/narrative-continuity/RUN.json',
                     'evidence/narrative-continuity/results.json', 'labs/input-timing/run.py',
                     'labs/input-timing/browser.mjs', 'evidence/input-timing/results.json',
                     'references/rave-master/source/PLAYER_LEVEL_STAT_BUDGET.csv'):
            with self.subTest(path=path):
                self.assertEqual(self.selected(w(path)), {'north_star_csharp'})

    def test_existing_origin_implementations_keep_their_actual_jobs(self):
        cases = {'projects/eclipse-fair/Core/Game.cs': 'eclipse_economy',
                 'projects/cinderwatch/tools/check_linux.py': 'eclipse_economy',
                 'projects/veil-arena/arena.gd': 'native_arena',
                 'labs/combat-response/cases.json': 'native_arena',
                 'projects/tokyo80s/public/game.js': 'chat_evaluation',
                 'projects/waystone-dialogue/browser/public/app.js': 'chat_evaluation',
                 'projects/realtime-integration-lab/package-lock.json': 'chat_evaluation',
                 'evaluations/chat-send-buffering/runner.py': 'chat_evaluation',
                 'tools/check_calibration.py': 'chat_evaluation',
                 'labs/ai-evaluation/run.py': 'chat_evaluation',
                 'evidence/ai-evaluation/candidate-client.js': 'chat_evaluation'}
        for path, expected in cases.items():
            with self.subTest(path=path):self.assertEqual(self.selected(w(path)), {expected})

    def test_shared_prototype_model_and_delivery_keep_all_native_owners(self):
        for path in ('combat.gd', 'route.gd', 'fittings.gd', 'data/fittings.json',
                     'project.godot', 'dist/crossing-drill.pck', 'tools/export_linux.py', 'tests/policy.gd'):
            with self.subTest(path=path):
                self.assertEqual(self.selected(w('north-star/prototype/' + path)), set(scope.PROTOTYPE))

    def test_authority_changes_do_not_enable_unrelated_csharp_or_origin_jobs(self):
        self.assertEqual(self.selected(w('north-star/prototype/authority/server.gd')), set(scope.NETWORK))

    def test_recorded_consumer_baselines_keep_runtime_checks(self):
        for prefix, expected in [('eclipse-fair', {'eclipse_economy'}),
                                 ('combat-response', {'native_arena'}),
                                 ('north-star-preparation', set(scope.PROTOTYPE)),
                                 ('rpg-progression', {'north_star_csharp'}),
                                 ('narrative-continuity', {'north_star_csharp'}),
                                 ('realtime-chat', {'chat_evaluation'})]:
            with self.subTest(prefix=prefix):
                self.assertEqual(self.selected(w(f'evidence/{prefix}/results.json')), expected)

    def test_visual_method_keeps_both_actual_engine_and_destination_owners(self):
        for path in ('labs/visual-animation/run.py', 'labs/visual-animation/browser.mjs',
                     'evidence/visual-animation/results.json', 'labs/audio-music/run.py',
                     'labs/audio-music/browser.mjs', 'evidence/audio-music/source.json'):
            with self.subTest(path=path):
                self.assertEqual(self.selected(w(path)), {'native_arena', 'north_star_csharp'})

    def test_unknown_shared_tools_workflows_and_roots_fail_broad(self):
        for path in ('.github/workflows/lab-checks.yml', '.github/actions/runtime/action.yml',
                     w('tools/new_runtime_helper.py'), w('shared/transactions.cs'),
                     w('projects/new-consumer/entry.py'), 'global.json', 'future-code/main.cs'):
            with self.subTest(path=path):self.assertEqual(self.selected(path), set(scope.JOBS))
        self.assertEqual(self.selected(w('tools/ci_scope.py')), set(scope.JOBS))

    def test_empty_and_manual_scopes_run_every_retained_contract(self):
        self.assertEqual(scope.classify([]), dict.fromkeys(scope.JOBS, True))
        self.assertEqual(scope.classify(['README.md'], full=True), dict.fromkeys(scope.JOBS, True))

    def test_mixed_paths_union_owners_without_losing_any_job(self):
        self.assertEqual(self.selected(w('north-star/csharp/Rules.cs'),
                                       w('projects/cinderwatch/Core/Game.cs')),
                         {'north_star_csharp', 'eclipse_economy'})

    def test_noncanonical_paths_cannot_masquerade_as_documentary_changes(self):
        for path in ('', '/README.md', '../README.md', './README.md', w('docs/../runtime.py'), 'x\0y'):
            with self.subTest(path=path), self.assertRaises(ValueError):scope.classify([path])

    def test_cli_appends_fixed_outputs_and_has_explicit_full_mode(self):
        with tempfile.TemporaryDirectory(prefix='ci-scope-output-') as folder:
            output = Path(folder)/'output';output.write_text('previous=value\n')
            with contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(scope.main(['--path', w('north-star/csharp/Rules.cs'), '--output', str(output)]), 0)
            self.assertEqual(json.loads(stdout.getvalue()), {key: key == 'north_star_csharp' for key in scope.JOBS})
            lines = output.read_text().splitlines()
            self.assertEqual(lines[0], 'previous=value')
            self.assertEqual(set(lines[1:]), {f'{key}={str(key == "north_star_csharp").lower()}' for key in scope.JOBS})
            with contextlib.redirect_stdout(io.StringIO()) as stdout:scope.main(['--full'])
            self.assertTrue(all(json.loads(stdout.getvalue()).values()))


class ActualGitDiff(unittest.TestCase):
    def test_added_deleted_and_renamed_paths_are_classified_from_real_git(self):
        with tempfile.TemporaryDirectory(prefix='ci-scope-git-') as folder:
            repo = Path(folder)
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.STDOUT).decode().strip()
            git('init', '-q')
            old = repo/w('projects/eclipse-fair/Core/Game.cs');old.parent.mkdir(parents=True);old.write_text('retained rules\n')
            deleted = repo/w('projects/veil-arena/arena.gd');deleted.parent.mkdir(parents=True);deleted.write_text('native baseline\n')
            git('add', '.')
            git('-c', 'user.name=Scope test', '-c', 'user.email=scope@example.invalid', 'commit', '-qm', 'Baseline')
            base = git('rev-parse', 'HEAD')
            renamed = repo/w('projects/realtime-integration-lab/rules.cs');renamed.parent.mkdir(parents=True);old.rename(renamed)
            deleted.unlink()
            added = repo/w('north-star/csharp/new file café.cs');added.parent.mkdir(parents=True);added.write_text('new domain\n')
            git('add', '-A')
            git('-c', 'user.name=Scope test', '-c', 'user.email=scope@example.invalid', 'commit', '-qm', 'Move and add')
            paths = scope.changed_paths(repo, base, 'HEAD')
            self.assertEqual(set(paths), {old.relative_to(repo).as_posix(), deleted.relative_to(repo).as_posix(),
                                          renamed.relative_to(repo).as_posix(), added.relative_to(repo).as_posix()})
            self.assertEqual({job for job, enabled in scope.classify(paths).items() if enabled},
                             {'eclipse_economy', 'native_arena', 'chat_evaluation', 'north_star_csharp'})
            self.assertTrue(all(scope.classify(scope.changed_paths(repo, 'HEAD', 'HEAD')).values()))
            with self.assertRaises(ValueError):scope.changed_paths(repo, '--all', 'HEAD')
            with self.assertRaises(ValueError):scope.changed_paths(repo, 'missing-revision', 'HEAD')


if __name__ == '__main__':
    unittest.main()
