"""Design check for the planned rest rules (docs/MILESTONE2_V2.md, section 4).

Nothing of Milestone 2 exists yet. These tests run the document's whole-number
formulas as tiny stand-alone functions and check the extremes mathematically.
When `genesis/needs.py` exists (stage 3/4) the real code must give the same
numbers, and these tests should then call it instead of the helpers below.
"""
import unittest

TIRE_BASE, TIRE_SPAN, TIRE_SCALE = 100, 100, 100
REST_BELOW, REST_RESUME, REST_GAIN = 30, 70, 3


def tire_rate(industriousness):
    """Rest lost per 100 moving ticks (hundredths of a rest point per move)."""
    return TIRE_BASE - ((industriousness - 50) * TIRE_SPAN) // 100


def one_move(rest, acc, industriousness):
    """One moving tick: returns (new rest, new accumulator, rest lost)."""
    acc += tire_rate(industriousness)
    loss = acc // TIRE_SCALE
    acc -= loss * TIRE_SCALE
    return max(0, rest - loss), acc, loss


def run_cycle(industriousness, ticks=3000):
    """An agent that is never hungry and never finds anything to gather."""
    rest, acc, resting = 100, 0, False
    moves = rests = 0
    cycles, cm, cr, losses = [], 0, 0, []
    for _ in range(ticks):
        if rest < REST_BELOW or (resting and rest < REST_RESUME):
            resting = True
            rest = min(100, rest + REST_GAIN)
            rests += 1
            cr += 1
        else:
            if resting:
                cycles.append((cm, cr))
                cm = cr = 0
            resting = False
            rest, acc, loss = one_move(rest, acc, industriousness)
            moves += 1
            cm += 1
            if len(losses) < 12:
                losses.append(loss)
        assert 0 <= rest <= 100
    return {"share": rests / float(ticks), "cycle": cycles[-1], "losses": losses}


def moves_until_tired(industriousness):
    rest, acc, n = 100, 0, 0
    while rest >= REST_BELOW:
        rest, acc, _ = one_move(rest, acc, industriousness)
        n += 1
    return n


class RestDesign(unittest.TestCase):
    def test_rate_extremes_and_neutral(self):
        self.assertEqual(tire_rate(0), 150)     # lazy: 1.5 rest points per move
        self.assertEqual(tire_rate(50), 100)    # neutral: exactly today's 1 per move
        self.assertEqual(tire_rate(100), 50)    # tireless: 0.5 per move
        self.assertEqual(tire_rate(25), 125)
        self.assertEqual(tire_rate(75), 75)

    def test_rate_is_monotone_and_in_range(self):
        rates = [tire_rate(i) for i in range(101)]
        self.assertEqual(min(rates), 50)
        self.assertEqual(max(rates), 150)
        self.assertTrue(all(a >= b for a, b in zip(rates, rates[1:])))
        self.assertTrue(all(isinstance(r, int) for r in rates))

    def test_exact_long_run_average_for_every_value(self):
        # Over 100 moving ticks the loss is exactly the rate in whole points:
        # nothing is lost to rounding, and the accumulator always stays below 100.
        for ind in range(101):
            rest, acc, total = 10 ** 6, 0, 0
            for _ in range(100):
                before = rest
                rest, acc, loss = one_move(rest, acc, ind)
                total += before - rest
                self.assertTrue(0 <= acc < TIRE_SCALE)
            self.assertEqual(total, tire_rate(ind), "industriousness %d" % ind)

    def test_loss_patterns_at_the_extremes(self):
        self.assertEqual(run_cycle(0)["losses"], [1, 2] * 6)
        self.assertEqual(run_cycle(50)["losses"], [1] * 12)
        self.assertEqual(run_cycle(100)["losses"], [0, 1] * 6)

    def test_time_to_first_tiredness(self):
        # From full rest until rest first drops below 30.
        self.assertEqual(moves_until_tired(0), 48)
        self.assertEqual(moves_until_tired(50), 71)    # 100 - 30 + 1
        self.assertEqual(moves_until_tired(100), 142)

    def test_steady_cycle_and_share_of_time_resting(self):
        lazy, mid, tireless = run_cycle(0), run_cycle(50), run_cycle(100)
        self.assertEqual(lazy["cycle"], (28, 14))
        self.assertEqual(mid["cycle"], (42, 14))
        self.assertEqual(tireless["cycle"], (84, 14))
        self.assertAlmostEqual(lazy["share"], 0.331, places=2)
        self.assertAlmostEqual(mid["share"], 0.247, places=2)
        self.assertAlmostEqual(tireless["share"], 0.140, places=2)
        self.assertGreater(lazy["share"], mid["share"])
        self.assertGreater(mid["share"], tireless["share"])

    def test_resting_energy_cost_is_half(self):
        # The half-rate drain rule: normal 1-energy drain undone, then 1 unit
        # of 2 added to the accumulator, paying 1 energy whenever it reaches 2.
        energy, acc = 90, 0
        for _ in range(10):
            energy -= 1
            energy += 1
            acc += 1
            if acc >= 2:
                acc -= 2
                energy -= 1
        self.assertEqual((energy, acc), (85, 0))


