"""How an agent decides what to do.

`decide()` looks at the world and returns ONE action, together with the
agent's need, the options it considered, and a short "why".
It never changes anything itself; `sim.py` applies the action.

That split matters for later: a smarter brain (for example an LLM) can
replace `decide()` without touching the rest of the simulation.
"""

from .world import is_land, tile_index

# The 8 directions an agent can step in: N, NE, E, SE, S, SW, W, NW
DIRS = [(0, -1), (1, -1), (1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1)]

_offset_cache = {}


def _offsets(vision):
    """Every tile position within `vision` steps, nearest first."""
    if vision not in _offset_cache:
        spots = [(dx, dy)
                 for dy in range(-vision, vision + 1)
                 for dx in range(-vision, vision + 1)
                 if (dx, dy) != (0, 0)]
        spots.sort(key=lambda s: (max(abs(s[0]), abs(s[1])),
                                  abs(s[0]) + abs(s[1]), s[1], s[0]))
        _offset_cache[vision] = spots
    return _offset_cache[vision]


def find_nearest_food(world, x, y):
    """Return (x, y, steps) of the closest food in sight, or None."""
    cfg = world["config"]
    width, height = cfg["width"], cfg["height"]
    food = world["food"]
    for dx, dy in _offsets(cfg["vision"]):
        nx, ny = x + dx, y + dy
        if 0 <= nx < width and 0 <= ny < height and food[ny * width + nx] > 0:
            return nx, ny, max(abs(dx), abs(dy))
    return None


def _sign(n):
    return (n > 0) - (n < 0)


def _wander(world, agent, rng, note, why):
    """Keep drifting the same way; sometimes (or when blocked) turn."""
    x, y = agent["x"], agent["y"]
    heading = agent["heading"]
    dx, dy = DIRS[heading]
    if rng.chance(0.15) or not is_land(world, x + dx, y + dy):
        open_ways = [i for i, (ddx, ddy) in enumerate(DIRS)
                     if is_land(world, x + ddx, y + ddy)]
        if not open_ways:
            return {"action": "rest", "why": why + " (but boxed in by water)"}
        heading = rng.choice(open_ways)
        dx, dy = DIRS[heading]
    return {"action": "move", "dx": dx, "dy": dy, "heading": heading,
            "note": note, "why": why}


def _option(action, ok, note):
    """One thing the agent considered: could it do it, and a short note."""
    return {"action": action, "ok": ok, "note": note}


def decide(world, agent, rng):
    """Pick one action for this tick.

    The rules are tried in a fixed order (eat, reproduce, gather, move) and
    the first one that fits wins. The result records three things so you can
    always see WHY:
      need    - what the agent most needs right now
      options - every rule it considered, and whether each one fitted
      why     - one sentence: the reason for the rule it chose
    """
    cfg = world["config"]
    x, y = agent["x"], agent["y"]
    energy, pack, age = agent["energy"], agent["food"], agent["age"]
    carry_max = cfg["carry_max"]
    here = world["food"][tile_index(world, x, y)]

    can_eat = pack > 0 and energy <= cfg["eat_below"]
    can_reproduce = (energy >= cfg["repro_min_energy"]
                     and age >= cfg["repro_min_age"] and agent["cooldown"] == 0)
    can_gather = here > 0 and pack < carry_max

    # --- What does it need most? ---
    if energy <= 20:
        need = "food, urgently (energy %d of %d)" % (energy, cfg["max_energy"])
    elif energy <= cfg["eat_below"]:
        need = "food (energy %d of %d)" % (energy, cfg["max_energy"])
    elif can_reproduce:
        need = "a child (strong, adult and rested)"
    elif pack < carry_max:
        need = "to stock up on food (pack %d of %d)" % (pack, carry_max)
    else:
        need = "nothing pressing (well fed, pack full)"

    # --- What did it consider? One short note per rule. ---
    if pack == 0:
        eat_note = "no food in my pack"
    elif not can_eat:
        eat_note = "energy %d is above %d, not hungry enough" % (energy, cfg["eat_below"])
    else:
        eat_note = "I carry %d food and have room for the energy" % pack

    if energy < cfg["repro_min_energy"]:
        repro_note = "energy %d is below %d" % (energy, cfg["repro_min_energy"])
    elif age < cfg["repro_min_age"]:
        repro_note = "too young (age %d, adult at %d)" % (age, cfg["repro_min_age"])
    elif agent["cooldown"] > 0:
        repro_note = "resting %d more ticks after my last child" % agent["cooldown"]
    else:
        repro_note = "strong, adult and rested"

    if here == 0:
        gather_note = "no food on this tile"
    elif pack >= carry_max:
        gather_note = "my pack is full (%d of %d)" % (pack, carry_max)
    else:
        gather_note = "%d food here and my pack has room" % here

    options = [_option("eat", can_eat, eat_note),
               _option("reproduce", can_reproduce, repro_note),
               _option("gather", can_gather, gather_note)]

    # --- Choose: the first rule that fits. ---
    if can_eat:
        decision = {"action": "eat",
                    "why": "energy %d is at or below %d and I carry %d food"
                           % (energy, cfg["eat_below"], pack)}
    elif can_reproduce:
        decision = {"action": "reproduce",
                    "why": "energy %d is at least %d, I am an adult (age %d) "
                           "and rested since my last child"
                           % (energy, cfg["repro_min_energy"], age)}
    elif can_gather:
        decision = {"action": "gather",
                    "why": "%d food on this tile and my pack has room (%d/%d)"
                           % (here, pack, carry_max)}
    else:
        decision = _choose_move(world, agent, rng)

    if decision["action"] == "move":
        options.append(_option("move", True, decision.pop("note")))
    elif decision["action"] == "rest":
        options.append(_option("move", False, "water on every side"))
        options.append(_option("rest", True, "nothing else is possible"))
    else:
        options.append(_option("move", True, "always possible, but a rule above fits first"))

    decision["need"] = need
    decision["options"] = options
    return decision


def _choose_move(world, agent, rng):
    """Nothing to eat, gather or give birth to: decide where to walk."""
    cfg = world["config"]
    x, y = agent["x"], agent["y"]
    energy, pack, carry_max = agent["energy"], agent["food"], cfg["carry_max"]

    # Explore if the pack is full, else go and look for food.
    if pack >= carry_max:
        return _wander(world, agent, rng, "nothing to fetch, so explore",
                       "pack is full (%d/%d) and I am not hungry, so exploring"
                       % (pack, carry_max))

    mood = "starving (energy %d), " % energy if energy <= 20 else ""
    target = find_nearest_food(world, x, y)
    if target is None:
        return _wander(world, agent, rng, "no food in sight, so search",
                       mood + "no food within %d tiles, searching" % cfg["vision"])

    tx, ty, steps = target
    sx, sy = _sign(tx - x), _sign(ty - y)
    for dx, dy in ((sx, sy), (sx, 0), (0, sy)):
        if (dx, dy) != (0, 0) and is_land(world, x + dx, y + dy):
            return {"action": "move", "dx": dx, "dy": dy,
                    "heading": DIRS.index((dx, dy)),
                    "note": "food in sight at (%d, %d)" % (tx, ty),
                    "why": mood + "nearest food is %d step%s away at (%d, %d)"
                           % (steps, "" if steps == 1 else "s", tx, ty)}
    return _wander(world, agent, rng, "food in sight but water blocks the way",
                   mood + "I see food at (%d, %d) but water blocks the way, "
                          "going around" % (tx, ty))
