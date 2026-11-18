"""Milestone 3 step 7: fading memory (genesis/memory.py, config memory_fade).

Rule: an agent forgets another agent it has not been within 1 tile of for
MORE than memory_fade ticks. memory_fade = 0 = never fade, which with
memory_keep = 10 must reproduce the step 6 world exactly (frozen in
experiments/baseline/milestone3_family.json, including every memory).
"""
import hashlib
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, load_world, step, world_to_json  # noqa: E402
from genesis.digest import EventDigest, behaviour_digest  # noqa: E402
from genesis.memory import update_memories  # noqa: E402
from genesis.overrides import parse_overrides  # noqa: E402
from genesis.save import NO_FADE_RULES  # noqa: E402
from genesis.world import SAVE_VERSION  # noqa: E402

REF = json.load(open(os.path.join(ROOT, "experiments", "baseline", "milestone3_family.json")))
FIXTURES = os.path.join(ROOT, "tests", "fixtures")


def mem_digest(w):
    m = [[a["id"], a["memory"]] for a in w["agents"]]
    return hashlib.sha256(json.dumps(m).encode()).hexdigest()[:16]


def tiny(fade, keep=10):
    """A hand-made world with two agents; only what update_memories reads."""
    a = {"id": 1, "x": 5, "y": 5, "memory": []}
    b = {"id": 2, "x": 6, "y": 5, "memory": []}
    w = {"tick": 1, "agents": [a, b],
         "config": {"width": 20, "memory_keep": keep, "memory_fade": fade}}
    return w, a, b


class FadeOffIsStepSix(unittest.TestCase):
    def test_fade_zero_keep_ten_reproduces_frozen_world_and_memories(self):
        for seed, ref in REF["short"].items():
            w = create_world(seed, dict(NO_FADE_RULES))
            ed = EventDigest()
            for _ in range(500):
                ed.add(step(w))
            s = w["stats"]
            now = {"alive": len(w["agents"]), "births": s["births"],
                   "starved": s["deaths_starved"], "old_age": s["deaths_old_age"],
                   "gifts": s["gifts"], "behaviour_digest": behaviour_digest(w),
                   "event_digest": ed.hexdigest(), "memory_digest": mem_digest(w)}
            self.assertEqual(now, ref, "seed " + seed)

    def test_v7_save_migrates_keeps_its_rules_and_continues_the_same(self):
        w = load_world(os.path.join(FIXTURES, "save_v7_seed42_t300.json"))
        self.assertEqual(w["version"], SAVE_VERSION)
        self.assertEqual((w["config"]["memory_fade"], w["config"]["memory_keep"]), (0, 10))
        self.assertTrue(any("memory_fade" in line and "old rules" in line
                            for line in w["migration_log"]))
        ed = EventDigest()
        for _ in range(200):
            ed.add(step(w))
        self.assertEqual({"tick": w["tick"], "behaviour_digest": behaviour_digest(w),
                          "event_digest": ed.hexdigest(), "memory_digest": mem_digest(w)},
                         REF["save_v7"])

    def test_saves_from_before_memory_get_the_old_memory_size(self):
        # A v4 save has no memory_keep at all: it must get 10, not today's default.
        w = load_world(os.path.join(FIXTURES, "save_v4_seed42_t300.json"))
        self.assertEqual((w["config"]["memory_fade"], w["config"]["memory_keep"]), (0, 10))


class TheRule(unittest.TestCase):
    def test_forgotten_exactly_when_not_met_for_more_than_fade_ticks(self):
        w, a, b = tiny(fade=5)
        update_memories(w)                      # met at tick 1
        b["x"] = 15                             # walk apart
        for t in range(2, 7):                   # ticks 2..6: 6 - 1 = 5, not more than 5
            w["tick"] = t
            update_memories(w)
            self.assertEqual([e[0] for e in a["memory"]], [2], "tick %d" % t)
        w["tick"] = 7                           # 7 - 1 = 6 > 5: forgotten, both sides
        update_memories(w)
        self.assertEqual((a["memory"], b["memory"]), ([], []))

    def test_meeting_again_in_time_keeps_and_counts_it(self):
        w, a, b = tiny(fade=5)
        update_memories(w)
        b["x"] = 15
        w["tick"] = 4
        update_memories(w)
        b["x"] = 6                              # back next to a at tick 6
        w["tick"] = 6
        update_memories(w)
        self.assertEqual(a["memory"][0][:4], [2, 1, 6, 2])   # first 1, last 6, 2 meetings
        b["x"] = 15
        w["tick"] = 11                          # 11 - 6 = 5: still kept
        update_memories(w)
        self.assertEqual(len(a["memory"]), 1)

    def test_fade_zero_never_forgets(self):
        w, a, b = tiny(fade=0)
        update_memories(w)
        b["x"] = 15
        w["tick"] = 10 ** 6
        update_memories(w)
        self.assertEqual([e[0] for e in a["memory"]], [2])

    def test_a_full_list_still_drops_the_least_met(self):
        # Room for 2; #9 met 7 times, #8 once, both recently enough to be
        # kept by fading. Meeting #2 overflows the list: #8 goes, not #9,
        # and not #2 (never someone it is meeting right now).
        w, a, b = tiny(fade=100, keep=2)
        a["memory"] = [[9, 0, 0, 7, 0, 0, 0, 0], [8, 0, 0, 1, 0, 0, 0, 0]]
        update_memories(w)
        self.assertEqual([e[0] for e in a["memory"]], [9, 2])

    def test_setting_can_be_changed_from_the_command_line(self):
        self.assertEqual(parse_overrides(["memory_fade=150"]), {"memory_fade": 150})
        with self.assertRaises(ValueError):
            parse_overrides(["memory_fade=-1"])


class InTheWorld(unittest.TestCase):
    def test_nobody_remembers_anyone_older_than_the_fade(self):
        w = create_world("7", {"memory_fade": 100, "memory_keep": 20, "history_keep": 0})
        for _ in range(400):
            step(w)
            oldest = min((e[2] for a in w["agents"] for e in a["memory"]), default=w["tick"])
            self.assertGreaterEqual(oldest, w["tick"] - 100)

    def test_same_seed_same_world_with_fading(self):
        cfg = {"memory_fade": 150, "memory_keep": 20}
        x, y = create_world("9", cfg), create_world("9", cfg)
        for _ in range(300):
            step(x)
            step(y)
        self.assertEqual(world_to_json(x), world_to_json(y))


if __name__ == "__main__":
    unittest.main()
