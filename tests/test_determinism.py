"""Same seed must always give the same world.

Run all tests with:   python3 -m unittest discover -s tests -v
"""

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, fingerprint, run  # noqa: E402


class SameSeedSameResult(unittest.TestCase):
    def test_same_seed_gives_identical_world_and_events(self):
        world_a = create_world(42)
        world_b = create_world(42)
        self.assertEqual(world_a, world_b, "worlds differ before any tick")

        events_a = run(world_a, 400)
        events_b = run(world_b, 400)

        self.assertEqual(events_a, events_b, "the decision logs differ")
        self.assertEqual(world_a, world_b, "the final worlds differ")
        self.assertEqual(fingerprint(world_a), fingerprint(world_b))

    def test_different_seeds_give_different_worlds(self):
        world_a = create_world(1)
        world_b = create_world(2)
        run(world_a, 50)
        run(world_b, 50)
        self.assertNotEqual(fingerprint(world_a), fingerprint(world_b))

    def test_number_seed_and_text_seed_match(self):
        self.assertEqual(create_world(7), create_world("7"))

    def test_same_result_in_a_fresh_python_process(self):
        """Python scrambles some internals on every start (hash randomisation).
        The sim must not depend on that, so two separate runs must agree."""
        def fingerprint_from_new_process(hash_seed):
            env = dict(os.environ, PYTHONHASHSEED=hash_seed)
            output = subprocess.run(
                [sys.executable, "run_headless.py", "--seed", "42",
                 "--ticks", "200", "--every", "0"],
                cwd=ROOT, env=env, capture_output=True, text=True, check=True,
            ).stdout
            return output.strip().split("fingerprint=")[-1]

        self.assertEqual(fingerprint_from_new_process("1"),
                         fingerprint_from_new_process("999"))


class WorldRules(unittest.TestCase):
    def test_every_decision_has_a_why(self):
        world = create_world(3)
        events = run(world, 300)
        self.assertTrue(events)
        seen = set()
        for event in events:
            seen.add(event["action"])
            self.assertTrue(event["why"].strip(),
                            "event without a why: %r" % event)
        # All the Milestone 1 behaviours actually happen.
        for action in ("eat", "move", "gather", "reproduce", "born", "die"):
            self.assertIn(action, seen)
        for agent in world["agents"]:
            self.assertTrue(agent["last_why"].strip())

    def test_world_stays_within_its_rules(self):
        world = create_world(5)
        cfg = world["config"]
        self.assertEqual(len(world["agents"]), cfg["start_agents"])
        for _ in range(300):
            run(world, 1)
            for i, amount in enumerate(world["food"]):
                self.assertTrue(0 <= amount <= cfg["food_cap"][world["terrain"][i]])
            for agent in world["agents"]:
                self.assertTrue(0 < agent["energy"] <= cfg["max_energy"])
                self.assertTrue(0 <= agent["food"] <= cfg["carry_max"])
                tile = agent["y"] * cfg["width"] + agent["x"]
                self.assertNotEqual(world["terrain"][tile], 0, "agent in water")
        ids = [agent["id"] for agent in world["agents"]]
        self.assertEqual(len(ids), len(set(ids)), "two agents share an id")

    def test_population_survives(self):
        world = create_world(1)
        run(world, 1500)
        self.assertGreater(len(world["agents"]), 10)


if __name__ == "__main__":
    unittest.main()
