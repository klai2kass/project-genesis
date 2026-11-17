"""--summary must report only real, consistent numbers.

Run all tests with:   python3 -m unittest discover -s tests -v
"""

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step  # noqa: E402
from genesis.summary import RunRecorder  # noqa: E402


def record(seed, ticks):
    world = create_world(seed)
    rec = RunRecorder(world)
    for _ in range(ticks):
        rec.update(world, step(world))
    return world, rec


class Summary(unittest.TestCase):
    def test_numbers_match_the_world_counters(self):
        world, rec = record(42, 400)
        stats = world["stats"]
        self.assertEqual(rec.births, stats["births"])
        self.assertEqual(rec.deaths["starved"], stats["deaths_starved"])
        self.assertEqual(rec.deaths["old age"], stats["deaths_old_age"])

    def test_people_are_conserved(self):
        world, rec = record(7, 400)
        self.assertEqual(rec.start_pop + rec.births - sum(rec.deaths.values()),
                         len(world["agents"]))
        self.assertEqual(len(rec.pop), 401)

    def test_report_has_the_real_numbers_and_a_not_tracked_list(self):
        world, rec = record(42, 300)
        text = rec.report(world)
        self.assertIn("seed                 42", text)
        self.assertIn("births               %d" % world["stats"]["births"], text)
        self.assertIn("Not tracked", text)
        self.assertIn("average age at death", text)

    def test_zero_ticks_and_no_deaths_do_not_crash(self):
        world, rec = record(1, 0)
        self.assertIn("n/a", rec.report(world))

    def test_command_line_flag(self):
        out = subprocess.run(
            [sys.executable, os.path.join(ROOT, "run_headless.py"), "--seed", "42",
             "--ticks", "100", "--every", "0", "--summary"],
            capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("RUN SUMMARY", out.stdout)
        self.assertIn("fingerprint=", out.stdout)


if __name__ == "__main__":
    unittest.main()
