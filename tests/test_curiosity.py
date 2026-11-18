"""The curiosity fix (2026-11-18): curious agents turn LESS and walk straighter.

Rule (genesis/traits.py, turn_percent), with curiosity_straight = 1:
    turn = turn_chance - ((curiosity - 50) * turn_span) // 100
The old Milestone 2 rule (curiosity_straight = 0) used "+": curious agents
turned more, zigzagged and reached FEWER new tiles
(experiments/results/curiosity_before.txt). Curiosity 50 gives 15% either way.
"""
import json
import math
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, load_world, step, world_to_json  # noqa: E402
from genesis.config import DEFAULT_CONFIG  # noqa: E402
from genesis.digest import EventDigest, behaviour_digest  # noqa: E402
from genesis.overrides import parse_overrides  # noqa: E402
from genesis.rng import Rng  # noqa: E402
from genesis.traits import turn_percent  # noqa: E402
from genesis.world import GRASS, SAVE_VERSION, make_agent  # noqa: E402

FIXTURES = os.path.join(ROOT, "tests", "fixtures")
OLD = json.load(open(os.path.join(ROOT, "experiments", "baseline",
                                  "milestone3_curiosity_old.json")))


def pct(curiosity, straight):
    cfg = dict(DEFAULT_CONFIG, curiosity_straight=straight)
    return turn_percent({"traits": {"curiosity": curiosity}}, cfg)


def walker(curiosity, seed, size=400):
    """Open grass, no food, one agent that never tires, starves, ages or
    breeds and has no home: only wandering is left. The world is made small
    (fast) and then widened to size x size grass; 400 x 400 so that 500
    ticks of walking from the middle rarely reach an edge."""
    w = create_world(seed, {"width": 20, "height": 20, "start_agents": 0,
                            "regrow_per_tick": 0, "max_energy": 10 ** 6,
                            "repro_min_age": 10 ** 6, "history_keep": 0,
                            "rest_below": 0, "home_radius": 0})
    w["config"]["width"] = w["config"]["height"] = size
    w["terrain"] = [GRASS] * (size * size)
    w["food"] = [0] * (size * size)
    a = make_agent(1, size // 2, size // 2, 10 ** 5, 100, Rng(3), w["config"],
                   traits={"curiosity": curiosity, "industriousness": 50})
    a["max_age"] = 10 ** 6
    w["agents"], w["next_id"] = [a], 2
    return w, a


def explore(curiosity, seed, ticks=500):
    """(distinct tiles visited, heading changes, distance from the start at
    the end) over `ticks` ticks."""
    w, a = walker(curiosity, seed)
    x0, y0 = a["x"], a["y"]
    seen, turns, last = {(x0, y0)}, 0, a["heading"]
    for _ in range(ticks):
        step(w)
        seen.add((a["x"], a["y"]))
        turns += a["heading"] != last
        last = a["heading"]
    return len(seen), turns, math.hypot(a["x"] - x0, a["y"] - y0)


class TheNumbers(unittest.TestCase):
    def test_new_rule_values_including_edges_and_rounding(self):
        # 15 - ((c - 50) * 20) // 100; // rounds DOWN, so 49 gives 16.
        expected = {0: 25, 10: 23, 45: 16, 49: 16, 50: 15, 51: 15, 54: 15,
                    55: 14, 90: 7, 100: 5}
        self.assertEqual({c: pct(c, 1) for c in expected}, expected)

    def test_old_rule_values_unchanged(self):
        expected = {0: 5, 10: 7, 49: 14, 50: 15, 51: 15, 90: 23, 100: 25}
        self.assertEqual({c: pct(c, 0) for c in expected}, expected)

    def test_neutral_is_fifteen_either_way_and_stays_within_0_100(self):
        self.assertEqual(pct(50, 0), pct(50, 1), 15)
        cfg = dict(DEFAULT_CONFIG, turn_chance=95, turn_span=200)
        for c in (0, 100):
            self.assertTrue(0 <= turn_percent({"traits": {"curiosity": c}}, cfg) <= 100)

    def test_setting_is_on_by_default_and_can_be_changed(self):
        self.assertEqual(DEFAULT_CONFIG["curiosity_straight"], 1)
        self.assertEqual(parse_overrides(["curiosity_straight=0"]), {"curiosity_straight": 0})
        with self.assertRaises(ValueError):
            parse_overrides(["curiosity_straight=2"])


