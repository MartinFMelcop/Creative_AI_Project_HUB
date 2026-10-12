#!/usr/bin/env python3
"""Integrated rescue scenarios, boundary conditions, CLI and legacy reuse."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

from adventure import Adventure, VERSION
from scene import Scene

HERE = Path(__file__).resolve().parent


def play(actions, game=None):
    game = game or Adventure()
    for action in actions:
        game.act(action)
    return game


BRIDGE = ['rope', 'timber', 'ready', 'herbs', 'bargain', 'causeway',
          'iven', 'roof', 'span', 'convoy']
FERRY = ['rope', 'oil', 'ready', 'leave', 'ferry', 'iven', 'roof',
         'board', 'row', 'row', 'load', 'board', 'row', 'finish']


class AdventureTests(unittest.TestCase):
    def test_permanent_causeway_complete_operation(self):
        game = play(BRIDGE)
        s = game.state
        self.assertEqual((s.ending, s.saved, s.medicine, s.iven, s.bridge, s.time),
                         ('FULL_RESCUE', 4, 'delivered', 'rescued', 'stable', 0))
        self.assertEqual((s.elapsed, game.workshop.state.turn), (9, 2))
        self.assertIn('Tomorrow', game.epilogue())
        self.assertEqual(game.choices(), [])

    def test_ferry_complete_operation_without_keeper_agreement(self):
        game = play(FERRY)
        s = game.state
        self.assertEqual((s.ending, s.saved, s.medicine, s.iven),
                         ('FULL_RESCUE', 4, 'delivered', 'rescued'))
        self.assertFalse(s.light)
        self.assertEqual(s.hull, 1)
        self.assertEqual(s.time, 1)
        self.assertIn('keeps its river route', game.epilogue())

    def test_cargo_order_changes_clinic_outcome_with_same_equipment(self):
        start = ['timber', 'oil', 'ready', 'leave', 'ferry', 'iven', 'roof']
        people_first = play(start + ['board', 'row', 'row', 'load', 'board', 'row'])
        medicine_first = play(start + ['load', 'board', 'row', 'row', 'board', 'row'])
        self.assertEqual(people_first.state.saved, 4)
        self.assertEqual(medicine_first.state.saved, 4)
        self.assertEqual(people_first.state.medicine, 'spoiled')
        self.assertEqual(medicine_first.state.medicine, 'delivered')
        self.assertEqual(people_first.state.ending, 'PEOPLE_SAFE')
        self.assertEqual(medicine_first.state.ending, 'FULL_RESCUE')
        self.assertEqual(people_first.state.elapsed, medicine_first.state.elapsed)
        self.assertIn('surge', people_first.history[-1]['text'])

    def test_equipment_and_rescue_order_trade_permanent_road_for_iven(self):
        base = ['timber', 'oil', 'ready', 'herbs', 'bargain', 'causeway']
        helpers = play(base + ['iven', 'roof', 'span', 'lead'])
        cargo = play(base + ['roof', 'span', 'convoy', 'finish'])
        self.assertEqual((helpers.state.saved, helpers.state.iven, helpers.state.medicine),
                         (4, 'rescued', 'waiting'))
        self.assertEqual((cargo.state.saved, cargo.state.iven, cargo.state.medicine),
                         (4, 'sheltered', 'delivered'))
        self.assertEqual(cargo.state.bridge, 'stable')

    def test_temporary_crossing_keeps_medicine_but_requires_future_repair(self):
        game = play(['rope', 'oil', 'ready', 'herbs', 'bargain', 'causeway',
                     'iven_hands', 'roof', 'lash', 'lead', 'medicine'])
        self.assertEqual((game.state.ending, game.state.bridge), ('FULL_RESCUE', 'temporary'))
        self.assertIn('replace your temporary crossing', game.epilogue())

    def test_workshop_delay_affects_clock_current_and_rescue_availability(self):
        early = play(['rope', 'oil', 'ready', 'leave', 'ferry'])
        late = play(['rope', 'oil', 'ready', 'wait', 'wait', 'leave', 'ferry'])
        self.assertEqual((early.state.elapsed, early.state.time), (3, 6))
        self.assertEqual((late.state.elapsed, late.state.time), (5, 4))
        self.assertEqual(late.state.iven, 'sheltered')
        self.assertIn('iven', [c.name for c in early.choices()])
        self.assertNotIn('iven', [c.name for c in late.choices()])
        self.assertNotEqual(early.current(), late.current())

    def test_lie_repair_carries_memory_without_restoring_lost_time(self):
        repaired = play(['rope', 'timber', 'ready', 'lie', 'apologize', 'herbs', 'bargain'])
        self.assertTrue(repaired.state.light)
        self.assertEqual((repaired.state.elapsed, repaired.state.time), (4, 5))
        repaired.act('causeway')
        self.assertNotIn('iven', [c.name for c in repaired.choices()])
        repaired.act('roof')
        repaired.act('span')
        repaired.act('lead')
        self.assertIn('council order', repaired.epilogue())
        self.assertIn('Withdrawn', repaired.epilogue())
        unresolved = play(['rope', 'timber', 'ready', 'lie', 'leave', 'retreat'])
        self.assertIn('remains uncorrected', unresolved.epilogue())
        self.assertFalse(unresolved.state.light)

    def test_workshop_is_the_actual_existing_scene_for_every_route(self):
        for actions in (['herbs', 'bargain'], ['lie', 'apologize', 'herbs', 'bargain'],
                        ['lie'] * 4 + ['wait'] * 5 + ['apologize', 'leave'], ['wait'] * 12):
            with self.subTest(actions=actions):
                old = Scene()
                game = play(['rope', 'timber', 'ready'])
                for action in actions:
                    expected = old.act(action)
                    self.assertEqual(game.act(action)['workshop_trace'], expected)
                self.assertEqual(game.workshop.state.snapshot(), old.state.snapshot())

    def test_night_ends_operation_instead_of_offering_impossible_routes(self):
        for turns in (9, 10, 11, 12):
            with self.subTest(turns=turns):
                actions = ['wait'] * (turns - 1) + ['leave'] if turns < 12 else ['wait'] * 12
                game = play(['rope', 'oil', 'ready'] + actions)
                self.assertEqual(game.state.ending, 'SHELTERED')
                self.assertEqual(game.state.time, 0)
                self.assertEqual(game.choices(), [])
                self.assertEqual(game.state.iven, 'sheltered')
                self.assertEqual(game.state.roof, 'sheltered')

    def test_rescue_at_exact_deadline_succeeds_later_one_is_unavailable(self):
        game = play(['timber', 'oil', 'ready', 'leave', 'ferry', 'iven', 'roof'])
        self.assertEqual((game.state.iven, game.state.roof, game.state.elapsed),
                         ('rescued', 'rescued', 6))
        missed = play(['timber', 'oil', 'ready', 'leave', 'ferry', 'hold', 'hold'])
        self.assertEqual(missed.state.iven, 'sheltered')
        self.assertNotIn('iven', [c.name for c in missed.choices()])
        self.assertIn('roof', [c.name for c in missed.choices()])
        missed.act('hold')
        self.assertEqual(missed.state.roof, 'sheltered')
        self.assertNotIn('roof', [c.name for c in missed.choices()])

    def test_current_telegraph_matches_each_stroke_and_hold_is_safe(self):
        game = play(['rope', 'timber', 'ready', 'leave', 'ferry', 'board'])
        row = next(c for c in game.choices() if c.name == 'row')
        self.assertIn('slack/pull', row.label)
        self.assertEqual(row.cost, 2)
        game.act('row')
        self.assertEqual(game.state.hull, 3)
        self.assertEqual(game.state.saved, 2)
        before = game.state.hull
        game.act('hold')
        self.assertEqual(game.state.hull, before)
        self.assertEqual(game.current(), 'slack')

    def test_guide_line_prevents_hull_and_medicine_damage(self):
        game = play(['rope', 'oil', 'ready', 'leave', 'ferry', 'secure', 'load', 'board'])
        self.assertEqual(game.current(), 'pull')
        self.assertIn('pull/surge', next(c.label for c in game.choices() if c.name == 'row'))
        game.act('row')
        self.assertEqual((game.state.hull, game.state.medicine, game.state.saved),
                         (4, 'delivered', 1))
        self.assertNotIn('rope', game.state.kit)
        self.assertNotIn('secure', [c.name for c in game.choices()])

    def test_boat_loss_ends_with_accurate_prior_arrivals(self):
        game = play(['rope', 'oil', 'ready', 'leave', 'ferry', 'board', 'row', 'row'])
        self.assertEqual((game.state.hull, game.state.saved, game.state.bank), (1, 2, 'mill'))
        game.act('load')
        # At beat 7 a solo crossing sees pull/surge and fails before arrival.
        result = game.act('row')
        self.assertEqual((game.state.ending, game.state.saved, game.state.medicine, game.state.hull),
                         ('BOAT_LOST', 2, 'spoiled', 0))
        self.assertIn('safety chains', result['text'])
        self.assertIn('2/4', game.epilogue())
        self.assertEqual(game.choices(), [])

    def test_reinforcement_buys_buoyancy_without_protecting_cargo(self):
        game = play(['timber', 'oil', 'ready', 'leave', 'ferry', 'reinforce', 'load', 'board'])
        self.assertEqual(game.state.hull, 7)
        game.act('row')
        self.assertEqual(game.state.hull, 4)
        self.assertEqual(game.state.medicine, 'spoiled')
        self.assertNotIn('reinforce', [c.name for c in game.choices()])

    def test_loading_capacity_unload_and_solo_trip(self):
        game = play(['rope', 'oil', 'ready', 'leave', 'ferry', 'load', 'board'])
        self.assertEqual((game.state.aboard, game.state.waiting, game.state.medicine), (1, 1, 'aboard'))
        self.assertNotIn('board', [c.name for c in game.choices()])
        game.act('unload')
        self.assertEqual((game.state.aboard, game.state.waiting, game.state.medicine), (0, 2, 'waiting'))
        self.assertEqual(game.state.elapsed, 3)
        game.act('board')
        self.assertEqual(game.state.aboard, 2)
        game.act('row')
        self.assertEqual((game.state.saved, game.state.aboard), (2, 0))
        self.assertNotIn('board', [c.name for c in game.choices()])

    def test_invalid_choices_are_atomic_and_sessions_restart_cleanly(self):
        first, other = Adventure(), Adventure()
        play(['rope', 'timber', 'ready', 'leave', 'ferry'], first)
        for action in ('span', 'causeway', 'unknown', 'apologize'):
            before = copy.deepcopy(first.snapshot())
            count = len(first.history)
            with self.assertRaises(ValueError):
                first.act(action)
            self.assertEqual(first.snapshot(), before)
            self.assertEqual(len(first.history), count)
        self.assertEqual(other.snapshot(), Adventure().snapshot())
        first.restart()
        self.assertEqual(first.snapshot(), other.snapshot())
        self.assertEqual(first.history, [])

    def test_full_kit_requires_two_distinct_items_and_allows_repacking(self):
        game = Adventure()
        game.act('rope')
        self.assertNotIn('ready', [c.name for c in game.choices()])
        game.act('timber')
        with self.assertRaises(ValueError):
            game.act('oil')
        game.act('rope')
        game.act('oil')
        self.assertEqual(game.state.kit, {'timber', 'oil'})
        game.act('ready')
        self.assertEqual(game.workshop.state.turn, 0)

    def test_every_advertised_river_choice_preserves_population_and_clock(self):
        # Explore actual successor states from representative loadouts and workshop histories.
        seen, frontier = set(), []
        for kit in (['rope', 'timber'], ['rope', 'oil'], ['timber', 'oil']):
            for dialogue in (['leave'], ['herbs', 'bargain'], ['wait', 'leave'],
                             ['lie', 'apologize', 'herbs', 'bargain']):
                frontier.append(play(kit + ['ready'] + dialogue))
        endings = set()
        while frontier:
            game = frontier.pop()
            key = json.dumps(game.snapshot(), sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            s = game.state
            self.assertEqual(s.time + s.elapsed, 9)
            self.assertGreaterEqual(s.time, 0)
            self.assertGreaterEqual(s.hull, 0)
            population = s.waiting + s.aboard + s.saved + (2 if s.roof != 'rescued' else 0)
            self.assertEqual(population, 4)
            self.assertLessEqual(s.aboard + (s.medicine == 'aboard'), 3 if s.iven == 'rescued' else 2)
            if s.ending:
                endings.add(s.ending)
                self.assertEqual(game.choices(), [])
                continue
            for choice in game.choices():
                successor = copy.deepcopy(game)
                successor.history = []
                result = successor.act(choice.name)
                self.assertEqual(result['cost'], choice.cost)
                self.assertEqual(successor.state.time, s.time - choice.cost)
                if not choice.cost:
                    self.assertEqual(successor.state.elapsed, s.elapsed)
                frontier.append(successor)
        self.assertEqual(endings, {'FULL_RESCUE', 'PEOPLE_SAFE', 'PARTIAL_CROSSING', 'SHELTERED', 'BOAT_LOST'})
        self.assertGreater(len(seen), 1000)
        print(f'Adventure graph: {len(seen)} states from 12 actual river-entry configurations; five endings.')

    def test_cli_full_operation_trace_diagnostics_and_restart(self):
        commands = ['status', 'look', 'not-a-choice', '9' * 5000, *BRIDGE, 'status', 'restart', 'status', 'quit']
        run = subprocess.run([sys.executable, str(HERE / 'adventure.py'), '--trace'],
                             input='\n'.join(commands) + '\n', text=True, capture_output=True,
                             cwd='/tmp', timeout=10)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('Ending: FULL_RESCUE', run.stdout)
        self.assertIn('Adventure restarted', run.stdout)
        traces = [json.loads(line.split('TRACE ', 1)[1]) for line in run.stdout.splitlines() if 'TRACE ' in line]
        self.assertEqual([t['action'] for t in traces], BRIDGE)
        self.assertEqual(traces[-1]['after']['expedition']['saved'], 4)
        self.assertEqual(traces[-1]['after']['expedition']['elapsed'], 9)
        self.assertIn('"phase": "pack"', run.stdout)

    def test_cli_numbers_eof_version_and_late_departure(self):
        numeric = subprocess.run([sys.executable, str(HERE / 'adventure.py'), '--trace'],
                                 input='1\n2\n3\nstatus\n', capture_output=True, text=True, timeout=10)
        self.assertEqual(numeric.returncode, 0, numeric.stderr)
        self.assertIn('Session closed', numeric.stdout)
        self.assertIn('"phase": "workshop"', numeric.stdout)
        version = subprocess.run([sys.executable, str(HERE / 'adventure.py'), '--version'],
                                 capture_output=True, text=True, timeout=10)
        self.assertEqual(version.stdout.strip(), VERSION)
        late = subprocess.run([sys.executable, str(HERE / 'adventure.py')],
                              input='rope\noil\nready\n' + 'wait\n' * 12 + 'quit\n',
                              capture_output=True, text=True, timeout=10)
        self.assertEqual(late.returncode, 0, late.stderr)
        self.assertIn('Ending: SHELTERED', late.stdout)
        self.assertNotIn('You cross before dusk', late.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
