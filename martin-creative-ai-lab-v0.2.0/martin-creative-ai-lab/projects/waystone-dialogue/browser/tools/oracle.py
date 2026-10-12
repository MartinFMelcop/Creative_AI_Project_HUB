#!/usr/bin/env python3
"""Emit real Python transitions, including every river successor of 12 entries."""
import copy
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from adventure import Adventure

def emit(game):
    choices = [vars(c) for c in game.choices()]
    transitions = []
    for c in choices:
        child = copy.deepcopy(game)
        transitions.append(child.act(c["name"]))
    print(json.dumps({"snapshot": game.snapshot(), "choices": choices,
      "transitions": transitions, "epilogue": game.epilogue() if game.state.ending else None}))

# Dialogue framing, repeat lies, apology ceilings, outburst waits and dusk.
rng = random.Random(301)
for _ in range(180):
    game = Adventure()
    for a in ["rope", "timber", "ready"]:
        emit(game)
        game.act(a)
    while game.state.phase == "workshop":
        emit(game)
        game.act(rng.choice([c.name for c in game.choices()]))
    emit(game)
for talk in (["lie"] * 4 + ["wait"] * 5 + ["apologize", "leave"],
             ["wait"] * 12, ["lie", "apologize", "lie", "apologize", "herbs", "bargain"]):
    game = Adventure()
    for a in ["rope", "oil", "ready"] + talk:
        emit(game)
        game.act(a)
    emit(game)

# Exhaustive river graph, bounded to these actual entry histories, with loops deduped.
seen = set()
for kit in itertools.combinations(("rope", "timber", "oil"), 2):
    for talk, route in [(["herbs", "bargain"], "causeway"),
                        (["herbs", "bargain"], "ferry"),
                        (["leave"], "ferry"), (["wait", "leave"], "ferry")]:
        game = Adventure()
        for a in list(kit) + ["ready"] + talk + [route]:
            game.act(a)
        pending = [game]
        while pending:
            game = pending.pop()
            key = json.dumps(game.snapshot(), sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            emit(game)
            for c in game.choices():
                child = copy.deepcopy(game)
                child.act(c.name)
                # History is not part of the domain state; keep graph traversal lean.
                child.history.clear()
                pending.append(child)
print(json.dumps({"river_states": len(seen)}))
