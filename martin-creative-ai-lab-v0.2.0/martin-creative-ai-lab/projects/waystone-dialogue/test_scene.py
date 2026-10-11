#!/usr/bin/env python3
"""Behavior, real CLI and preserved-source checks for the bounded scene."""

import csv
import hashlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from zipfile import ZipFile

from scene import MAX_TURNS, OUTBURST_COOLDOWN, Scene, State, VARIANTS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


class SceneTests(unittest.TestCase):
    def test_crossing_requires_help_before_agreement(self):
        scene = Scene()
        first = scene.act("bargain")
        self.assertIsNone(scene.state.ending)
        self.assertIn("basket", first["text"])
        scene.act("herbs")
        self.assertEqual(scene.state.mood, "OBSESSED")
        self.assertEqual(scene.state.stress, 14)
        scene.act("bargain")
        self.assertEqual(scene.state.ending, "COOPERATED")
        self.assertIn("EVT_PLAYER_HELPED", scene.state.events)

    def test_repeated_false_orders_have_visible_consequences(self):
        scene = Scene()
        turns = [scene.act("lie") for _ in range(4)]
        self.assertEqual([r["after"]["stress"] for r in turns], [42, 64, 86, 81])
        self.assertEqual([r["after"]["mood"] for r in turns],
                         ["PRESSURIZED"] * 3 + ["OUTBURST"])
        self.assertEqual(scene.state.trust, 33)
        self.assertEqual(scene.state.respect, 49)
        self.assertEqual(scene.state.cooldown, 5)
        self.assertTrue(scene.state.apology_due)
        self.assertEqual(scene.state.flags, {"FLAG_PLAYER_LIED", "FLAG_OUTBURST_RECENT"})
        self.assertIn("EVT_NPC_OUTBURST", scene.state.events)
        self.assertTrue(turns[-1]["variant_id"].endswith("OUTBURST_001"))

    def test_negotiation_trust_boundary(self):
        for trust, variant, mood, stress, ending in [
            (39, "002", "WARY", 24, None),
            (40, "001", "NEUTRAL", 20, "COOPERATED"),
        ]:
            with self.subTest(trust=trust):
                scene = Scene()
                scene.state.trust = trust
                scene.state.herbs_sorted = True
                turn = scene.act("bargain")
                self.assertTrue(turn["variant_id"].endswith(variant))
                self.assertEqual((scene.state.mood, scene.state.stress, scene.state.ending),
                                 (mood, stress, ending))

    def test_catalog_stress_boundary_is_checked_before_effects(self):
        for stress, mood, after in [(79, "PRESSURIZED", 100), (80, "OUTBURST", 75)]:
            with self.subTest(stress=stress):
                scene = Scene()
                scene.state.stress = stress
                scene.act("lie")
                self.assertEqual((scene.state.mood, scene.state.stress), (mood, after))

    def test_apology_requires_an_unresolved_fault_and_cannot_be_repeated(self):
        scene = Scene()
        self.assertNotIn("apologize", scene.available_actions())
        scene.act("lie")
        scene.act("apologize")
        self.assertEqual((scene.state.stress, scene.state.trust, scene.state.mood),
                         (30, 51, "NEUTRAL"))
        self.assertFalse(scene.state.apology_due)
        self.assertIn("FLAG_PLAYER_LIED", scene.state.flags)
        self.assertIn("EVT_PLAYER_PRAISED", scene.state.events)
        before = scene.state.snapshot()
        with self.assertRaises(ValueError):
            scene.act("apologize")
        self.assertEqual(scene.state.snapshot(), before)

    def test_herbs_cannot_be_spent_twice(self):
        scene = Scene()
        scene.act("herbs")
        before = scene.state.snapshot()
        with self.assertRaises(ValueError):
            scene.act("herbs")
        self.assertEqual(scene.state.snapshot(), before)
        self.assertEqual(len(scene.history), 1)

    def test_cooldown_blocks_repair_and_apology_until_five_waits(self):
        scene = Scene()
        for _ in range(4):
            scene.act("lie")
        self.assertEqual(scene.available_actions(), ["wait", "leave"])
        for remaining in [4, 3, 2, 1, 0]:
            for action in ["herbs", "apologize", "lie", "bargain", "ask", "unknown"]:
                before = scene.state.snapshot()
                with self.assertRaises(ValueError):
                    scene.act(action)
                self.assertEqual(scene.state.snapshot(), before)
            scene.act("wait")
            self.assertEqual(scene.state.cooldown, remaining)
            self.assertEqual(scene.state.mood, "OUTBURST" if remaining else "WARY")
        self.assertEqual(scene.state.turn, 9)
        scene.act("apologize")
        self.assertEqual(scene.state.trust, 39)
        self.assertEqual(scene.state.stress, 69)
        scene.act("herbs")
        scene.act("bargain")
        self.assertEqual(scene.state.mood, "WARY")
        self.assertEqual(scene.state.ending, "DUSK")

    def test_numeric_effects_clamp_at_both_bounds(self):
        scene = Scene()
        scene.state.stress = 5
        scene.state.trust = 99
        scene.state.apology_due = True
        scene.act("apologize")
        self.assertEqual((scene.state.stress, scene.state.trust), (0, 100))
        scene.state.stress = 80
        scene.state.trust = 1
        scene.state.respect = 1
        scene.act("lie")
        self.assertEqual((scene.state.trust, scene.state.respect), (0, 0))
        other = Scene()
        other.state.trust = 39
        other.state.stress = 99
        other.act("bargain")
        self.assertEqual(other.state.stress, 100)

    def test_leaving_calm_or_in_outburst_selects_distinct_endings(self):
        for angry, ending, mood in [(False, "LEFT", "NEUTRAL"), (True, "DISMISSED", "AVOIDANT")]:
            with self.subTest(angry=angry):
                scene = Scene()
                if angry:
                    for _ in range(4):
                        scene.act("lie")
                scene.act("leave")
                self.assertEqual((scene.state.ending, scene.state.mood), (ending, mood))
                if angry:
                    self.assertIn("EVT_NPC0007_LEAVE_SCENE", scene.state.events)
                before = scene.state.snapshot()
                with self.assertRaises(ValueError):
                    scene.act("wait")
                self.assertEqual(scene.state.snapshot(), before)
                self.assertEqual(scene.available_actions(), [])

    def test_dusk_is_terminal_and_last_turn_can_still_succeed_or_leave(self):
        scene = Scene()
        for _ in range(MAX_TURNS):
            scene.act("wait")
        self.assertEqual(scene.state.ending, "DUSK")
        with self.assertRaises(ValueError):
            scene.act("herbs")
        for action, ending in [("bargain", "COOPERATED"), ("leave", "LEFT")]:
            scene = Scene()
            scene.act("herbs")
            for _ in range(MAX_TURNS - 2):
                scene.act("wait")
            scene.act(action)
            self.assertEqual((scene.state.turn, scene.state.ending), (MAX_TURNS, ending))

    def test_restart_removes_memory_clock_cooldown_ending_and_trace(self):
        scene = Scene()
        for _ in range(4):
            scene.act("lie")
        scene.act("leave")
        scene.restart()
        self.assertEqual(scene.state.snapshot(), State().snapshot())
        self.assertEqual(scene.history, [])
        scene.act("herbs")
        scene.act("bargain")
        self.assertEqual(scene.state.ending, "COOPERATED")

    def test_sessions_and_trace_snapshots_do_not_share_memory(self):
        first, second = Scene(), Scene()
        turn = first.act("lie")
        preserved = json.dumps(turn, sort_keys=True)
        first.act("apologize")
        self.assertEqual(json.dumps(turn, sort_keys=True), preserved)
        self.assertEqual(second.state.snapshot(), State().snapshot())
        self.assertEqual(turn["before"]["flags"], [])
        self.assertEqual(turn["after"]["flags"], ["FLAG_PLAYER_LIED"])
        first.restart()
        self.assertEqual(json.dumps(turn, sort_keys=True), preserved)

    def test_same_choices_replay_identical_decisions(self):
        runs = []
        for _ in range(2):
            scene = Scene()
            runs.append([scene.act(a) for a in ["ask", "lie", "apologize", "herbs", "bargain"]])
        self.assertEqual(runs[0], runs[1])

    def test_selected_records_match_verified_preserved_sources(self):
        provenance = json.loads((HERE / "provenance.json").read_text())
        registry = json.loads((ROOT / "registry/legacy_sources.json").read_text())
        source = next(s for s in registry["sources"] if s["id"] == provenance["source_id"])
        self.assertEqual(source["commit"], provenance["commit"])
        self.assertEqual(source["repository"], provenance["repository"])
        self.assertEqual(source["archive_prefix"], provenance["archive_prefix"])
        self.assertEqual(registry["source_archive"], provenance["archive"])
        archive = ROOT / provenance["archive"]["path"]
        self.assertEqual(hashlib.sha256(archive.read_bytes()).hexdigest(), provenance["archive"]["sha256"])
        texts = {}
        with ZipFile(archive) as z:
            for item in provenance["files"]:
                inventory = next(i for i in source["inventory"] if i["path"] == item["path"])
                self.assertEqual(inventory["sha256"], item["sha256"])
                data = z.read(provenance["archive_prefix"] + "/" + item["path"])
                self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"])
                texts[Path(item["path"]).name] = data.decode("utf-8-sig")
        rows = {r["VariantID"]: r for r in csv.DictReader(io.StringIO(texts["DIALOGUE_VARIANTS.csv"]))}
        self.assertEqual(len({v.source_id for v in VARIANTS}), 9)
        for variant in VARIANTS:
            row = rows[variant.source_id]
            self.assertEqual((row["ScopeType"], row["ScopeID"]), ("NPC", provenance["npc_id"]))
            self.assertEqual(int(row["BaseScore"]), 0)
            self.assertEqual(int(row["Priority"]), variant.priority)
            for column, value in [("DeltaStress", variant.stress), ("DeltaTrust_Player", variant.trust),
                                  ("DeltaRespect_Player", variant.respect)]:
                self.assertEqual(int(row[column] or 0), value)
            self.assertEqual(row["SetMood"], variant.mood)
            self.assertEqual(tuple(filter(None, row["AddFlags"].split("|"))), variant.flags)
            self.assertEqual(tuple(filter(None, row["AddRecentEvent"].split("|"))), variant.events)
        state = next(r for r in csv.DictReader(io.StringIO(texts["NPC_STATE.csv"])) if r["IdNPC"] == provenance["npc_id"])
        relations = next(r for r in csv.DictReader(io.StringIO(texts["NPC_RELATIONS.csv"]))
                         if r["SourceIdNPC"] == provenance["npc_id"] and r["TargetType"] == "PLAYER")
        profile = next(r for r in csv.DictReader(io.StringIO(texts["NPC_PROFILE.csv"])) if r["IdNPC"] == provenance["npc_id"])
        self.assertEqual(State().stress, int(state["Stress_0_100"]))
        self.assertEqual(State().mood, state["Mood"])
        self.assertEqual(State().trust, int(relations["Trust_0_100"]))
        self.assertEqual(State().respect, int(relations["Respect_0_100"]))
        self.assertEqual(OUTBURST_COOLDOWN, int(profile["OutburstCooldownTurns"]))


