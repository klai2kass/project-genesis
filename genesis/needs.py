"""The rest need: when an agent may rest, and what resting and moving do.

Whole numbers only. See docs/MILESTONE2_V2.md section 4 for the full rules
and the worked cycle (stints start below rest_below=30, end at rest_resume=70,
last exactly 14 ticks at rest_gain=3).

    agent["needs"]["rest"]  0..100, 100 = fully rested
    agent["resting"]        True if its previous action was a voluntary rest
    agent["drain_acc"]      half-rate energy drain counter while resting
    agent["tire_acc"]       tiring counter while moving (industriousness)

Low rest never costs energy or lifespan by itself. Resting is only allowed
when the agent is not hungry (energy above eat_below), so it never overrides
hunger.
"""

from .traits import tire_rate


def _clamp(value):
    return max(0, min(100, value))


def wants_rest(agent, cfg):
    """(fits, note) for the rest rule. Eat/reproduce/gather are checked first."""
    rest = agent["needs"]["rest"]
    if agent["energy"] <= cfg["eat_below"]:
        return False, "hungry (energy %d is not above %d), so no resting" % (
            agent["energy"], cfg["eat_below"])
    if rest < cfg["rest_below"]:
        return True, "tired (rest %d is below %d)" % (rest, cfg["rest_below"])
    if agent["resting"] and rest < cfg["rest_resume"]:
        return True, "still recovering (rest %d, resting until %d)" % (
            rest, cfg["rest_resume"])
    return False, "not tired (rest %d, rests below %d)" % (rest, cfg["rest_below"])


def apply_rest(agent, cfg):
    """A voluntary resting tick, after the normal 1-energy drain was taken."""
    agent["needs"]["rest"] = _clamp(agent["needs"]["rest"] + cfg["rest_gain"])
    agent["energy"] += 1                       # undo the normal drain ...
    agent["drain_acc"] += cfg["rest_drain_units"]
    per = cfg["drain_units_per_energy"]
    while agent["drain_acc"] >= per:           # ... and pay at the rest rate
        agent["drain_acc"] -= per
        agent["energy"] -= 1


def apply_move(agent, cfg):
    """A moving tick tires the agent; industriousness sets how fast."""
    agent["tire_acc"] += tire_rate(agent, cfg)
    scale = cfg["tire_scale"]
    loss = agent["tire_acc"] // scale
    agent["tire_acc"] -= loss * scale
    agent["needs"]["rest"] = _clamp(agent["needs"]["rest"] - loss)
