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


class OldAndOddSaves(unittest.TestCase):
    def _v1_text(self, mutate=None):
        world = create_world(5)
        run(world, 60)
        world["version"] = 1
        if mutate:
            mutate(world)
        return world_to_json(world)

    def test_old_format_save_loads_and_continues(self):
        loaded = world_from_json(self._v1_text())
        self.assertEqual(loaded["version"], 3)   # migrated 1 -> 2 -> 3
        self.assertNotIn("migration_log", loaded)   # nothing needed fixing
        reference = create_world(5)
        run(reference, 60)
        run(reference, 100)
        run(loaded, 100)
        self.assertEqual(loaded["agents"], reference["agents"])

    def test_missing_config_key_gets_default_and_is_logged(self):
        def drop(w):
            del w["config"]["vision"]
            del w["config"]["regrow_per_tick"]
            del w["stats"]["births"]
            del w["agents"][0]["cooldown"]
        loaded = world_from_json(self._v1_text(drop))
        self.assertEqual(loaded["config"]["vision"], 4)
        self.assertEqual(loaded["stats"]["births"], 0)
        self.assertEqual(loaded["agents"][0]["cooldown"], 0)
        log = " ".join(loaded["migration_log"])
        self.assertIn("config.vision", log)
        self.assertIn("config.regrow_per_tick", log)
        run(loaded, 20)   # must not crash

    def test_saved_values_beat_defaults(self):
        def change(w):
            w["config"]["vision"] = 7
        loaded = world_from_json(self._v1_text(change))
        self.assertEqual(loaded["config"]["vision"], 7)

    def test_unknown_extra_keys_are_kept(self):
        def extra(w):
            w["future_thing"] = {"a": [1, 2]}
            w["config"]["new_setting"] = 9
            w["agents"][0]["mood"] = "calm"
        loaded = world_from_json(self._v1_text(extra))
        self.assertEqual(loaded["future_thing"], {"a": [1, 2]})
        self.assertEqual(loaded["config"]["new_setting"], 9)
        self.assertEqual(loaded["agents"][0]["mood"], "calm")
        again = world_from_json(world_to_json(loaded))
        self.assertEqual(again["future_thing"], {"a": [1, 2]})

    def test_newer_version_and_missing_essentials_are_rejected(self):
        with self.assertRaises(ValueError):
            world_from_json('{"version": 4}')     # newer than this program
        with self.assertRaises(ValueError):
            world_from_json('{"version": 1, "seed": "1"}')


class MilestoneTwoMigration(unittest.TestCase):
    def test_v2_fixture_migrates_to_v3_and_keeps_its_old_rules(self):
        from genesis import load_world
        w = load_world(os.path.join(ROOT, "tests", "fixtures", "save_v2_seed42_t300.json"))
        self.assertEqual(w["version"], 3)
        self.assertEqual(w["config"]["rest_below"], 0)            # nobody rests
        self.assertEqual(w["config"]["trait_mutation"], 0)        # newborns stay 50
        self.assertTrue(all(a["traits"] == {"curiosity": 50, "industriousness": 50}
                            and a["needs"] == {"rest": 100} and a["tire_acc"] == 0
                            for a in w["agents"]))
        self.assertTrue(any("version 2 -> 3" in line for line in w["migration_log"]))
        self.assertTrue(any("keeps its old rules" in line for line in w["migration_log"]))


if __name__ == "__main__":
    unittest.main()
