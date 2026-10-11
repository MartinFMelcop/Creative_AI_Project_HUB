#!/usr/bin/env python3
"""A deterministic, in-memory dialogue scene; Python standard library only."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from typing import Callable

VERSION = "0.1.1"
MAX_TURNS = 12
OUTBURST_COOLDOWN = 5
INTRO = (
    "The Last Waystone\n"
    "Fog is swallowing the road. The Keeper can repair the village Waystone,\n"
    "but a basket of swamp herbs has absorbed all their attention. You need\n"
    "a safe route before dusk. Help with the herbs, then make your case.\n"
    "A false order from the council might get attention. It might also cost it."
)
ENDINGS = {
    "COOPERATED": "The Keeper fits the last rune. A path shines through the fog.\n"
                  "'Next time, lead with the herbs.' You cross before dusk.",
    "LEFT": "You leave the Keeper to the herbs and follow the lanterns toward the ferry.\n"
            "The Waystone stays dark; another route will have to do.",
    "DISMISSED": "The workshop door closes. The Waystone will stay dark tonight.\n"
                 "You turn back toward the village, carrying no shortcut.",
    "DUSK": "The last light fades before an agreement is made.\n"
            "You find shelter in the village. The crossing must wait until morning.",
}
ACTIONS = {
    "ask": "Ask for the repair without offering help.",
    "herbs": "Sort the swamp herbs and ask about the missing rune.",
    "bargain": "Explain why the village needs the crossing.",
    "lie": "Claim the council has ordered an immediate repair.",
    "apologize": "Admit your false order and apologize.",
    "wait": "Give the Keeper a quiet moment.",
    "leave": "End the conversation and take another route.",
}


@dataclass
class State:
    stress: int = 20
    trust: int = 45
    respect: int = 55
    mood: str = "NEUTRAL"
    cooldown: int = 0
    turn: int = 0
    herbs_sorted: bool = False
    apology_due: bool = False
    apology_trust_ceiling: int | None = None
    flags: set[str] = field(default_factory=set)
    events: set[str] = field(default_factory=set)
    ending: str | None = None

    def snapshot(self) -> dict:
        return {
            "stress": self.stress, "trust": self.trust, "respect": self.respect,
            "mood": self.mood, "cooldown": self.cooldown, "turn": self.turn,
            "herbs_sorted": self.herbs_sorted, "apology_due": self.apology_due,
            "apology_trust_ceiling": self.apology_trust_ceiling,
            "flags": sorted(self.flags), "events": sorted(self.events),
            "ending": self.ending,
        }


@dataclass(frozen=True)
class Variant:
    source_id: str
    action: str
    priority: int
    gate: Callable[[State], bool]
    text: str
    stress: int = 0
    trust: int = 0
    respect: int = 0
    mood: str = "NEUTRAL"
    flags: tuple[str, ...] = ()
    events: tuple[str, ...] = ()


def calm(state: State) -> bool:
    return state.mood != "OUTBURST"


# Closed Python predicates replace the legacy expression evaluator. These nine
# priority/delta/flag/event records are traceable in provenance.json. Wording is
# an English adaptation, not a claim to preserve the original scene or canon.
VARIANTS = (
    Variant("DV_NPC0007_REQUEST_HELP_001", "herbs", 60, calm,
            "Now that I can see my desk, yes. Give me the rune. And don't interrupt.",
            stress=-6, mood="OBSESSED", events=("EVT_PLAYER_HELPED",)),
    Variant("DV_NPC0007_REQUEST_HELP_002", "ask", 55, calm,
            "That sounds like work. You start. I'll correct it later.", respect=-1),
    Variant("DV_NPC0007_NEGOTIATION_001", "bargain", 55,
            lambda s: calm(s) and s.trust >= 40,
            "All right. Make your case. If it makes sense, I'm listening."),
    Variant("DV_NPC0007_NEGOTIATION_002", "bargain", 55,
            lambda s: calm(s) and s.trust < 40,
            "What are you trying to sell me, exactly?", stress=4, mood="WARY",
            events=("EVT_MANIPULATION_SUSPECTED",)),
    Variant("DV_NPC0007_MANIP_CONF_WARN_001", "lie", 70,
            lambda s: calm(s) and s.stress < 80,
            "I saw the trick. Stop now, or this conversation is over.",
            stress=22, mood="PRESSURIZED", flags=("FLAG_PLAYER_LIED",),
            events=("EVT_PLAYER_LIED",)),
    Variant("DV_NPC0007_MANIP_CONF_OUTBURST_001", "lie", 95,
            lambda s: calm(s) and s.stress >= 80,
            "Enough. I saw it. You're trying to bend me with words. I am not a fool.",
            stress=-5, trust=-12, respect=-6, mood="OUTBURST",
            flags=("FLAG_PLAYER_LIED", "FLAG_OUTBURST_RECENT"),
            events=("EVT_PLAYER_LIED", "EVT_NPC_OUTBURST")),
    Variant("DV_NPC0007_APOLOGY_001", "apologize", 55, calm,
            "All right. It happens. Correct it, and we move on.",
            stress=-12, trust=6, events=("EVT_PLAYER_PRAISED",)),
    Variant("DV_NPC0007_GOODBYE_001", "leave", 55,
            lambda s: calm(s) and "FLAG_NPC0007_AVOID_PLAYER_TEMP" not in s.flags,
            "Go on. And don't make more work for me."),
    Variant("DV_NPC0007_GOODBYE_002", "leave", 90,
            lambda s: not calm(s) or "FLAG_NPC0007_AVOID_PLAYER_TEMP" in s.flags,
            "I'm done. Get out of my sight.", stress=-10, mood="AVOIDANT",
            flags=("FLAG_NPC0007_AVOID_PLAYER_TEMP",),
            events=("EVT_NPC0007_LEAVE_SCENE",)),
)

# This response belongs to the new scene, not the preserved NPC catalog. Its
# higher priority keeps an unresolved lie from selecting an agreement response.
SCENE_VARIANTS = (
    Variant("SCENE_BARGAIN_UNRESOLVED_LIE", "bargain", 100,
            lambda s: calm(s) and s.apology_due,
            "First, correct the false order. I won't agree while you're hiding behind the council.",
            mood="WARY"),
)


class Scene:
    def __init__(self):
        self.state = State()
        self.history: list[dict] = []

    def restart(self) -> None:
        self.state = State()
        self.history = []

    def available_actions(self) -> list[str]:
        if self.state.ending:
            return []
        if not calm(self.state):
            return ["wait", "leave"]
        return [action for action in ACTIONS
                if not (action == "herbs" and self.state.herbs_sorted)
                and not (action == "apologize" and not self.state.apology_due)]

    def act(self, action: str) -> dict:
        s = self.state
        if s.ending:
            raise ValueError("The scene has ended. Restart to play again.")
        if action not in self.available_actions():
            raise ValueError("That choice is unavailable. Use a listed choice.")
        if action == "apologize" and s.apology_trust_ceiling is None:
            raise RuntimeError("An unresolved lie must retain its earlier trust level.")

        # Reject unavailable input before advancing any memory, clock or cooldown.
        before = s.snapshot()
        candidates = [v for v in VARIANTS + SCENE_VARIANTS
                      if v.action == action and v.gate(s)]
        variant = (max(candidates, key=lambda v: (v.priority, v.source_id))
                   if candidates else None)
        if action != "wait" and variant is None:
            raise RuntimeError(f"No response for an available action: {action}")

        if variant:
            s.stress = max(0, min(100, s.stress + variant.stress))
            s.trust = max(0, min(100, s.trust + variant.trust))
            s.respect = max(0, min(100, s.respect + variant.respect))
            s.mood = variant.mood
            s.flags.update(variant.flags)
            s.events.update(variant.events)
            text = variant.text
        else:
            text = "The Keeper measures a pinch of herbs. You let the silence stand."

        if action == "herbs":
            s.herbs_sorted = True
        elif action == "lie":
            if not before["apology_due"]:
                s.apology_trust_ceiling = before["trust"]
            s.apology_due = True
        elif action == "apologize":
            s.trust = min(s.trust, before["apology_trust_ceiling"])
            s.apology_due = False
            s.apology_trust_ceiling = None

        if s.mood == "OUTBURST" and before["mood"] != "OUTBURST":
            s.cooldown = OUTBURST_COOLDOWN
        elif before["cooldown"] > 0:
            s.cooldown = before["cooldown"] - 1
            if s.cooldown == 0 and s.mood == "OUTBURST":
                s.mood = "WARY"
                text += "\nTheir breathing steadies. They are ready to listen again."

        s.turn += 1
        if (action == "bargain" and s.herbs_sorted and before["trust"] >= 40
                and not s.apology_due):
            s.ending = "COOPERATED"
        elif action == "leave":
            s.ending = "DISMISSED" if s.mood == "AVOIDANT" else "LEFT"
        elif s.turn >= MAX_TURNS:
            s.ending = "DUSK"
        elif (action == "bargain" and before["trust"] >= 40
              and not s.herbs_sorted and not s.apology_due):
            text += "\n'But first, this basket. I can't work under a heap of herbs.'"

        result = {
            "action": action,
            "variant_id": variant.source_id if variant else "SCENE_WAIT",
            "variant_origin": "legacy-adaptation" if variant in VARIANTS else "scene",
            "eligible_variants": sorted(v.source_id for v in candidates),
            "text": text, "before": before, "after": s.snapshot(),
        }
        self.history.append(result)
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Play The Last Waystone.")
    parser.add_argument("--trace", action="store_true",
                        help="Print a JSON decision/state trace after each turn.")
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args()
    scene = Scene()
    announced_ending = None
    print(INTRO)
    print("\nChoose a number or its name. Commands: status, restart, quit.")
    try:
        while True:
            s = scene.state
            if s.ending:
                if s.ending != announced_ending:
                    print(f"\nEnding: {s.ending}\n{ENDINGS[s.ending]}")
                    print("Commands: restart, status, quit.")
                    announced_ending = s.ending
                options = []
            else:
                print(f"\nDusk in {MAX_TURNS - s.turn} turns. The Keeper is {s.mood.lower()}.")
                options = scene.available_actions()
                for number, action in enumerate(options, 1):
                    print(f"{number}. {action}: {ACTIONS[action]}")
            try:
                choice = input("> ").strip().lower()
            except EOFError:
                print("\nSession closed. No progress is saved.")
                return 0
            if choice == "quit":
                return 0
            if choice == "restart":
                scene.restart()
                announced_ending = None
                print("\nScene restarted.\n" + INTRO)
                continue
            if choice == "status":
                print(json.dumps(scene.state.snapshot(), sort_keys=True))
                continue
            if choice.isascii() and choice.isdigit():
                # Bound the token before integer conversion (also handles huge input).
                choice = (options[int(choice) - 1]
                          if len(choice) == 1 and 1 <= int(choice) <= len(options) else "")
            try:
                result = scene.act(choice)
            except ValueError as exc:
                print(str(exc))
                continue
            print(f"\nKeeper: {result['text']}")
            if args.trace:
                print("TRACE " + json.dumps(result, sort_keys=True))
    except KeyboardInterrupt:
        print("\nSession closed. No progress is saved.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