class CliTests(unittest.TestCase):
    def run_cli(self, inputs, *args):
        result = subprocess.run([sys.executable, str(HERE / "scene.py"), *args],
                                input=inputs, text=True, capture_output=True, cwd="/tmp", timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        return result.stdout

    def traces(self, output):
        return [json.loads(line[6:]) for line in output.splitlines() if line.startswith("TRACE ")]

    def test_number_choices_play_to_completion_without_trace(self):
        output = self.run_cli("2\n2\nstatus\nwait\nquit\n")
        self.assertIn("Ending: COOPERATED", output)
        self.assertEqual(output.count("Ending: COOPERATED"), 1)
        self.assertIn("The scene has ended", output)
        self.assertIn("path shines through the fog", output)
        self.assertNotIn("TRACE ", output)
        self.assertNotIn('"variant_id"', output)

    def test_named_choices_trace_conflict_and_restart(self):
        output = self.run_cli("lie\nlie\nlie\nlie\nleave\nrestart\nherbs\nbargain\nquit\n", "--trace")
        self.assertIn("Ending: DISMISSED", output)
        self.assertIn("Ending: COOPERATED", output)
        trace = self.traces(output)
        self.assertEqual(len(trace), 7)
        self.assertEqual(trace[5]["before"], State().snapshot())
        self.assertEqual(trace[4]["after"]["ending"], "DISMISSED")

    def test_bad_input_and_status_consume_no_turn(self):
        output = self.run_cli("status\n0\n999\n" + "9" * 5000 + "\n\u00b2\napologize\nunknown\nherbs\nbargain\nquit\n", "--trace")
        trace = self.traces(output)
        self.assertEqual(len(trace), 2)
        self.assertEqual(trace[0]["before"], State().snapshot())
        self.assertEqual(trace[1]["after"]["turn"], 2)
        self.assertIn("Ending: COOPERATED", output)

    def test_eof_during_live_and_terminal_scene_exits_cleanly(self):
        for inputs in ["", "herbs\nbargain\n"]:
            with self.subTest(inputs=inputs):
                self.assertIn("Session closed. No progress is saved.", self.run_cli(inputs))

    def test_all_waits_reach_dusk_in_real_cli(self):
        output = self.run_cli("wait\n" * MAX_TURNS + "quit\n", "--trace")
        self.assertIn("Ending: DUSK", output)
        self.assertEqual(len(self.traces(output)), MAX_TURNS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
