#!/usr/bin/env python3
"""A complete deterministic rescue adventure built around the preserved scene."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field

from scene import ACTIONS, INTRO as WORKSHOP_INTRO, Scene

VERSION = "0.2.0"
RIVER_WINDOW = 9
ROOF_DEADLINE = 6
IVEN_DEADLINE = 5
CURRENTS = ("slack", "pull", "surge")
INTRO = """The Last Waystone — Flood Crossing
Mara's cart has stopped outside the workshop. Two mill workers are on its roof;
two more wait with the clinic's medicine below. The flood will cut off the mill.
Iven's ferry is pinned against the jetty. A repaired Waystone could light the
old causeway, but it cannot replace the missing boards.

Mara: 'Four people. One medicine chest. Iven if we can reach him. Don't tell me
we'll get everything out unless you've looked at what we can carry.'

You have two equipment slots. Rope speeds one rescue OR secures the ferry OR
makes a temporary crossing. Timber repairs the causeway OR reinforces the boat.
Oil signals the roof workers when there is no Waystone light. Nothing is random.
You have 9 beats in total, including workshop choices and travel. The roof
workers leave at beat 6; Iven abandons the jetty at beat 5. Reach the river early."""


@dataclass(frozen=True)
class Choice:
    name: str
    label: str
    cost: int = 0


@dataclass
class Expedition:
    phase: str = "pack"
    kit: set[str] = field(default_factory=set)
    time: int = RIVER_WINDOW
    elapsed: int = 0
    route: str | None = None
    light: bool = False
    roof: str = "waiting"
    iven: str = "waiting"
    waiting: int = 2
    saved: int = 0
    medicine: str = "waiting"
    bridge: str | None = None
    hull: int = 4
    line: bool = False
    bank: str = "mill"
    aboard: int = 0
    ending: str | None = None

    def snapshot(self) -> dict:
        return {**vars(self), "kit": sorted(self.kit)}


class Adventure:
    def __init__(self):
        self.state = Expedition()
        self.workshop = Scene()
        self.history: list[dict] = []

    def restart(self) -> None:
        self.__init__()

    def snapshot(self) -> dict:
        return {"version": VERSION, "expedition": self.state.snapshot(),
                "workshop": self.workshop.state.snapshot()}

    def current(self, offset: int = 0) -> str:
        return CURRENTS[(self.state.elapsed + offset) % len(CURRENTS)]

    def rescue_cost(self, who: str) -> int:
        s = self.state
        if "rope" in s.kit or (who == "roof" and (s.light or "oil" in s.kit)):
            return 1
        return 2

    def choices(self) -> list[Choice]:
        s = self.state
        if s.ending:
            return []
        if s.phase == "pack":
            options = [Choice(name, f"{'Unpack' if name in s.kit else 'Pack'} {name}.")
                       for name in ("rope", "timber", "oil")
                       if name in s.kit or len(s.kit) < 2]
            if len(s.kit) == 2:
                options.append(Choice("ready", "Take this equipment to the workshop."))
            return options
        if s.phase == "workshop":
            return [Choice(a, ACTIONS[a] + " [1 flood-window beat]", 1)
                    for a in self.workshop.available_actions()]
        if s.phase == "route":
            options = [Choice("ferry", "Follow the lower track to the ferry. [2 beats]", 2)]
            if s.light:
                options.insert(0, Choice("causeway", "Follow the Waystone light to the mill yard. [1 beat]", 1))
            options.append(Choice("retreat", "Return to high ground; abandon tonight's crossing."))
            return [c for c in options if c.cost <= s.time]

        options = []
        at_mill = s.phase == "causeway" or s.bank == "mill"
        if at_mill:
            for who, deadline, label in (("roof", ROOF_DEADLINE, "Bring Lio and Senn down from the roof"),
                                         ("iven", IVEN_DEADLINE, "Free Iven from the pinned jetty")):
                cost = self.rescue_cost(who)
                if getattr(s, who) == "waiting" and s.elapsed + cost <= deadline:
                    if who == "roof" and s.light:
                        method = "Waystone signal"
                    elif who == "roof" and "oil" in s.kit:
                        method = "burn oil as a signal; consume oil"
                    elif "rope" in s.kit:
                        method = "consume rope"
                    else:
                        method = "work by hand"
                    options.append(Choice(who, f"{label}. [{cost} beat(s); {method}; deadline {deadline}]", cost))
                    if who == "iven" and "rope" in s.kit and s.elapsed + 2 <= deadline:
                        options.append(Choice("iven_hands", "Free Iven by hand; keep the rope for the crossing. [2 beats; deadline 5]", 2))

        if s.phase == "causeway":
            if not s.bridge:
                if "timber" in s.kit:
                    options.append(Choice("span", "Replace the missing boards. [2 beats; consume timber; permanent crossing]", 2))
                if "rope" in s.kit:
                    options.append(Choice("lash", "Rig a temporary footline. [1 beat; consume rope; slow evacuation]", 1))
                options.append(Choice("wade", "Mark a shallow footpath. [1 beat; slow evacuation; medicine cannot follow]", 1))
            else:
                cost = 1 if s.bridge == "stable" or s.iven == "rescued" else 2
                if s.waiting:
                    options.append(Choice("lead", f"Lead all {s.waiting} waiting villagers across. [{cost} beat(s); people only]", cost))
                    if s.bridge == "stable" and s.medicine == "waiting":
                        options.append(Choice("convoy", "Move the people and medicine cart together. [2 beats]", 2))
                if s.bridge != "waded" and s.medicine == "waiting":
                    options.append(Choice("medicine", "Carry the medicine chest across separately. [1 beat]", 1))
        else:
            capacity = 3 if s.iven == "rescued" else 2
            occupied = s.aboard + (s.medicine == "aboard")
            if s.bank == "mill":
                if s.waiting and occupied < capacity:
                    count = min(s.waiting, capacity - occupied)
                    options.append(Choice("board", f"Board {count} villager(s). [no time; {capacity} cargo slots total]"))
                if s.medicine == "waiting" and occupied < capacity:
                    options.append(Choice("load", "Load medicine in one cargo slot. [no time; unprotected surge spoils it]"))
                if occupied:
                    options.append(Choice("unload", "Put this load back on the mill bank. [no time]"))
            if "rope" in s.kit and not s.line:
                options.append(Choice("secure", "Rig a guide line across the channel. [1 beat; consume rope; prevents current damage]", 1))
            if "timber" in s.kit:
                options.append(Choice("reinforce", "Add timber buoyancy to the ferry. [1 beat; consume timber; hull +3; medicine still vulnerable]", 1))
            cost = 1 if s.iven == "rescued" else 2
            if occupied or s.bank == "road":
                forecast = "/".join(self.current(i) for i in range(cost))
                options.append(Choice("row", f"Row to the {'road' if s.bank == 'mill' else 'mill'} bank. [{cost} beat(s); current {forecast}]", cost))
            options.append(Choice("hold", "Stay tied to the jetty; let the current change. [1 beat; no hull damage]", 1))

        options.append(Choice("finish", "End the operation; take the delivered people/cargo to shelter."))
        return [c for c in options if c.cost <= s.time]

    def describe(self) -> str:
        s = self.state
        if s.ending:
            return self.epilogue()
        if s.phase == "pack":
            return "Preparation: choose two different items, then ready.\nPacked: " + (", ".join(sorted(s.kit)) or "nothing")
        if s.phase == "workshop":
            return (f"Workshop: {self.workshop.state.turn} choices spent; "
                    f"{max(0, RIVER_WINDOW - self.workshop.state.turn)} flood-window beats remain.\n"
                    "You may leave for the ferry; the causeway needs the Keeper's repair.")
        if s.phase == "route":
            return (f"Mara tightens the chest's straps. You have {s.time} beats before the landing floods.\n"
                    "The roof workers leave for the north loft at beat 6; Iven abandons\n"
                    "his jetty at beat 5. A rescue completed on its deadline still succeeds.\n"
                    + ("The Waystone burns. Its light reaches the causeway and can signal the roof."
                       if s.light else "The Waystone is dark. Only the ferry track is usable."))
        overview = (f"River beat {s.elapsed}; {s.time} remaining. Roof: {s.roof}; Iven: {s.iven}.\n"
                    f"At the mill: {s.waiting}; delivered: {s.saved}/4; medicine: {s.medicine}.\n"
                    f"Equipment: {', '.join(sorted(s.kit)) or 'none'}. ")
        if s.phase == "causeway":
            return overview + f"Crossing: {s.bridge or 'missing boards'}."
        return overview + (f"Ferry at {s.bank}; hull {s.hull}; aboard {s.aboard}; "
                           f"guide line {'rigged' if s.line else 'absent'}.\n"
                           f"Current now: {self.current()}; next: {self.current(1)}. "
                           "Unprotected pull costs 1 hull; surge costs 2 and spoils aboard medicine.\n"
                           "Iven can steer in 1 beat with 3 slots; alone you need 2 beats with 2 slots.")

    def _spend(self, cost: int) -> list[str]:
        s = self.state
        s.time -= cost
        s.elapsed += cost
        notices = []
        if s.roof == "waiting" and s.elapsed >= ROOF_DEADLINE:
            s.roof = "sheltered"
            notices.append("Lio waves once from the roof. He and Senn climb toward the north loft.\n"
                           "They are above the flood, but the road party cannot reach them tonight.")
        if s.iven == "waiting" and s.elapsed >= IVEN_DEADLINE:
            s.iven = "sheltered"
            notices.append("The jetty tears loose. Iven scrambles onto the north shoal.\n"
                           "His boat remains here; he can no longer help steer it tonight.")
        return notices

    def _close(self, forced: str | None = None) -> None:
        s = self.state
        if forced:
            s.ending = forced
        elif s.saved == 4 and s.medicine == "delivered" and s.iven == "rescued":
            s.ending = "FULL_RESCUE"
        elif s.saved == 4:
            s.ending = "PEOPLE_SAFE"
        elif s.saved:
            s.ending = "PARTIAL_CROSSING"
        else:
            s.ending = "SHELTERED"
        s.phase = "ending"

    def act(self, action: str) -> dict:
        options = {c.name: c for c in self.choices()}
        if action not in options:
            raise ValueError("That choice is unavailable. Use a listed choice.")
        before = self.snapshot()
        choice = options[action]
        s = self.state
        text, workshop_trace = "", None
        if s.phase == "pack":
            if action == "ready":
                s.phase = "workshop"
                text = WORKSHOP_INTRO
            elif action in s.kit:
                s.kit.remove(action)
                text = f"You return the {action} to Mara's cart."
            else:
                s.kit.add(action)
                text = f"You take the {action}."
        elif s.phase == "workshop":
            workshop_trace = self.workshop.act(action)
            text = f"{workshop_trace['speaker']}: {workshop_trace['text']}"
            s.elapsed = self.workshop.state.turn
            s.time = max(0, RIVER_WINDOW - s.elapsed)
            text += "".join("\n" + n for n in self._spend(0))
            if self.workshop.state.ending:
                s.light = self.workshop.state.ending == "COOPERATED"
                s.time = max(0, RIVER_WINDOW - self.workshop.state.turn)
                s.elapsed = self.workshop.state.turn
                s.phase = "route"
                if s.light:
                    text += "\nThe Keeper seats the rune in a hooded lantern. 'Fit it at the causeway.\nThe boards are your problem. Use the light to call down the mill workers.'"
                else:
                    text += "\nMara lifts the medicine chest. 'Then we're using the ferry. Come on.'"
                if not s.time:
                    text += "\nThe landing is already under water. Mara turns the cart toward high ground."
                    self._close()
        else:
            if action in ("retreat", "finish"):
                text = "You call an end to the operation. Mara checks the names on her cart list."
                self._close()
            elif action in ("causeway", "ferry"):
                s.route = s.phase = action
                text = ("You fit the rune into the causeway socket. Light picks out the mill yard,\n"
                        "but a gap cuts the line of stones."
                        if action == "causeway" else
                        "The lower track ends at Iven's pinned ferry. The mill yard is still dry.\nMara: 'We'll load here. The high road is across the channel.'")
            elif action == "roof":
                s.roof = "rescued"
                s.waiting += 2
                if s.light:
                    method = "You sweep the Waystone light across the stair below the roof."
                elif "oil" in s.kit:
                    s.kit.remove("oil")
                    method = "You burn the oil in Mara's lamp and light the hidden stair."
                elif "rope" in s.kit:
                    s.kit.remove("rope")
                    method = "You fasten your rope to the roof rail and lower the workers."
                else:
                    method = "You and Mara drag a ladder through the mud and brace it against the mill."
                text = method + "\nSenn comes down first. Lio follows with an empty flour sack.\n'It was full this morning,' he says. Mara takes it without answering."
            elif action in ("iven", "iven_hands"):
                s.iven = "rescued"
                if action == "iven" and "rope" in s.kit:
                    s.kit.remove("rope")
                    method = "You anchor the rope to a mill post; Iven pulls himself off the jetty."
                else:
                    method = "You and Mara lever the jetty aside with a broken spar. Iven crawls clear."
                text = method + "\nIven: 'I know where the channel pulls. Give me the tiller, not another order.'"
                if "FLAG_PLAYER_LIED" in self.workshop.state.flags:
                    text += "\nMara looks at you. This time you pass him the tiller without invoking the council."
            elif action == "span":
                s.kit.remove("timber")
                s.bridge = "stable"
                text = "You fix the new boards between two sound stone piers. Mara tests them\nwith the cart's empty axle. It rolls straight; the road can carry the chest."
            elif action == "lash":
                s.kit.remove("rope")
                s.bridge = "temporary"
                text = "The rope holds between the piers. Each crossing will need steady hands.\nMara leaves the cart behind; the medicine must be carried separately."
            elif action == "wade":
                s.bridge = "waded"
                text = "You probe the submerged stones with a pole. The others can follow your\nfootmarks, slowly. The medicine chest would sit below the waterline."
            elif action in ("lead", "convoy"):
                s.saved += s.waiting
                s.waiting = 0
                text = "Mara counts the villagers onto the high road, one hand on each shoulder."
                if action == "convoy":
                    s.medicine = "delivered"
                    text += "\nThe cart follows. The chest's wax seal is dry."
            elif action == "medicine":
                s.medicine = "delivered"
                text = "You carry the chest between you and Mara. At the high road she checks\nthe wax seal, then sets it beyond the reach of the water."
            elif action == "board":
                capacity = 3 if s.iven == "rescued" else 2
                count = min(s.waiting, capacity - s.aboard - (s.medicine == "aboard"))
                s.aboard += count
                s.waiting -= count
                text = f"{count} villager(s) step aboard. Mara shifts their weight away from the cracked bow."
            elif action == "load":
                s.medicine = "aboard"
                text = "Mara wedges the medicine chest beneath the seat. 'Dry until a surge gets in.'"
            elif action == "unload":
                s.waiting += s.aboard
                s.aboard = 0
                if s.medicine == "aboard":
                    s.medicine = "waiting"
                text = "You unload onto the mill bank and choose a different cargo order."
            elif action == "secure":
                s.kit.remove("rope")
                s.line = True
                text = "You rig a line between the mill and the road bank. The ferry can now\nfollow it through the pull without taking water."
            elif action == "reinforce":
                s.kit.remove("timber")
                s.hull += 3
                text = "You lash timber beneath the cracked bow. It adds buoyancy, not a lid\nfor the medicine chest; a surge can still wet the cargo."
            elif action == "hold":
                text = "You hold the ferry against the jetty. The current moves past; the hull stays intact."
            elif action == "row":
                currents = [self.current(i) for i in range(choice.cost)]
                damage = 0 if s.line else sum({"slack": 0, "pull": 1, "surge": 2}[c] for c in currents)
                s.hull = max(0, s.hull - damage)
                text = f"You cross through {' then '.join(currents)}. The hull loses {damage}."
                if not s.line and "surge" in currents and s.medicine == "aboard":
                    s.medicine = "spoiled"
                    text += "\nWater enters the medicine chest. Mara prises it open; the paper packets run to pulp."
                if not s.hull:
                    text += "\nThe bow gives way. Everyone aboard catches the jetty's safety chains.\nYou pull them onto the nearest bank; the crossing is over."
                    if s.medicine == "aboard":
                        s.medicine = "spoiled"
                    self._close("BOAT_LOST")
                else:
                    s.bank = "road" if s.bank == "mill" else "mill"
                    if s.bank == "road":
                        s.saved += s.aboard
                        s.aboard = 0
                        if s.medicine == "aboard":
                            s.medicine = "delivered"
                        text += "\nThe passengers step onto the high road. Mara marks their names."
                    else:
                        text += "\nThe empty ferry returns to the mill bank."
            text += "".join("\n" + n for n in self._spend(choice.cost))
            if not s.ending and not s.time:
                text += "\nThe landing disappears under the flood. There is no time for another trip."
                self._close()
        result = {"action": action, "cost": choice.cost, "text": text,
                  "before": before, "after": self.snapshot(), "workshop_trace": workshop_trace}
        self.history.append(result)
        return result

    def epilogue(self) -> str:
        s = self.state
        if not s.ending:
            raise ValueError("The operation is still open.")
        lines = [f"Ending: {s.ending}", f"High-road arrivals: {s.saved}/4. Medicine: {s.medicine}."]
        if s.saved == 4:
            lines.append("At the shelter Mara calls four names. Four people answer. Senn sits beside\nthe stove, both hands around a mug. Lio sets his empty flour sack beneath her wet boots.")
        elif s.saved:
            lines.append("Mara seats the arrivals by the stove and writes the missing names for\nthe morning crew. The others shelter at the mill or north loft tonight.")
        else:
            lines.append("Mara turns the cart toward the hill shelter. No one reached the high road\nthrough your crossing. The mill party must wait above the flood until morning.")
        if s.medicine == "delivered":
            lines.append("The clinic chest arrives sealed. Mara hands it to the night attendant\nbefore she takes off her wet coat.")
        elif s.medicine == "spoiled":
            lines.append("The night attendant tips water from the chest and reaches for the last dry\nbandages. Mara takes back her cart list and adds a fresh clinic load for morning.")
        else:
            lines.append("The medicine is still at the mill. Mara puts it first on the morning list.")
        if s.iven == "rescued":
            lines.append("Iven reaches shelter with the party. He asks who has dry boots for tomorrow.")
        else:
            lines.append("Iven is beyond tonight's reach; the morning crew must check the jetty and north shoal.")
        if s.bridge == "stable":
            lines.append("The Waystone marks a repaired causeway. Tomorrow's carts have a road again.")
        elif s.bridge:
            lines.append("The Waystone still burns, but tomorrow's crew must replace your temporary crossing.")
        elif s.route == "ferry" and s.hull and s.iven == "rescued":
            lines.append("Iven leaves the ferry tied above the landing. The village keeps its river route.")
        if "FLAG_PLAYER_LIED" in self.workshop.state.flags:
            if self.workshop.state.apology_due:
                lines.append("Your false council order remains uncorrected. The Keeper will hear about the crossing,\nbut Mara will not carry that order back as fact.")
            else:
                lines.append("In the morning the Keeper asks Mara about the council order. 'Withdrawn,'\nshe says. Then she hands over the crossing crew's repair list.")
        return "\n\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Play Flood Crossing, a complete Waystone adventure.")
    parser.add_argument("--trace", action="store_true", help="Print a JSON transition after each accepted choice.")
    parser.add_argument("--version", action="version", version=VERSION)
    args = parser.parse_args()
    game = Adventure()
    print("Commands: status, look, restart, quit. Numbers follow the current menu.\n")
    print(INTRO + "\n\n" + game.describe())
    try:
        while True:
            options = game.choices()
            for i, choice in enumerate(options, 1):
                print(f"{i}. {choice.name}: {choice.label}")
            try:
                token = input("> ").strip().lower()
            except EOFError:
                print("\nSession closed. No progress is saved.")
                return 0
            if token == "quit":
                return 0
            if token == "restart":
                game.restart()
                print("\nAdventure restarted.\n" + INTRO + "\n\n" + game.describe())
                continue
            if token == "status":
                print(json.dumps(game.snapshot(), sort_keys=True))
                continue
            if token == "look":
                print(game.describe())
                continue
            if token.isascii() and token.isdigit():
                token = options[int(token) - 1].name if len(token) <= 2 and 1 <= int(token) <= len(options) else ""
            try:
                result = game.act(token)
            except ValueError as exc:
                print(exc)
                continue
            print("\n" + result["text"])
            if args.trace:
                print("TRACE " + json.dumps(result, sort_keys=True))
            print("\n" + game.describe())
            if game.state.ending:
                print("Commands: restart, status, look, quit.")
    except KeyboardInterrupt:
        print("\nSession closed. No progress is saved.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
