"""The real rest mechanic and industriousness, run through sim.step().

Rules (docs/MILESTONE2_V2.md section 4): rest only when not hungry
(energy > eat_below); start when rest < 30, keep going until rest >= 70;
+3 rest per resting tick; resting drains energy at half rate (integer
counter); moving tires by 150/100/50 hundredths of a rest point at
industriousness 0/50/100.
"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step  # noqa: E402
from genesis.rng import Rng  # noqa: E402
from genesis.world import GRASS, make_agent  # noqa: E402


def open_world(industriousness=50, curiosity=50, energy=100000, rest=100, **cfg):
    """All grass, no food at all, one agent that never ages or breeds.
    A huge energy store keeps it 'not hungry' for a long time."""
    settings = {"width": 30, "height": 30, "start_agents": 0, "regrow_per_tick": 0,
                "max_energy": 10 ** 6, "repro_min_age": 10 ** 6, "history_keep": 0}
    settings.update(cfg)
    w = create_world(1, settings)
    w["terrain"] = [GRASS] * (30 * 30)
    w["food"] = [0] * (30 * 30)
    a = make_agent(1, 15, 15, energy, 100, Rng(5), w["config"],
                   traits={"curiosity": curiosity, "industriousness": industriousness})
    a["max_age"] = 10 ** 6
    a["needs"]["rest"] = rest
    w["agents"] = [a]
    w["next_id"] = 2
    return w


def trace(world, ticks):
    """(action, rest, energy, tire_acc, drain_acc) after each tick."""
    out = []
    for _ in range(ticks):
        events = step(world)
        a = world["agents"][0]
        out.append((events[0]["action"], a["needs"]["rest"], a["energy"],
                    a["tire_acc"], a["drain_acc"]))
    return out


def stints(rows):
    """Lengths of runs of 'rest' actions."""
    lengths, n = [], 0
    for action, *_ in rows:
        if action == "rest":
            n += 1
        elif n:
            lengths.append(n)
            n = 0
    return lengths


class Tiring(unittest.TestCase):
    def test_lazy_agent_tires_1_2_1_2_and_first_rests_after_48_moves(self):
        rows = trace(open_world(industriousness=0), 60)
        rests = [100] + [r[1] for r in rows]
        losses = [a - b for a, b in zip(rests, rests[1:12])]
        self.assertEqual(losses, [1, 2] * 5 + [1])
        first_rest = [r[0] for r in rows].index("rest")
        self.assertEqual(first_rest, 48)        # 48 moves, then the first rest
        self.assertLess(rests[first_rest], 30)

    def test_tireless_agent_tires_0_1_and_first_rests_after_142_moves(self):
        rows = trace(open_world(industriousness=100), 160)
        rests = [100] + [r[1] for r in rows]
        self.assertEqual([a - b for a, b in zip(rests, rests[1:11])], [0, 1] * 5)
        self.assertEqual([r[0] for r in rows].index("rest"), 142)

    def test_neutral_agent_tires_exactly_one_per_move(self):
        rows = trace(open_world(industriousness=50), 70)
        self.assertEqual([r[1] for r in rows], list(range(99, 29, -1)))
        self.assertTrue(all(r[3] == 0 for r in rows))

    def test_tire_counter_stays_below_scale(self):
        for ind in (0, 13, 50, 77, 100):
            rows = trace(open_world(industriousness=ind), 400)
            self.assertTrue(all(0 <= r[3] < 100 for r in rows), ind)
            self.assertTrue(all(0 <= r[1] <= 100 for r in rows), ind)


class RestStints(unittest.TestCase):
    def test_every_stint_is_14_ticks_and_ends_at_70_or_71(self):
        for ind in (0, 50, 100):
            rows = trace(open_world(industriousness=ind), 1200)
            lengths = stints(rows)
            self.assertGreater(len(lengths), 2, ind)
            self.assertEqual(set(lengths), {14}, ind)
            for i in range(1, len(rows)):
                if rows[i - 1][0] == "rest" and rows[i][0] != "rest":
                    self.assertIn(rows[i - 1][1], (70, 71))

    def test_resting_share_follows_industriousness(self):
        share = {}
        for ind in (0, 50, 100):
            rows = trace(open_world(industriousness=ind), 3000)[300:]
            share[ind] = sum(1 for r in rows if r[0] == "rest") / float(len(rows))
        self.assertAlmostEqual(share[0], 1 / 3.0, delta=0.01)
        self.assertAlmostEqual(share[50], 0.25, delta=0.01)
        self.assertAlmostEqual(share[100], 1 / 7.0, delta=0.01)

    def test_a_14_tick_stint_costs_exactly_7_energy(self):
        rows = trace(open_world(), 200)
        start = [r[0] for r in rows].index("rest")
        before = rows[start - 1][2]
        after = rows[start + 13][2]
        self.assertEqual(before - after, 7)
        self.assertEqual(rows[start + 13][4], 0)            # counter back at 0
        self.assertTrue(all(r[4] in (0, 1) for r in rows))

    def test_moving_costs_one_energy_per_tick(self):
        rows = trace(open_world(), 40)
        energies = [100000] + [r[2] for r in rows]
        self.assertTrue(all(a - b == 1 for a, b in zip(energies, energies[1:])))


class HungerFirst(unittest.TestCase):
    def test_never_rests_while_hungry_even_when_exhausted(self):
        # Energy 79 (hungry, nothing to eat): rest 0 never leads to resting,
        # and there is no penalty: energy falls exactly 1 per tick.
        w = open_world(energy=79, rest=0, max_energy=100)
        rows = trace(w, 60)
        self.assertNotIn("rest", [r[0] for r in rows])
        self.assertEqual([r[2] for r in rows], list(range(78, 18, -1)))
        self.assertTrue(all(r[1] == 0 for r in rows))

    def test_hunger_interrupts_a_stint(self):
        w = open_world(energy=84, rest=20, max_energy=100)
        rows = trace(w, 30)
        self.assertEqual(rows[0][0], "rest")
        # Decision energy = energy after the tick's drain = (previous energy - 1).
        prev = 84
        for action, rest, energy, _, _ in rows:
            if prev - 1 <= 80:
                self.assertNotEqual(action, "rest")
            prev = energy
        self.assertIn("move", [r[0] for r in rows])

    def test_no_voluntary_rest_while_hungry_in_real_worlds(self):
        for seed in ("42", "1"):
            w = create_world(seed, {"history_keep": 0})
            bad = rests = 0
            for _ in range(1500):
                before = {a["id"]: a["energy"] for a in w["agents"]}
                for e in step(w):
                    if e["action"] == "rest" and "half the energy cost" in e["why"]:
                        rests += 1
                        if before[e["agent"]] - 1 <= w["config"]["eat_below"]:
                            bad += 1
            self.assertGreater(rests, 0, seed)
            self.assertEqual(bad, 0, seed)


class Curiosity(unittest.TestCase):
    def _turns(self, curiosity):
        # home_radius=0: this tests Milestone 2 turning alone, without homes.
        w = open_world(curiosity=curiosity, rest_below=0, width=60, height=60,
                       home_radius=0)
        w["terrain"] = [GRASS] * (60 * 60)
        w["food"] = [0] * (60 * 60)
        changes, last = 0, w["agents"][0]["heading"]
        for _ in range(3000):
            step(w)
            h = w["agents"][0]["heading"]
            changes += h != last
            last = h
        return changes / 3000.0

    def test_more_curious_agents_turn_more_often(self):
        low, mid, high = self._turns(0), self._turns(50), self._turns(100)
        self.assertLess(low, mid)
        self.assertLess(mid, high)
        self.assertGreater(high, 2.5 * low)


if __name__ == "__main__":
    unittest.main()
