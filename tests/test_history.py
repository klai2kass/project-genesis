"""Agent decision history is stored in the world, so saves keep it.

Run all tests with:   python3 -m unittest discover -s tests -v
"""

import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import (create_world, run, step, world_from_json,  # noqa: E402
                     world_to_json)
from genesis.history import events_for  # noqa: E402


def lived_world(ticks=400, config=None):
    w = create_world(42, config)
    run(w, ticks)
    return w


class History(unittest.TestCase):
    def test_history_survives_save_and_load(self):
        w = lived_world()
        self.assertTrue(w["history"])
        loaded = world_from_json(world_to_json(w))
        self.assertEqual(loaded["history"], w["history"])
        self.assertEqual(loaded["history_dead"], w["history_dead"])

    def test_history_belongs_to_the_right_agent(self):
        w = lived_world()
        for agent in w["agents"]:
            events = events_for(w, agent["id"])
            self.assertTrue(events)
            last = events[-1]
            # The newest record is that agent's own latest decision.
            self.assertEqual(last["tick"], w["tick"])
            self.assertEqual(last["agent"], agent["id"])
            self.assertEqual((last["x"], last["y"]), (agent["x"], agent["y"]))
            self.assertEqual(last["action"], agent["last_action"])
            self.assertEqual(last["why"], agent["last_why"])
            ticks = [e["tick"] for e in events]
            self.assertEqual(ticks, sorted(ticks))
            self.assertEqual(len(set(ticks)), len(ticks))

    def test_two_agents_do_not_share_records(self):
        w = lived_world(150)
        a, b = w["agents"][0]["id"], w["agents"][1]["id"]
        # A record is always an event of that agent: compare with the live feed.
        w2 = create_world(42)
        mine = {a: [], b: []}
        for _ in range(150):
            for e in step(w2):
                if e["agent"] in mine:
                    mine[e["agent"]].append(e)
        for agent_id in (a, b):
            kept = events_for(w, agent_id)
            expected = mine[agent_id][-len(kept):]
            self.assertEqual([(e["tick"], e["action"], e["why"]) for e in kept],
                             [(e["tick"], e["action"], e["why"]) for e in expected])
            self.assertEqual([e["options"] for e in kept],
                             [e["options"] for e in expected])

    def test_dead_agents_history_is_kept_and_ends_with_death(self):
        w = lived_world(500)
        self.assertTrue(w["history_dead"])
        for key in w["history_dead"]:
            events = events_for(w, int(key))
            self.assertTrue(events)
            self.assertEqual(events[-1]["action"], "die")
        loaded = world_from_json(world_to_json(w))
        self.assertEqual(loaded["history_dead"], w["history_dead"])
        self.assertEqual(events_for(loaded, int(w["history_dead"][0])),
                         events_for(w, int(w["history_dead"][0])))

    def test_limits_are_respected(self):
        w = lived_world(600, {"history_keep": 5, "dead_history_keep": 3})
        self.assertTrue(all(len(r) <= 5 for r in w["history"].values()))
        self.assertLessEqual(len(w["history_dead"]), 3)
        alive = set(str(a["id"]) for a in w["agents"])
        self.assertEqual(set(w["history"]), alive | set(w["history_dead"]))

    def test_old_save_without_history_loads_and_starts_remembering(self):
        w = lived_world(120)
        data = json.loads(world_to_json(w))
        del data["history"]
        del data["history_dead"]
        del data["config"]["history_keep"]
        del data["config"]["dead_history_keep"]
        data["version"] = 1
        loaded = world_from_json(json.dumps(data))
        self.assertEqual(loaded["history"], {})
        self.assertIn("history missing", " ".join(loaded["migration_log"]))
        run(loaded, 5)
        self.assertEqual(len(events_for(loaded, loaded["agents"][0]["id"])), 5)

    def test_loaded_world_still_continues_identically(self):
        a = lived_world(200)
        b = world_from_json(world_to_json(a))
        run(a, 150)
        run(b, 150)
        self.assertEqual(a, b)

    def test_history_does_not_change_behaviour(self):
        on = lived_world(300)
        off = lived_world(300, {"history_keep": 0})
        self.assertEqual(on["agents"], off["agents"])
        self.assertEqual(on["food"], off["food"])
        self.assertEqual(off["history"], {})


if __name__ == "__main__":
    unittest.main()