def stints(industriousness, resume=REST_RESUME, how_many=200):
    """Complete cycles of a never-hungry agent: a list of
    (rest value when the stint began, rest value when it ended, stint length in
    ticks, moves made since the previous stint). The first entry starts from
    full rest (100), so steady-state numbers skip it."""
    rest, acc, resting = 100, 0, False
    out, start, rests_now, moves_now = [], None, 0, 0
    while len(out) < how_many + 1:
        if rest < REST_BELOW or (resting and rest < resume):
            if not resting:
                start, resting = rest, True
            rest = min(100, rest + REST_GAIN)
            rests_now += 1
        else:
            if resting:
                out.append((start, rest, rests_now, moves_now))
                resting, rests_now, moves_now = False, 0, 0
            rest, acc, _ = one_move(rest, acc, industriousness)
            moves_now += 1
    return out[1:]


class CompleteRestCycle(unittest.TestCase):
    """Start condition: rest < 30. End condition: rest >= 70 (NOT 100)."""

    def test_stint_starts_below_30_and_ends_at_70_or_more(self):
        for ind in range(0, 101, 5):
            for start, end, length, _ in stints(ind):
                self.assertLess(start, REST_BELOW)           # began because rest < 30
                self.assertGreaterEqual(start, REST_BELOW - 2)  # a move loses at most 2
                self.assertGreaterEqual(end, REST_RESUME)    # ended because rest >= 70
                self.assertLess(end, REST_RESUME + REST_GAIN)  # and stopped right away
                self.assertEqual(end, min(100, start + REST_GAIN * length))

    def test_every_stint_is_exactly_14_ticks_for_every_trait_value(self):
        # 14 = smallest k with start + 3k >= 70 for start 28 or 29
        self.assertEqual(-(-(REST_RESUME - 29) // REST_GAIN), 14)   # 29 + 3*14 = 71
        self.assertEqual(-(-(REST_RESUME - 28) // REST_GAIN), 14)   # 28 + 3*14 = 70
        for ind in range(101):
            lengths = {x[2] for x in stints(ind, how_many=60)}
            self.assertEqual(lengths, {14}, "industriousness %d" % ind)

    def test_rest_threshold_hand_calculation(self):
        rest = 29
        for k in range(1, 15):
            rest += REST_GAIN
            if k == 13:
                self.assertEqual(rest, 68)     # still below 70: keep resting
            if k == 14:
                self.assertEqual(rest, 71)     # >= 70: the stint ends here

    def test_steady_state_share_matches_gain_loss_balance(self):
        # Over a full cycle rest returns to where it was: moves * rate/100 =
        # rest_ticks * 3, so share = rate / (rate + 300), up to a 1-tick edge.
        expected = {0: (28.0, 33.33), 25: (33.6, 29.41), 50: (42.0, 25.00),
                    75: (56.0, 20.00), 100: (84.0, 14.29)}
        for ind, (moves, share) in expected.items():
            cycles = stints(ind, how_many=300)
            rests = sum(c[2] for c in cycles)
            mv = sum(c[3] for c in cycles)
            self.assertAlmostEqual(mv / float(len(cycles)), moves, places=1)
            self.assertAlmostEqual(100.0 * rests / (rests + mv), share, places=1)
            rate = tire_rate(ind)
            self.assertAlmostEqual(100.0 * rate / (rate + 300), share, places=1)

    def test_ending_a_stint_at_100_changes_length_but_hardly_the_share(self):
        # Alternative (not proposed): rest until 100 instead of 70.
        for ind, share in ((0, 33.33), (50, 25.26), (100, 14.46)):
            cycles = stints(ind, resume=100, how_many=200)
            self.assertEqual({c[2] for c in cycles}, {24})   # 29 + 3*24 = 101 -> 100
            rests = sum(c[2] for c in cycles)
            mv = sum(c[3] for c in cycles)
            self.assertAlmostEqual(100.0 * rests / (rests + mv), share, places=1)

    def test_energy_over_a_complete_cycle(self):
        # Moving costs 1 energy per tick, resting 1 per 2 ticks (drain_acc).
        # A 14-tick stint has an even number of resting ticks, so drain_acc is
        # 0 after every stint and each full cycle costs exactly moves + 7.
        for ind in (0, 50, 100):
            rest, acc, resting = 100, 0, False
            energy, drain_acc = 10 ** 6, 0
            marks = []                      # (energy, drain_acc) at the end of each stint
            while len(marks) < 6:
                if rest < REST_BELOW or (resting and rest < REST_RESUME):
                    resting = True
                    rest = min(100, rest + REST_GAIN)
                    energy -= 1             # normal drain
                    energy += 1             # undone while resting
                    drain_acc += 1
                    if drain_acc >= 2:
                        drain_acc -= 2
                        energy -= 1
                else:
                    if resting:
                        marks.append((energy, drain_acc))
                    resting = False
                    rest, acc, _ = one_move(rest, acc, ind)
                    energy -= 1
            cycles = stints(ind, how_many=4)
            for i in range(1, 4):           # marks[0] belongs to the first descent
                used = marks[i - 1][0] - marks[i][0]
                self.assertEqual(marks[i][1], 0)
                self.assertEqual(used, cycles[i - 1][3] + 7, "industriousness %d" % ind)

    def test_no_rest_while_rest_is_30_or_more_unless_mid_stint(self):
        rest, acc, resting = 100, 0, False
        for _ in range(2000):
            starts_or_continues = rest < REST_BELOW or (resting and rest < REST_RESUME)
            if starts_or_continues:
                resting = True
                rest = min(100, rest + REST_GAIN)
            else:
                self.assertTrue(rest >= REST_BELOW or resting)
                resting = False
                rest, acc, _ = one_move(rest, acc, 50)
            self.assertTrue(0 <= rest <= 100)


if __name__ == "__main__":
    unittest.main()
