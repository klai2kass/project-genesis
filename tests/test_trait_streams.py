"""Design check for the planned per-agent trait dice (docs/MILESTONE2_V2.md, section 2a).

These tests call the real genesis/traits.py. The golden numbers were fixed
before the module existed (from the documented rule), and the module
reproduces them: the derivation is deterministic, independent of the main
dice, unaffected by save/load, and well spread.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step, world_from_json, world_to_json  # noqa: E402
from genesis import traits  # noqa: E402
from genesis.config import DEFAULT_CONFIG  # noqa: E402
from genesis.rng import seed_to_state  # noqa: E402
from genesis.traits import trait_stream  # noqa: E402


def founder_traits(seed, agent_id):
    """The real genesis.traits code, with the default founder range 40..60."""
    t = traits.founder_traits(seed, agent_id, DEFAULT_CONFIG)
    return t["curiosity"], t["industriousness"]


class TraitStreams(unittest.TestCase):
    def test_golden_values(self):
        # Fixed numbers: a changed rule or a changed Rng breaks these on purpose.
        self.assertEqual(founder_traits("42", 1), (60, 53))
        self.assertEqual(founder_traits("42", 2), (42, 49))
        self.assertEqual(founder_traits("1", 1), (54, 44))
        self.assertEqual(founder_traits("42", 51), (53, 43))
        self.assertEqual(trait_stream("42", 1).between(-5, 5), 5)
        self.assertEqual(trait_stream("42", 2).between(-5, 5), -4)

    def test_depends_only_on_seed_and_id(self):
        self.assertEqual(founder_traits("42", 7), founder_traits(42, 7))   # 42 and "42" are one seed
        self.assertNotEqual([founder_traits("42", i) for i in range(1, 30)],
                            [founder_traits("43", i) for i in range(1, 30)])
        self.assertNotEqual(founder_traits("42", 1), founder_traits("42", 2))

    def test_main_dice_cannot_change_trait_values(self):
        # Run the real world (it uses the main dice heavily); the trait values
        # derived afterwards for the same ids are identical to those derived before.
        before = [founder_traits("42", i) for i in range(1, 200)]
        world = create_world("42")
        for _ in range(100):
            step(world)
        after = [founder_traits(world["seed"], i) for i in range(1, 200)]
        self.assertEqual(before, after)

    def test_survives_save_and_load(self):
        world = create_world("42")
        for _ in range(50):
            step(world)
        loaded = world_from_json(world_to_json(world))
        self.assertEqual(loaded["seed"], world["seed"])      # the seed text is saved
        newest = max(a["id"] for a in world["agents"])       # ids are saved too
        self.assertEqual(founder_traits(loaded["seed"], newest),
                         founder_traits(world["seed"], newest))
        # No generator state has to be saved: the stream is made fresh from
        # (seed, id), used for exactly two draws, and thrown away.

    def test_ids_never_collide_and_draws_are_spread(self):
        for seed in ("42", "1", "2", "3", "4"):
            states = {seed_to_state("%s|traits|%d" % (seed, i)) for i in range(1, 5001)}
            self.assertEqual(len(states), 5000, "two agents would share a stream")
        buckets = [0] * 10
        for i in range(1, 3001):
            buckets[int(trait_stream("42", i).random() * 10)] += 1
        for count in buckets:                                # expected 300 each
            self.assertTrue(210 <= count <= 390, buckets)


if __name__ == "__main__":
    unittest.main()
