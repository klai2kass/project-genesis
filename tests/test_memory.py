"""Milestone 3 step 2: encounter memory (genesis/memory.py).

Memory is a record only. It must never change behaviour, it must count each
meeting once (not once per tick), keep at most memory_keep entries, survive
save and load, and agree with an independent, brute-force count.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, load_world, step, world_from_json, world_to_json  # noqa: E402
from genesis.digest import EventDigest, behaviour_digest  # noqa: E402
from genesis.memory import strongest, update_memories  # noqa: E402
from genesis.rng import Rng  # noqa: E402
from genesis.world import GRASS, SAVE_VERSION, make_agent  # noqa: E402

REF = json.load(open(os.path.join(ROOT, "experiments", "baseline", "milestone3_home.json")))
FIXTURE_V4 = os.path.join(ROOT, "tests", "fixtures", "save_v4_seed42_t300.json")


def tiny_world(positions, keep=10):
    """Agents at fixed positions on open grass; we move them by hand and call
    update_memories directly, one 'tick' at a time."""
    w = create_world(1, {"width": 20, "height": 20, "start_agents": 0,
                         "memory_keep": keep, "history_keep": 0})
    w["terrain"] = [GRASS] * 400
    w["agents"] = [make_agent(i + 1, x, y, 50, 100, Rng(i), w["config"])
                   for i, (x, y) in enumerate(positions)]
    return w


def tick(w, positions=None):
    if positions:
        for a, (x, y) in zip(w["agents"], positions):
            a["x"], a["y"] = x, y
    w["tick"] += 1
    return update_memories(w)


def entry(agent, other):
    return next((e for e in agent["memory"] if e[0] == other), None)


class RecordOnly(unittest.TestCase):
    def _short(self, seed, cfg):
        w = create_world(seed, cfg)
        ed = EventDigest()
        for _ in range(500):
            ed.add(step(w))
        s = w["stats"]
        return w, {"alive": len(w["agents"]), "births": s["births"],
                   "starved": s["deaths_starved"], "old_age": s["deaths_old_age"],
                   "behaviour_digest": behaviour_digest(w), "event_digest": ed.hexdigest()}

    def test_memory_on_or_off_reproduces_frozen_homes_world(self):
        for seed, ref in REF["short"].items():
            # Sharing (step 3) is the first thing that READS memory, so it is
            # switched off here; memory alone must change nothing.
            w, now = self._short(seed, {"share_min_meetings": 0, "home_inherit": 0})
            self.assertEqual(now, ref, "memory on, seed " + seed)
            self.assertTrue(any(a["memory"] for a in w["agents"]))
            # Memory off: nobody knows anybody, so even with sharing on
            # nobody gives, and the world is the homes world again.
            w, now = self._short(seed, {"memory_keep": 0, "home_inherit": 0})
            self.assertEqual(now, ref, "memory off, seed " + seed)
            self.assertFalse(any(a["memory"] for a in w["agents"]))

    def test_v4_save_migrates_and_continues_the_same(self):
        w = load_world(FIXTURE_V4)
        self.assertEqual(w["version"], SAVE_VERSION)
        self.assertTrue(all(a["memory"] == [] for a in w["agents"]))
        self.assertTrue(any("version 4 -> 5" in line for line in w["migration_log"]))
        ed = EventDigest()
        for _ in range(200):
            ed.add(step(w))
        self.assertEqual({"tick": w["tick"], "behaviour_digest": behaviour_digest(w),
                          "event_digest": ed.hexdigest()}, REF["save_v4"])
        self.assertTrue(any(a["memory"] for a in w["agents"]))


class Counting(unittest.TestCase):
    def test_one_meeting_is_counted_once_and_a_new_one_again(self):
        w = tiny_world([(5, 5), (6, 6)])
        a, b = w["agents"]
        self.assertEqual(tick(w), 1)                    # tick 1: they meet
        self.assertEqual(tick(w), 0)                    # tick 2: still together
        self.assertEqual(entry(a, 2), [2, 1, 2, 1, 5, 5, 0, 0])
        self.assertEqual(entry(b, 1), [1, 1, 2, 1, 6, 6, 0, 0])
        self.assertEqual(tick(w, [(5, 5), (8, 8)]), 0)  # tick 3: apart
        self.assertEqual(entry(a, 2), [2, 1, 2, 1, 5, 5, 0, 0])
        self.assertEqual(tick(w, [(9, 9), (8, 8)]), 1)  # tick 4: together again
        self.assertEqual(entry(a, 2), [2, 1, 4, 2, 9, 9, 0, 0])
        self.assertEqual(entry(b, 1), [1, 1, 4, 2, 8, 8, 0, 0])

    def test_same_tile_counts_two_tiles_apart_does_not(self):
        w = tiny_world([(5, 5), (5, 5), (7, 5)])
        tick(w)
        a, b, c = w["agents"]
        self.assertIsNotNone(entry(a, 2))
        self.assertIsNone(entry(a, 3))
        self.assertIsNone(entry(c, 1))

    def test_cap_drops_the_least_met_and_keeps_a_friend(self):
        # Keep 2. Agent 1 meets #2 three separate times, then #3, then #4.
        far = (0, 0)
        w = tiny_world([(10, 10), far, far, far], keep=2)
        for _ in range(3):
            tick(w, [(10, 10), (11, 10), (0, 19), (19, 19)])   # with #2
            tick(w, [(10, 10), (0, 19), (19, 0), (19, 19)])    # apart
        tick(w, [(10, 10), (0, 19), (10, 11), (19, 19)])       # meets #3
        tick(w, [(10, 10), (0, 19), (19, 0), (9, 9)])          # meets #4
        a = w["agents"][0]
        self.assertEqual(sorted(e[0] for e in a["memory"]), [2, 4])  # #3 forgotten
        self.assertEqual(entry(a, 2)[3], 3)

    def test_cap_among_equals_drops_the_one_met_longest_ago(self):
        # Agent 1 at (10, 10) meets 2, then 3, then 4 (one at a time). Keep 2.
        far = (0, 0)
        w = tiny_world([(10, 10), far, far, far], keep=2)
        tick(w, [(10, 10), (11, 10), far, (19, 19)])
        tick(w, [(10, 10), (0, 19), (10, 11), (19, 19)])
        tick(w, [(10, 10), (0, 19), (19, 0), (9, 9)])
        a = w["agents"][0]
        self.assertEqual(sorted(e[0] for e in a["memory"]), [3, 4])

    def test_tie_drops_fewer_meetings_then_lower_id(self):
        w = tiny_world([(10, 10), (11, 10), (9, 10), (10, 11)], keep=2)
        tick(w)                                          # 1 meets 2, 3, 4 at once
        a = w["agents"][0]
        self.assertEqual(sorted(e[0] for e in a["memory"]), [3, 4])

    def test_memory_off_records_nothing(self):
        w = tiny_world([(5, 5), (6, 6)], keep=0)
        self.assertEqual(tick(w), 0)
        self.assertEqual(w["agents"][0]["memory"], [])

    def test_strongest_orders_by_meetings_then_recency(self):
        a = {"memory": [[7, 1, 50, 2, 0, 0], [3, 1, 90, 5, 0, 0], [9, 1, 80, 2, 0, 0]]}
        self.assertEqual([e[0] for e in strongest(a, 2)], [3, 9])


class AgreesWithBruteForce(unittest.TestCase):
    def test_counts_match_an_independent_count(self):
        # Big memory so nothing is ever dropped; then every entry's meeting
        # count must equal a slow all-pairs count of meetings that started.
        w = create_world("42", {"memory_keep": 1000, "history_keep": 0})
        starts, before = {}, set()
        for _ in range(300):
            step(w)
            ag = w["agents"]
            now = set()
            for i, a in enumerate(ag):
                for b in ag[i + 1:]:
                    if abs(a["x"] - b["x"]) <= 1 and abs(a["y"] - b["y"]) <= 1:
                        now.add((min(a["id"], b["id"]), max(a["id"], b["id"])))
            for p in now - before:
                starts[p] = starts.get(p, 0) + 1
            before = now
        checked = 0
        for a in w["agents"]:
            for e in a["memory"]:
                pair = (min(a["id"], e[0]), max(a["id"], e[0]))
                self.assertEqual(e[3], starts.get(pair), pair)
                checked += 1
        self.assertGreater(checked, 500)


class SaveLoad(unittest.TestCase):
    def test_memory_survives_save_load_and_continues_identically(self):
        a, b = create_world("42"), create_world("42")
        for _ in range(250):
            step(a)
            step(b)
        b = world_from_json(world_to_json(b))
        self.assertNotIn("migration_log", b)
        self.assertEqual([x["memory"] for x in a["agents"]], [x["memory"] for x in b["agents"]])
        for _ in range(150):
            step(a)
            step(b)
        self.assertEqual(world_to_json(a), world_to_json(b))


if __name__ == "__main__":
    unittest.main()
