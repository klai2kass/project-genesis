"""Milestone 3 step 1: every agent has a home (where it was born).

Rule (genesis/agents.py, _step_home): only while WANDERING (no reachable food
in sight, or pack full), an agent more than home_radius tiles from home
(counted as king's-move steps) takes the land step that brings it closest to
home. If no step gets it closer (water in the way) it wanders normally.
home_radius = 0 switches homes off, which must reproduce Milestone 2 exactly.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import (create_world, load_world, step, world_from_json,  # noqa: E402
                     world_to_json)
from genesis.digest import EventDigest, behaviour_digest  # noqa: E402
from genesis.rng import Rng  # noqa: E402
from genesis.save import MILESTONE2_RULES  # noqa: E402
from genesis.world import GRASS, WATER, make_agent  # noqa: E402

REF = json.load(open(os.path.join(ROOT, "experiments", "baseline", "milestone2.json")))
FIXTURE_V3 = os.path.join(ROOT, "tests", "fixtures", "save_v3_seed42_t300.json")


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def open_world(**cfg):
    """30 x 30 grass, no food growing, one agent that never ages or breeds."""
    settings = {"width": 30, "height": 30, "start_agents": 0, "regrow_per_tick": 0,
                "max_energy": 10 ** 6, "repro_min_age": 10 ** 6, "history_keep": 0,
                "rest_below": 0}
    settings.update(cfg)
    w = create_world(1, settings)
    w["terrain"] = [GRASS] * (30 * 30)
    w["food"] = [0] * (30 * 30)
    a = make_agent(1, 5, 5, 50, 100, Rng(5), w["config"])
    a["max_age"] = 10 ** 6
    a["home"] = [20, 20]
    w["agents"] = [a]
    w["next_id"] = 2
    return w, a


class HomesOffIsMilestoneTwo(unittest.TestCase):
    def test_home_radius_zero_reproduces_frozen_milestone2(self):
        for seed, ref in REF["short"].items():
            w = create_world(seed, dict(MILESTONE2_RULES))
            ed = EventDigest()
            for _ in range(500):
                ed.add(step(w))
            s = w["stats"]
            now = {"alive": len(w["agents"]), "births": s["births"],
                   "starved": s["deaths_starved"], "old_age": s["deaths_old_age"],
                   "behaviour_digest": behaviour_digest(w), "event_digest": ed.hexdigest()}
            self.assertEqual(now, ref, "seed " + seed)

    def test_homes_on_do_change_behaviour(self):
        w = create_world("42")
        self.assertEqual(w["config"]["home_radius"], 6)
        ed = EventDigest()
        for _ in range(500):
            ed.add(step(w))
        self.assertNotEqual(ed.hexdigest(), REF["short"]["42"]["event_digest"])

    def test_v3_save_migrates_keeps_its_rules_and_continues_the_same(self):
        w = load_world(FIXTURE_V3)
        self.assertEqual(w["version"], 4)
        self.assertEqual(w["config"]["home_radius"], 0)
        self.assertTrue(all(a["home"] == [a["x"], a["y"]] for a in w["agents"]))
        log = w["migration_log"]
        self.assertTrue(any("version 3 -> 4" in line for line in log))
        self.assertTrue(any("home_radius" in line and "old rules" in line for line in log))
        ed = EventDigest()
        for _ in range(200):
            ed.add(step(w))
        self.assertEqual({"tick": w["tick"], "behaviour_digest": behaviour_digest(w),
                          "event_digest": ed.hexdigest()}, REF["save_v3"])

    def test_v2_save_gets_homes_and_homes_off(self):
        w = load_world(os.path.join(ROOT, "tests", "fixtures", "save_v2_seed42_t300.json"))
        self.assertEqual(w["config"]["home_radius"], 0)
        self.assertTrue(all(a["home"] == [a["x"], a["y"]] for a in w["agents"]))


class WhereHomeIs(unittest.TestCase):
    def test_founders_home_is_start_and_children_home_is_birth_tile(self):
        w = create_world("42")
        start = {a["id"]: [a["x"], a["y"]] for a in w["agents"]}
        self.assertTrue(all(a["home"] == start[a["id"]] for a in w["agents"]))
        born = {}
        for _ in range(400):
            for e in step(w):
                if e["action"] == "born":
                    born[e["agent"]] = [e["x"], e["y"]]
        self.assertTrue(born)
        for a in w["agents"]:
            self.assertEqual(a["home"], born.get(a["id"], start.get(a["id"])))

    def test_home_survives_save_and_load(self):
        w = create_world("42")
        for _ in range(200):
            step(w)
        again = world_from_json(world_to_json(w))
        self.assertEqual([a["home"] for a in again["agents"]],
                         [a["home"] for a in w["agents"]])
        self.assertNotIn("migration_log", again)


class TheRule(unittest.TestCase):
    def test_far_away_agent_walks_home_and_then_stays_near(self):
        w, a = open_world(home_radius=6)
        dist = [cheb((a["x"], a["y"]), a["home"])]
        whys = []
        for _ in range(200):
            for e in step(w):
                whys.append(e["why"])
            dist.append(cheb((a["x"], a["y"]), a["home"]))
        # 15 steps away: one step closer every tick until inside the radius ...
        self.assertEqual(dist[:10], list(range(15, 5, -1)))
        self.assertIn("heading home", whys[0])
        self.assertIn("15 tiles from home (20, 20)", whys[0])
        # ... and afterwards never more than one step outside it.
        self.assertTrue(all(d <= 7 for d in dist[10:]), dist)

    def test_homes_off_lets_it_drift(self):
        w, a = open_world(home_radius=0)
        for _ in range(60):
            for e in step(w):
                self.assertNotIn("home", e["why"])

    def test_home_never_beats_eat_gather_or_food_in_sight(self):
        # Food 2 tiles away, AWAY from home: it walks to the food, not home.
        w, a = open_world(home_radius=3)
        w["food"][5 * 30 + 3] = 2
        e = step(w)[0]
        self.assertEqual((e["action"], a["x"]), ("move", 4))   # toward the food
        self.assertIn("nearest reachable food", e["why"])
        self.assertNotIn("home", e["why"])
        e = step(w)[0]
        self.assertEqual(e["action"], "move")
        e = step(w)[0]
        self.assertEqual(e["action"], "gather")
        # Hungry with food in the pack: eats, far from home or not.
        a["energy"] = 40
        self.assertEqual(step(w)[0]["action"], "eat")

    def test_home_never_beats_rest(self):
        w, a = open_world(home_radius=3, rest_below=30)
        a["energy"] = 1000           # not hungry
        a["needs"]["rest"] = 10      # tired
        self.assertEqual(step(w)[0]["action"], "rest")

    def test_water_in_the_way_falls_back_to_wandering(self):
        # A wall of water at x = 11 between the agent (10, 15) and home (20, 15).
        w, a = open_world(home_radius=3)
        for y in range(30):
            w["terrain"][y * 30 + 11] = WATER
        a["x"], a["y"], a["home"] = 10, 15, [20, 15]
        a["energy"] = 10 ** 5        # lives through the whole test
        xs = []
        for _ in range(100):
            for e in step(w):
                self.assertEqual(e["action"], "move")
            xs.append(a["x"])
        self.assertTrue(all(x <= 10 for x in xs))     # never walks into water
        self.assertGreater(len(set(xs)), 1)           # and is not frozen in place

    def test_same_seed_same_world_with_homes(self):
        a, b = create_world("9"), create_world("9")
        for _ in range(300):
            step(a)
            step(b)
        self.assertEqual(world_to_json(a), world_to_json(b))


if __name__ == "__main__":
    unittest.main()
