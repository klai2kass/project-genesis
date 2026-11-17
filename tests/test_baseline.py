"""Behaviour must stay the same as the frozen Milestone 1 reference.

The reference numbers live in experiments/baseline/baseline.json (made from
the unchanged Milestone 1 rules). A stage that promises "behaviour unchanged"
must keep these tests green. A stage that changes behaviour on purpose must
say so in docs/MILESTONE2_V2.md and update the reference ON PURPOSE, in its
own commit, with the reason in STATUS.md.
"""
import json
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "experiments", "baseline"))

import make_baseline as mb  # noqa: E402
from genesis import create_world, load_world, step, world_from_json, world_to_json  # noqa: E402
from genesis.digest import EventDigest, behaviour_digest  # noqa: E402

REF = json.load(open(mb.PATH))


class BaselineTest(unittest.TestCase):
    def test_short_runs_match_reference(self):
        # Milestone 2 code with MILESTONE1_RULES (nobody rests, traits 50) must
        # behave exactly like the frozen Milestone 1 code: same counters, same
        # behaviour digest, same event digest. Only the whole-world fingerprint
        # differs, because agents now carry new fields (expected, documented).
        for seed in mb.SHORT_SEEDS:
            now, ref = mb.short_run(seed), dict(REF["short"][seed])
            self.assertNotEqual(now.pop("fingerprint"), None)
            ref.pop("fingerprint")
            self.assertEqual(now, ref, "seed " + seed)

    def test_new_rules_do_change_behaviour(self):
        # Sanity check the other way round: with the real Milestone 2 defaults
        # (rest on, varied traits) the events are NOT the Milestone 1 events.
        now = mb.short_run("42", rules={})
        self.assertNotEqual(now["event_digest"], REF["short"]["42"]["event_digest"])

    def test_v2_save_loads_and_continues_the_same(self):
        self.assertEqual(mb.fixture_run(), REF["save"])

    def test_save_load_continue_equals_uninterrupted(self):
        a = create_world("42")
        b = create_world("42")
        for _ in range(150):
            step(a)
            step(b)
        b = world_from_json(world_to_json(b))
        da, db = EventDigest(), EventDigest()
        for _ in range(100):
            da.add(step(a))
            db.add(step(b))
        self.assertEqual(da.hexdigest(), db.hexdigest())
        self.assertEqual(behaviour_digest(a), behaviour_digest(b))

    def test_digest_ignores_new_agent_fields_but_sees_behaviour(self):
        w = create_world("7")
        before = behaviour_digest(w)
        for a in w["agents"]:
            a["traits"] = {"curiosity": 50}      # a new field: digest must not care
        self.assertEqual(behaviour_digest(w), before)
        w["agents"][0]["energy"] += 1            # real change: digest must notice
        self.assertNotEqual(behaviour_digest(w), before)


if __name__ == "__main__":
    unittest.main()