class NeutralAndOldWorldsUnchanged(unittest.TestCase):
    def test_all_neutral_world_is_identical_under_both_rules(self):
        cfg = {"trait_founder_min": 50, "trait_founder_max": 50, "trait_mutation": 0}
        a = create_world("5", dict(cfg, curiosity_straight=0))
        b = create_world("5", dict(cfg, curiosity_straight=1))
        for _ in range(400):
            step(a)
            step(b)
        a["config"].pop("curiosity_straight")
        b["config"].pop("curiosity_straight")
        self.assertEqual(world_to_json(a), world_to_json(b))

    def test_new_rule_changes_the_default_world(self):
        a, b = create_world("42", {"curiosity_straight": 0}), create_world("42")
        ea, eb = EventDigest(), EventDigest()
        for _ in range(300):
            ea.add(step(a))
            eb.add(step(b))
        self.assertNotEqual(ea.hexdigest(), eb.hexdigest())

    def test_v8_save_migrates_keeps_old_rule_and_continues_the_same(self):
        w = load_world(os.path.join(FIXTURES, "save_v8_seed42_t300.json"))
        self.assertEqual(w["version"], SAVE_VERSION)
        self.assertEqual(w["config"]["curiosity_straight"], 0)
        self.assertTrue(any("curiosity_straight" in line and "old rules" in line
                            for line in w["migration_log"]))
        ed = EventDigest()
        for _ in range(200):
            ed.add(step(w))
        got = {"tick": w["tick"], "behaviour_digest": behaviour_digest(w),
               "event_digest": ed.hexdigest()}
        want = {k: OLD["save_v8"][k] for k in got}
        self.assertEqual(got, want)

    def test_every_older_save_gets_the_old_rule(self):
        for v in (2, 3, 4, 5, 6, 7, 8):
            w = load_world(os.path.join(FIXTURES, "save_v%d_seed42_t300.json" % v))
            self.assertEqual(w["config"]["curiosity_straight"], 0, "v%d" % v)


class Acceptance(unittest.TestCase):
    """Two otherwise identical agents, curiosity 10 and 90, same dice."""

    def test_curious_agent_turns_less_gets_further_and_sees_more_tiles(self):
        # 20 pairs; within a pair only curiosity differs (same world dice,
        # same start). Each walk is still luck, so "consistently" means:
        # always fewer turns, and further / more tiles in clearly most pairs
        # and on average. Measured when written: heading changes 31 vs 101
        # per 500 ticks; further in 18 of 20 (mean 125 vs 51 tiles); more
        # distinct tiles in 17 of 20 (452 vs 423).
        low = [explore(10, seed) for seed in range(1, 21)]
        high = [explore(90, seed) for seed in range(1, 21)]
        for (lc, lt, ld), (hc, ht, hd) in zip(low, high):
            self.assertLess(ht, lt)
        further = sum(h[2] > l[2] for l, h in zip(low, high))
        more = sum(h[0] > l[0] for l, h in zip(low, high))
        self.assertGreaterEqual(further, 15)
        self.assertGreaterEqual(more, 14)
        self.assertGreater(sum(h[2] for h in high), 1.3 * sum(l[2] for l in low))
        self.assertGreater(sum(h[0] for h in high), sum(l[0] for l in low))

    def test_same_seed_same_walk(self):
        self.assertEqual(explore(90, 4), explore(90, 4))


if __name__ == "__main__":
    unittest.main()
