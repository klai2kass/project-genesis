"""Real trait creation and inheritance inside real worlds."""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step, world_from_json, world_to_json  # noqa: E402
from genesis.config import DEFAULT_CONFIG  # noqa: E402
from genesis.digest import EventDigest  # noqa: E402
from genesis.save import MILESTONE1_RULES  # noqa: E402
from genesis.traits import child_traits  # noqa: E402

NAMES = ("curiosity", "industriousness")


class Founders(unittest.TestCase):
    def test_golden_founders_in_a_real_world(self):
        w = create_world("42")
        by_id = {a["id"]: a["traits"] for a in w["agents"]}
        self.assertEqual(by_id[1], {"curiosity": 60, "industriousness": 53})
        self.assertEqual(by_id[2], {"curiosity": 42, "industriousness": 49})

    def test_founders_are_40_to_60_and_varied(self):
        for seed in ("42", "1", "2"):
            values = [a["traits"][n] for a in create_world(seed)["agents"] for n in NAMES]
            self.assertTrue(all(40 <= v <= 60 for v in values), seed)
            self.assertGreater(len(set(values)), 10, seed)

    def test_traits_do_not_move_the_main_dice(self):
        # Founder traits from 40..60 or all 50: everything else is identical.
        a = create_world("42")
        b = create_world("42", dict(MILESTONE1_RULES))
        self.assertEqual(a["rng"], b["rng"])
        self.assertEqual(a["terrain"], b["terrain"])
        self.assertEqual(a["food"], b["food"])
        strip = lambda w: [{k: v for k, v in x.items() if k != "traits"} for x in w["agents"]]
        self.assertEqual(strip(a), strip(b))
        self.assertTrue(all(x["traits"] == {"curiosity": 50, "industriousness": 50}
                            for x in b["agents"]))


class Inheritance(unittest.TestCase):
    def test_children_are_within_5_of_their_parent(self):
        w = create_world("42", {"history_keep": 0})
        known = {a["id"]: a["traits"] for a in w["agents"]}
        children = 0
        for _ in range(700):
            step(w)
            for a in w["agents"]:
                if a["id"] not in known:
                    parent = known[a["parent"]]
                    for n in NAMES:
                        self.assertLessEqual(abs(a["traits"][n] - parent[n]), 5)
                        self.assertTrue(0 <= a["traits"][n] <= 100)
                    self.assertEqual(a["traits"],
                                     child_traits(w["seed"], a["id"], parent, w["config"]))
                    known[a["id"]] = a["traits"]
                    children += 1
        self.assertGreater(children, 50)

    def test_clamped_at_0_and_100(self):
        cfg = dict(DEFAULT_CONFIG, trait_mutation=20)
        for cid in range(1, 300):
            lo = child_traits("7", cid, {"curiosity": 0, "industriousness": 0}, cfg)
            hi = child_traits("7", cid, {"curiosity": 100, "industriousness": 100}, cfg)
            self.assertTrue(all(0 <= v <= 20 for v in lo.values()))
            self.assertTrue(all(80 <= v <= 100 for v in hi.values()))

    def test_mutations_of_the_two_traits_are_independent(self):
        same = sum(1 for cid in range(1, 2001)
                   if len(set(t - 50 for t in child_traits(
                       "9", cid, {"curiosity": 50, "industriousness": 50},
                       DEFAULT_CONFIG).values())) == 1)
        self.assertLess(same, 2000 * 0.2)   # 1 in 11 expected by chance


class SaveLoadWithNewRules(unittest.TestCase):
    def test_save_load_continue_equals_uninterrupted(self):
        a = create_world("42")
        b = create_world("42")
        for _ in range(400):            # long enough that agents rest and tire
            step(a)
            step(b)
        self.assertTrue(any(x["resting"] or x["tire_acc"] or x["drain_acc"]
                            for x in b["agents"]))
        b = world_from_json(world_to_json(b))
        self.assertEqual(b["version"], 4)
        self.assertNotIn("migration_log", b)
        da, db = EventDigest(), EventDigest()
        for _ in range(300):
            da.add(step(a))
            db.add(step(b))
        self.assertEqual(da.hexdigest(), db.hexdigest())
        self.assertEqual(a["agents"], b["agents"])

    def test_die_events_carry_traits_and_needs(self):
        w = create_world("1", {"history_keep": 0})
        for _ in range(600):
            for e in step(w):
                if e["action"] == "die":
                    self.assertEqual(set(e["traits"]), set(NAMES))
                    self.assertIn("rest", e["needs"])
                    return
        self.fail("nobody died in 600 ticks")


if __name__ == "__main__":
    unittest.main()
