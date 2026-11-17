"""Pause, step, speed, new world, save and load, tested without a browser.

These drive the same `Game` object the web page talks to.

Run all tests with:   python3 -m unittest discover -s tests -v
"""

import json
import os
import sys
import tempfile
import threading
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import server  # noqa: E402
from genesis import create_world, fingerprint, run  # noqa: E402


class Controls(unittest.TestCase):
    def setUp(self):
        # Send saves to a throwaway folder so tests never touch real saves.
        self.folder = tempfile.TemporaryDirectory()
        self.real_saves_dir = server.SAVES_DIR
        server.SAVES_DIR = self.folder.name
        self.game = server.Game("42")
        self.game.paused = True

    def tearDown(self):
        self.game.running = False
        server.SAVES_DIR = self.real_saves_dir
        self.folder.cleanup()

    def test_step_moves_exactly_one_tick(self):
        self.game.control({"action": "step"})
        self.game.control({"action": "step"})
        self.assertEqual(self.game.world["tick"], 2)
        self.assertTrue(self.game.paused)

    def test_stepping_matches_a_headless_run(self):
        for _ in range(30):
            self.game.control({"action": "step"})
        headless = create_world("42")
        run(headless, 30)
        self.assertEqual(fingerprint(self.game.world), fingerprint(headless))

    def test_pause_stops_time_and_play_restarts_it(self):
        self.game.control({"action": "speed", "value": 20})
        threading.Thread(target=self.game.loop, daemon=True).start()

        self.game.control({"action": "play"})
        time.sleep(0.4)
        self.game.control({"action": "pause"})
        tick_when_paused = self.game.world["tick"]
        self.assertGreater(tick_when_paused, 0, "time did not move while playing")

        time.sleep(0.3)
        self.assertEqual(self.game.world["tick"], tick_when_paused,
                         "time moved while paused")

    def test_speed_accepts_only_known_values(self):
        for speed in server.ALLOWED_SPEEDS:
            self.game.control({"action": "speed", "value": speed})
            self.assertEqual(self.game.speed, speed)
        with self.assertRaises(ValueError):
            self.game.control({"action": "speed", "value": 1000})

    def test_new_world_uses_the_seed(self):
        self.game.control({"action": "step"})
        self.game.control({"action": "new", "seed": "banana"})
        self.assertEqual(self.game.world, create_world("banana"))

    def test_save_then_load_brings_back_the_same_world(self):
        for _ in range(25):
            self.game.control({"action": "step"})
        saved = fingerprint(self.game.world)
        self.game.control({"action": "save", "name": "test-save"})
        self.assertEqual(server.Game.list_saves(), ["test-save"])

        for _ in range(10):
            self.game.control({"action": "step"})
        self.assertNotEqual(fingerprint(self.game.world), saved)

        self.game.control({"action": "load", "name": "test-save"})
        self.assertEqual(fingerprint(self.game.world), saved)
        self.assertTrue(self.game.paused, "a loaded world should start paused")

    def test_load_message_says_tick_and_seed_for_the_page(self):
        for _ in range(7):
            self.game.control({"action": "step"})
        self.game.control({"action": "save", "name": "msg"})
        text = self.game.control({"action": "load", "name": "msg"})
        self.assertIn("tick 7", text)
        self.assertIn("seed 42", text)

    def test_agent_trail_is_still_there_after_loading_a_save(self):
        for _ in range(30):
            self.game.control({"action": "step"})
        self.game.control({"action": "save", "name": "trail"})
        before = json.loads(self.game.snapshot(since=0, feed="all", agent_id=1))
        self.game.control({"action": "new", "seed": "other"})
        self.game.control({"action": "load", "name": "trail"})
        after = json.loads(self.game.snapshot(since=0, feed="all", agent_id=1))
        self.assertEqual(len(after["selected"]["trail"]), 20)
        self.assertEqual(after["selected"]["trail"], before["selected"]["trail"])

    def test_broken_saves_fail_with_a_plain_error_and_keep_the_world(self):
        before = fingerprint(self.game.world)
        bad = {"not json": "{oops", "empty": "{}",
               "damaged": '{"version": 2, "seed": "1", "tick": 0, "rng": 1, '
                          '"config": 5, "terrain": [], "food": [], "agents": []}'}
        for name, text in bad.items():
            with open(os.path.join(self.folder.name, name.replace(" ", "-")
                                   + ".json"), "w") as f:
                f.write(text)
            with self.assertRaises(ValueError, msg=name):
                self.game.control({"action": "load", "name": name.replace(" ", "-")})
        self.assertEqual(fingerprint(self.game.world), before)

    def test_bad_save_names_are_refused(self):
        for name in ("../escape", "a/b", "", "x" * 41, None):
            with self.assertRaises(ValueError):
                self.game.control({"action": "save", "name": name})
        with self.assertRaises(ValueError):
            self.game.control({"action": "load", "name": "does-not-exist"})
        self.assertEqual(os.listdir(self.folder.name), [])

    def test_the_page_gets_the_selected_agents_decisions(self):
        for _ in range(5):
            self.game.control({"action": "step"})
        state = json.loads(self.game.snapshot(since=0, feed="all", agent_id=1))
        self.assertEqual(state["tick"], 5)
        trail = state["selected"]["trail"]
        self.assertEqual(len(trail), 5)
        self.assertTrue(trail[-1]["need"])
        self.assertTrue(trail[-1]["options"])


if __name__ == "__main__":
    unittest.main()
