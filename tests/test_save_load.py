"""Saving then loading must give back exactly the same world.

Run all tests with:   python3 -m unittest discover -s tests -v
"""

import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import (create_world, fingerprint, load_world, run,  # noqa: E402
                     save_world, world_from_json, world_to_json)


class SaveLoad(unittest.TestCase):
    def test_save_then_load_gives_the_same_state(self):
        world = create_world(42)
        run(world, 250)
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "test_save.json")
            save_world(world, path)
            loaded = load_world(path)
        self.assertEqual(loaded, world)
        self.assertEqual(fingerprint(loaded), fingerprint(world))

    def test_loaded_world_continues_exactly_like_the_original(self):
        """The stronger check: after loading, the future is identical too.
        This only works because the save includes where the dice are."""
        original = create_world("genesis")
        run(original, 200)
        loaded = world_from_json(world_to_json(original))

        events_original = run(original, 300)
        events_loaded = run(loaded, 300)

        self.assertEqual(events_loaded, events_original)
        self.assertEqual(loaded, original)

    def test_saving_does_not_change_the_world(self):
        world = create_world(9)
        run(world, 100)
        before = fingerprint(world)
        world_to_json(world)
        self.assertEqual(fingerprint(world), before)

    def test_a_broken_save_is_rejected_clearly(self):
        with self.assertRaises(ValueError):
            world_from_json('{"version": 999}')
        with self.assertRaises(ValueError):
            world_from_json("not a save file")


if __name__ == "__main__":
    unittest.main()
