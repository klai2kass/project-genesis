"""Movement around water, on tiny hand-made worlds.

Run all tests with:   python3 -m unittest discover -s tests -v
"""

import copy
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step  # noqa: E402
from genesis.rng import Rng  # noqa: E402
from genesis.world import FOREST, GRASS, WATER, make_agent  # noqa: E402
from genesis.agents import decide  # noqa: E402


def tiny_world(width, height, water=(), food=(), agent_at=(1, 1), energy=60):
    """All grass, no regrowth, one agent. water/food are lists of (x, y)."""
    w = create_world(1, {"width": width, "height": height, "start_agents": 0,
                         "regrow_per_tick": 0, "vision": 6})
    w["terrain"] = [GRASS] * (width * height)
    w["food"] = [0] * (width * height)
    for x, y in water:
        w["terrain"][y * width + x] = WATER
    for x, y in food:
        w["food"][y * width + x] = 2
    rng = Rng(5)
    agent = make_agent(1, agent_at[0], agent_at[1], energy, 100, rng, w["config"])
    agent["max_age"] = 10 ** 6
    agent["cooldown"] = 10 ** 6
    agent["heading"] = 2
    w["agents"] = [agent]
    w["next_id"] = 2
    return w


def walk(world, ticks):
    path = []
    for _ in range(ticks):
        step(world)
        a = world["agents"][0]
        path.append((a["x"], a["y"]))
    return path


class Movement(unittest.TestCase):
    def test_reachable_food_is_reached_directly(self):
        w = tiny_world(11, 3, food=[(7, 1)], agent_at=(1, 1))
        path = walk(w, 6)           # 6 steps along the row
        self.assertEqual(path[-1], (7, 1))
        step(w)                     # next tick it gathers
        self.assertEqual(w["agents"][0]["food"], 1)

    def test_walks_around_a_wall_of_water(self):
        # A wall at x=4 covering y=0..3; the gap is at y=4.
        wall = [(4, y) for y in range(0, 4)]
        w = tiny_world(9, 5, water=wall, food=[(6, 1)], agent_at=(2, 1))
        path = walk(w, 14)
        self.assertIn((6, 1), path)
        self.assertEqual(w["agents"][0]["food"] >= 1 or (6, 1) in path, True)
        for x, y in path:
            self.assertNotEqual(w["terrain"][y * 9 + x], WATER)

    def test_unreachable_food_is_ignored_not_dithered_over(self):
        # Food on an island at (6,2), ringed by water. Agent cannot reach it.
        ring = [(x, y) for x in range(5, 8) for y in range(1, 4) if (x, y) != (6, 2)]
        w = tiny_world(11, 5, water=ring, food=[(6, 2)], agent_at=(1, 2))
        walk(w, 12)
        a = w["agents"][0]
        self.assertEqual(a["target"], None)
        # It must never lock on to that food, however long it waits.
        for _ in range(20):
            step(w)
            self.assertEqual(w["agents"][0]["target"], None)

    def test_no_endless_back_and_forth_in_front_of_water(self):
        ring = [(x, y) for x in range(5, 8) for y in range(1, 4) if (x, y) != (6, 2)]
        w = tiny_world(11, 5, water=ring, food=[(6, 2)], agent_at=(1, 2),
                       energy=100)
        path = walk(w, 60)
        # Count immediate returns (A -> B -> A). A dithering agent does this
        # almost every tick; a walking/wandering one only now and then.
        returns = sum(1 for i in range(2, len(path)) if path[i] == path[i - 2])
        self.assertLess(returns, 20)

    def test_keeps_its_target_instead_of_flipping(self):
        # Two foods at equal distance on both sides.
        w = tiny_world(13, 3, food=[(2, 1), (10, 1)], agent_at=(6, 1))
        first = None
        for _ in range(3):
            step(w)
            t = w["agents"][0]["target"]
            if first is None:
                first = t
            self.assertEqual(t, first)

    def test_repeated_decisions_are_identical(self):
        w = tiny_world(9, 5, water=[(4, y) for y in range(4)], food=[(6, 1)],
                       agent_at=(2, 1))
        a, b = copy.deepcopy(w), copy.deepcopy(w)
        for _ in range(15):
            step(a)
            step(b)
        self.assertEqual(a, b)

    def test_deciding_never_changes_the_world(self):
        w = tiny_world(9, 5, food=[(6, 1)], agent_at=(2, 1))
        before_world = copy.deepcopy(w["food"]), copy.deepcopy(w["terrain"])
        decide(w, w["agents"][0], Rng(3))
        self.assertEqual((w["food"], w["terrain"]), before_world)


if __name__ == "__main__":
    unittest.main()
