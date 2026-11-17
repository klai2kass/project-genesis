"""--set name=value: valid, invalid and repeated overrides.

Run all tests with:   python3 -m unittest discover -s tests -v
"""

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, run, world_from_json, world_to_json  # noqa: E402
from genesis.config import DEFAULT_CONFIG  # noqa: E402
from genesis.overrides import (RULES, apply_to_loaded, build_new_config,  # noqa: E402
                               parse_overrides)


class Overrides(unittest.TestCase):
    def test_every_setting_has_a_rule(self):
        self.assertEqual(sorted(RULES), sorted(DEFAULT_CONFIG))

    def test_valid_values(self):
        got = parse_overrides(["regrow_per_tick=6", "water_share=0.1",
                               "food_cap=0,2,5"])
        self.assertEqual(got, {"regrow_per_tick": 6, "water_share": 0.1,
                               "food_cap": [0, 2, 5]})

    def test_repeated_names_last_wins_and_different_names_combine(self):
        got = parse_overrides(["vision=3", "regrow_per_tick=9", "vision=5"])
        self.assertEqual(got, {"vision": 5, "regrow_per_tick": 9})

    def test_unknown_name_lists_valid_names(self):
        with self.assertRaises(ValueError) as cm:
            parse_overrides(["regrow=6"])
        self.assertIn("regrow_per_tick", str(cm.exception))
        self.assertIn("vision", str(cm.exception))

    def test_bad_type_range_and_shape(self):
        for bad in ["vision=abc", "vision=2.5", "vision=0", "vision=999",
                    "water_share=2", "water_share=nan", "food_cap=1,2",
                    "food_cap=1,2,x", "novalue"]:
            with self.assertRaises(ValueError, msg=bad):
                parse_overrides([bad])

    def test_combined_rules(self):
        with self.assertRaises(ValueError):
            build_new_config(parse_overrides(["water_share=0.8",
                                              "forest_share=0.5"]))

    def test_override_beats_default_and_defaults_are_untouched(self):
        before = dict(DEFAULT_CONFIG)
        world = create_world(1, build_new_config(parse_overrides(["vision=6"])))
        self.assertEqual(world["config"]["vision"], 6)
        self.assertEqual(DEFAULT_CONFIG, before)

    def test_override_changes_the_outcome_and_is_deterministic(self):
        def go(extra):
            w = create_world(42, build_new_config(parse_overrides(extra)))
            run(w, 300)
            return len(w["agents"]), w["stats"]["births"]
        self.assertEqual(go(["regrow_per_tick=8"]), go(["regrow_per_tick=8"]))
        self.assertNotEqual(go(["regrow_per_tick=8"]), go([]))

    def test_loaded_world_accepts_runtime_setting_only(self):
        world = world_from_json(world_to_json(create_world(3)))
        apply_to_loaded(world, parse_overrides(["regrow_per_tick=7"]))
        self.assertEqual(world["config"]["regrow_per_tick"], 7)
        with self.assertRaises(ValueError):
            apply_to_loaded(world, parse_overrides(["width=30"]))

    def test_command_line_gives_plain_error(self):
        out = subprocess.run(
            [sys.executable, os.path.join(ROOT, "run_headless.py"),
             "--ticks", "1", "--set", "nope=1"],
            capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("Valid names", out.stderr)
        self.assertNotIn("Traceback", out.stderr)

    def test_command_line_override_works_for_both_tools(self):
        for script, extra in (("run_headless.py", ["--every", "0"]),
                              ("why.py", [])):
            out = subprocess.run(
                [sys.executable, os.path.join(ROOT, script), "--ticks", "5",
                 "--set", "regrow_per_tick=6", "--set", "vision=5"] + extra,
                capture_output=True, text=True)
            self.assertEqual(out.returncode, 0, out.stderr)


if __name__ == "__main__":
    unittest.main()
