"""Milestone 3 step 3: share food with a starving agent you know.

Rule (genesis/agents.py, who_to_help): checked after eat and reproduce,
before gather. A not-hungry agent (energy above eat_below) with food in its
pack gives 1 food to an agent within 1 tile that is starving (energy 20 or
less, empty pack) and that it has met share_min_meetings or more times.
Several: most meetings, then lowest energy, then lowest id. No dice.
share_min_meetings = 0 switches it off and must reproduce the world before
sharing exactly.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, load_world, step, world_from_json, world_to_json  # noqa: E402
from genesis.digest import EventDigest, behaviour_digest  # noqa: E402
from genesis.rng import Rng  # noqa: E402
from genesis.save import MEMORY_ONLY_RULES  # noqa: E402
from genesis.world import GRASS, SAVE_VERSION, make_agent  # noqa: E402

REF = json.load(open(os.path.join(ROOT, "experiments", "baseline", "milestone3_memory.json")))
FIXTURE_V5 = os.path.join(ROOT, "tests", "fixtures", "save_v5_seed42_t300.json")


def tiny(agents, **cfg):
    """agents: list of (id, x, y, energy, food). Open grass, no food on the
    ground, nobody ages, breeds or rests, homes off."""
    settings = {"width": 20, "height": 20, "start_agents": 0, "regrow_per_tick": 0,
                "history_keep": 0, "repro_min_age": 10 ** 6, "rest_below": 0,
                "home_radius": 0}
    settings.update(cfg)
    w = create_world(1, settings)
    w["terrain"] = [GRASS] * 400
    w["food"] = [0] * 400
    w["agents"] = []
    for aid, x, y, energy, food in agents:
        a = make_agent(aid, x, y, energy, 100, Rng(aid), w["config"])
        a["food"], a["max_age"] = food, 10 ** 6
        w["agents"].append(a)
    w["next_id"] = 100
    return w


def knows(w, a_id, b_id, meetings):
    a = next(a for a in w["agents"] if a["id"] == a_id)
    a["memory"].append([b_id, 0, 0, meetings, a["x"], a["y"], 0, 0])


def agent(w, aid):
    return next(a for a in w["agents"] if a["id"] == aid)


def first(events, aid):
    return next(e for e in events if e["agent"] == aid)


class SharingOffIsTheOldWorld(unittest.TestCase):
    def test_share_zero_reproduces_frozen_memory_world(self):
        for seed, ref in REF["short"].items():
            w = create_world(seed, dict(MEMORY_ONLY_RULES))
            ed = EventDigest()
            for _ in range(500):
                ed.add(step(w))
            s = w["stats"]
            now = {"alive": len(w["agents"]), "births": s["births"],
                   "starved": s["deaths_starved"], "old_age": s["deaths_old_age"],
                   "behaviour_digest": behaviour_digest(w), "event_digest": ed.hexdigest()}
            ref = {k: v for k, v in ref.items() if k != "memory"}
            self.assertEqual(now, ref, "seed " + seed)
            self.assertEqual(s["gifts"], 0)

    def test_sharing_on_changes_behaviour_and_gifts_happen(self):
        w = create_world("42")
        self.assertEqual(w["config"]["share_min_meetings"], 2)
        ed = EventDigest()
        for _ in range(500):
            ed.add(step(w))
        self.assertNotEqual(ed.hexdigest(), REF["short"]["42"]["event_digest"])
        self.assertGreater(w["stats"]["gifts"], 0)

    def test_v5_save_migrates_keeps_its_rules_and_continues_the_same(self):
        w = load_world(FIXTURE_V5)
        self.assertEqual(w["version"], SAVE_VERSION)
        self.assertEqual(w["config"]["share_min_meetings"], 0)
        self.assertEqual(w["stats"]["gifts"], 0)
        self.assertTrue(all(len(e) == 8 for a in w["agents"] for e in a["memory"]))
        log = w["migration_log"]
        self.assertTrue(any("version 5 -> 6" in line for line in log))
        self.assertTrue(any("share_min_meetings" in line and "old rules" in line for line in log))
        ed = EventDigest()
        for _ in range(200):
            ed.add(step(w))
        self.assertEqual({"tick": w["tick"], "behaviour_digest": behaviour_digest(w),
                          "event_digest": ed.hexdigest()}, REF["save_v5"])


class TheRule(unittest.TestCase):
    def test_gives_one_food_and_both_memories_count_it(self):
        w = tiny([(1, 5, 5, 100, 2), (2, 6, 5, 15, 0)])
        knows(w, 1, 2, 3)
        knows(w, 2, 1, 3)
        ev = step(w)
        e = first(ev, 1)
        self.assertEqual((e["action"], e["to"]), ("give", 2))
        self.assertIn("gave 1 food to #2 (we have met 3 times)", e["why"])
        self.assertIn("to help #2", e["need"])
        self.assertEqual((agent(w, 1)["food"], w["stats"]["gifts"]), (1, 1))
        # #2 acts after #1 in the same tick, so it already ate the gift.
        self.assertEqual(first(ev, 2)["action"], "eat")
        self.assertEqual(agent(w, 2)["food"], 0)
        self.assertEqual(agent(w, 2)["energy"], 15 - 1 + 20)
        gave = next(m for m in agent(w, 1)["memory"] if m[0] == 2)
        got = next(m for m in agent(w, 2)["memory"] if m[0] == 1)
        self.assertEqual((gave[6], gave[7], got[6], got[7]), (1, 0, 0, 1))

    def _gives(self, receiver_energy=15, receiver_food=0, giver_energy=100,
               meetings=2, dx=1, **cfg):
        w = tiny([(1, 5, 5, giver_energy, 1), (2, 5 + dx, 5, receiver_energy, receiver_food)],
                 **cfg)
        knows(w, 1, 2, meetings)
        return first(step(w), 1)["action"] == "give"

    def test_when_it_gives_and_when_not(self):
        self.assertTrue(self._gives())
        self.assertFalse(self._gives(meetings=1))            # met only once
        self.assertFalse(self._gives(dx=2))                  # 2 tiles away
        self.assertFalse(self._gives(giver_energy=81))       # 80 after the drain: hungry
        self.assertTrue(self._gives(giver_energy=82))        # 81: not hungry
        self.assertFalse(self._gives(receiver_energy=22))    # 21 after drain: not starving
        self.assertFalse(self._gives(receiver_food=1))       # has food of its own
        self.assertFalse(self._gives(share_min_meetings=0))  # sharing off
        self.assertTrue(self._gives(meetings=5, share_min_meetings=5))
        self.assertFalse(self._gives(meetings=4, share_min_meetings=5))

    def test_reproduce_and_eat_come_first(self):
        # Hungry giver with food eats instead (energy 50 -> 49 <= 80).
        w = tiny([(1, 5, 5, 50, 1), (2, 6, 5, 15, 0)])
        knows(w, 1, 2, 3)
        self.assertEqual(first(step(w), 1)["action"], "eat")
        # A giver that can have a child does that first.
        w = tiny([(1, 5, 5, 100, 1), (2, 6, 5, 15, 0)], repro_min_age=0)
        knows(w, 1, 2, 3)
        self.assertEqual(first(step(w), 1)["action"], "reproduce")

    def test_choice_most_met_then_lowest_energy_then_lowest_id(self):
        w = tiny([(1, 5, 5, 100, 1), (2, 6, 5, 15, 0), (3, 4, 5, 10, 0), (4, 5, 6, 10, 0)])
        knows(w, 1, 2, 5)
        knows(w, 1, 3, 3)
        knows(w, 1, 4, 3)
        self.assertEqual(first(step(w), 1)["to"], 2)              # most met
        w = tiny([(1, 5, 5, 100, 1), (2, 6, 5, 15, 0), (3, 4, 5, 10, 0), (4, 5, 6, 10, 0)])
        for other in (2, 3, 4):
            knows(w, 1, other, 3)
        self.assertEqual(first(step(w), 1)["to"], 3)              # lowest energy, then id

    def test_never_gives_to_an_agent_that_died_this_tick(self):
        # #1 has 1 energy: it starves at the start of its turn, before #2 acts.
        w = tiny([(1, 6, 5, 1, 0), (2, 5, 5, 100, 1)])
        knows(w, 2, 1, 3)
        ev = step(w)
        self.assertEqual(first(ev, 1)["action"], "die")
        self.assertNotEqual(first(ev, 2)["action"], "give")


class Determinism(unittest.TestCase):
    def test_same_seed_and_save_load_with_sharing(self):
        a, b = create_world("7"), create_world("7")
        for _ in range(300):
            step(a)
            step(b)
        self.assertEqual(world_to_json(a), world_to_json(b))
        self.assertGreater(a["stats"]["gifts"], 0)
        b = world_from_json(world_to_json(b))
        self.assertNotIn("migration_log", b)
        for _ in range(200):
            step(a)
            step(b)
        self.assertEqual(world_to_json(a), world_to_json(b))


if __name__ == "__main__":
    unittest.main()
