"""Every decision must explain itself: need, options considered, reason.

Run all tests with:   python3 -m unittest discover -s tests -v
"""

import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import (create_world, format_agent_history,  # noqa: E402
                     format_decision, run)

DECISIONS = ("eat", "reproduce", "gather", "move", "rest")


class WhyLog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world = create_world(11)
        cls.events = run(cls.world, 400)
        cls.decisions = [e for e in cls.events if e["action"] in DECISIONS]

    def test_every_decision_records_need_options_and_reason(self):
        self.assertTrue(self.decisions)
        for event in self.decisions:
            self.assertTrue(event["need"].strip(), "no need: %r" % event)
            self.assertTrue(event["why"].strip(), "no reason: %r" % event)
            self.assertGreaterEqual(len(event["options"]), 4)
            for option in event["options"]:
                self.assertIn(option["action"], DECISIONS)
                self.assertIsInstance(option["ok"], bool)
                self.assertTrue(option["note"].strip())

    def test_the_chosen_action_is_the_first_option_that_fits(self):
        """The rules are tried in order, so everything listed before the
        chosen option must have been ruled out."""
        for event in self.decisions:
            fitting = [o["action"] for o in event["options"] if o["ok"]]
            self.assertTrue(fitting, "nothing fitted: %r" % event)
            self.assertEqual(fitting[0], event["action"], "%r" % event)

    def test_births_and_deaths_have_a_reason_too(self):
        others = [e for e in self.events if e["action"] in ("born", "die")]
        self.assertTrue(others)
        for event in others:
            self.assertTrue(event["why"].strip())

    def test_a_decision_prints_as_readable_text(self):
        text = format_decision(self.decisions[0])
        for word in ("need", "options", "why", "CHOSEN"):
            self.assertIn(word, text)

    def test_history_of_one_agent(self):
        mine = [e for e in self.events if e["agent"] == 1][-3:]
        text = format_agent_history(1, mine, self.world)
        self.assertIn("Agent #1", text)
        self.assertEqual(text.count("  why  "), len(mine))
        self.assertIn("no agent #99999", format_agent_history(99999, [], self.world))

    def test_why_command_shows_the_last_decisions_of_one_agent(self):
        def why(*extra):
            return subprocess.run(
                [sys.executable, "why.py", "--seed", "42", "--ticks", "60"] + list(extra),
                cwd=ROOT, capture_output=True, text=True, check=True).stdout

        output = why("--agent", "1", "--last", "3")
        self.assertIn("Agent #1", output)
        self.assertEqual(output.count("  why  "), 3)
        self.assertEqual(output.count("CHOSEN"), 3)
        self.assertEqual(output, why("--agent", "1", "--last", "3"),
                         "the same command must print the same story")
        self.assertIn("agents alive", why())   # no --agent: lists who is alive


if __name__ == "__main__":
    unittest.main()
