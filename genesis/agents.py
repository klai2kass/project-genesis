"""How an agent decides what to do.

`decide()` looks at the world and returns ONE action plus a short "why".
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


def _wander(world, agent, rng, why):
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
    return {"action": "move", "dx": dx, "dy": dy, "heading": heading, "why": why}


def decide(world, agent, rng):
    """Pick one action for this tick. Rules are checked top to bottom."""
    cfg = world["config"]
    x, y = agent["x"], agent["y"]
    energy, pack, age = agent["energy"], agent["food"], agent["age"]
    carry_max = cfg["carry_max"]
    here = world["food"][tile_index(world, x, y)]

    # 1. Eat if there is room in the belly and food in the pack.
    if pack > 0 and energy <= cfg["eat_below"]:
        return {"action": "eat",
                "why": "energy %d is at or below %d and I carry %d food"
                       % (energy, cfg["eat_below"], pack)}

    # 2. Have a child if strong, grown up, and rested.
    if (energy >= cfg["repro_min_energy"] and age >= cfg["repro_min_age"]
            and agent["cooldown"] == 0):
        return {"action": "reproduce",
                "why": "energy %d is at least %d, I am an adult (age %d) "
                       "and rested since my last child"
                       % (energy, cfg["repro_min_energy"], age)}

    # 3. Pick up food from the ground if the pack has room.
    if here > 0 and pack < carry_max:
        return {"action": "gather",
                "why": "%d food on this tile and my pack has room (%d/%d)"
                       % (here, pack, carry_max)}

    # 4. Otherwise move: explore if the pack is full, else go look for food.
    if pack >= carry_max:
        return _wander(world, agent, rng,
                       "pack is full (%d/%d) and I am not hungry, so exploring"
                       % (pack, carry_max))

    mood = "starving (energy %d), " % energy if energy <= 20 else ""
    target = find_nearest_food(world, x, y)
    if target is None:
        return _wander(world, agent, rng,
                       mood + "no food within %d tiles, searching" % cfg["vision"])

    tx, ty, steps = target
    sx, sy = _sign(tx - x), _sign(ty - y)
    for dx, dy in ((sx, sy), (sx, 0), (0, sy)):
        if (dx, dy) != (0, 0) and is_land(world, x + dx, y + dy):
            return {"action": "move", "dx": dx, "dy": dy,
                    "heading": DIRS.index((dx, dy)),
                    "why": mood + "nearest food is %d step%s away at (%d, %d)"
                           % (steps, "" if steps == 1 else "s", tx, ty)}
    return _wander(world, agent, rng,
                   mood + "I see food at (%d, %d) but water blocks the way, "
                          "going around" % (tx, ty))
