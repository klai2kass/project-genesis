"""How an agent decides what to do.

`decide()` looks at the world and returns ONE action, together with the
agent's need, the options it considered, and a short "why".
It never changes anything itself; `sim.py` applies the action.

That split matters for later: a smarter brain (for example an LLM) can
replace `decide()` without touching the rest of the simulation.
"""

from .needs import wants_rest
from .traits import turn_percent
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


def _home_distance(x, y, home):
    """(Chebyshev steps, then plain grid distance) from (x, y) to home."""
    dx, dy = abs(x - home[0]), abs(y - home[1])
    return max(dx, dy), dx + dy


def _step_home(world, agent):
    """If the agent is too far from home, the direction of the land step that
    brings it closest (fixed order on ties, no dice). None if homes are off,
    it is close enough, or no step gets it closer (for example a lake in the
    way): then it wanders normally."""
    radius = world["config"]["home_radius"]
    home = agent["home"]
    x, y = agent["x"], agent["y"]
    now = _home_distance(x, y, home)
    if radius <= 0 or now[0] <= radius:
        return None
    best = None
    for i, (dx, dy) in enumerate(DIRS):
        if is_land(world, x + dx, y + dy):
            d = _home_distance(x + dx, y + dy, home)
            if d < now and (best is None or d < best[0]):
                best = (d, i)
    return None if best is None else best[1]


def _wander(world, agent, rng, note, why):
    """Keep drifting the same way; sometimes (or when blocked) turn.
    Too far from home (Milestone 3): step back toward home instead."""
    x, y = agent["x"], agent["y"]
    toward = _step_home(world, agent)
    if toward is not None:
        dx, dy = DIRS[toward]
        far = _home_distance(x, y, agent["home"])[0]
        return {"action": "move", "dx": dx, "dy": dy, "heading": toward,
                "note": note + ", but too far from home, so heading back",
                "why": why + "; I am %d tiles from home (%d, %d) and stay within "
                             "%d, so heading home"
                       % (far, agent["home"][0], agent["home"][1],
                          world["config"]["home_radius"])}
    heading = agent["heading"]
    dx, dy = DIRS[heading]
    # Curiosity sets the chance of a voluntary turn (15% at curiosity 50,
    # identical to Milestone 1's rng.chance(0.15)). Water ahead forces a turn.
    turn = rng.below(100) < turn_percent(agent, world["config"])
    if turn or not is_land(world, x + dx, y + dy):
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

    The rules are tried in a fixed order (eat, reproduce, gather, rest, move) and
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
    can_rest, rest_note = wants_rest(agent, cfg)
    rest_level = agent["needs"]["rest"]

    # --- What does it need most? ---
    if energy <= 20:
        need = "food, urgently (energy %d of %d)" % (energy, cfg["max_energy"])
    elif energy <= cfg["eat_below"]:
        need = "food (energy %d of %d)" % (energy, cfg["max_energy"])
    elif can_reproduce:
        need = "a child (strong, adult and rested)"
    elif can_rest:
        need = "rest (rest %d of 100)" % rest_level
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
               _option("gather", can_gather, gather_note),
               _option("rest", can_rest, rest_note)]

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
    elif can_rest:
        decision = {"action": "rest", "voluntary": True,
                    "why": "%s, not hungry (energy %d), so resting at half the "
                           "energy cost" % (rest_note, energy)}
    else:
        decision = _choose_move(world, agent, rng)

    if decision["action"] == "move":
        options.append(_option("move", True, decision.pop("note")))
    elif decision["action"] == "rest" and not decision.get("voluntary"):
        options.append(_option("move", False, "water on every side"))
        options[3] = _option("rest", True, "nothing else is possible (boxed in by water)")
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
    return _walk_to_food(world, agent, rng, mood)


def _food_in_box(world, x, y, vision):
    """Tiles with food inside the square the agent can see (cheap row scan)."""
    cfg = world["config"]
    width, height, food = cfg["width"], cfg["height"], world["food"]
    x0, x1 = max(0, x - vision), min(width - 1, x + vision)
    found = []
    for ty in range(max(0, y - vision), min(height - 1, y + vision) + 1):
        base = ty * width
        for tx in range(x0, x1 + 1):
            if food[base + tx] > 0 and (tx, ty) != (x, y):
                found.append((tx, ty))
    return found


def _steps_to(world, x, y, vision, goals):
    """Walk outward over land, one ring at a time, inside the square the agent
    can see (at most 13 x 13 tiles), until the first tile in `goals` is
    reached. Returns (tile, steps, first_direction) or None if no goal can be
    walked to. Water is never entered, so food across water is not found.
    Fixed order, no dice, so the answer is always the same."""
    cfg = world["config"]
    width, height = cfg["width"], cfg["height"]
    terrain = world["terrain"]
    seen = {(x, y): None}
    frontier = [((x, y), None)]
    steps = 0
    while frontier:
        steps += 1
        nxt = []
        for (cx, cy), first_here in frontier:
            for i, (dx, dy) in enumerate(DIRS):
                nx, ny = cx + dx, cy + dy
                if ((nx, ny) in seen or abs(nx - x) > vision or abs(ny - y) > vision
                        or nx < 0 or ny < 0 or nx >= width or ny >= height
                        or terrain[ny * width + nx] == 0):
                    continue
                first = i if first_here is None else first_here
                if (nx, ny) in goals:
                    return (nx, ny), steps, first
                seen[(nx, ny)] = first
                nxt.append(((nx, ny), first))
        frontier = nxt
    return None


def _walk_to_food(world, agent, rng, mood):
    """Walk toward food that can really be reached, going around water.

    Food is judged by the number of steps needed to WALK there, not by
    straight-line distance. Food behind water that cannot be walked to is
    ignored. The agent keeps its chosen food until it is gone or can no
    longer be reached, so it never flips between two foods. Every step lowers
    the walking distance by one, so it cannot circle forever.
    """
    cfg = world["config"]
    x, y = agent["x"], agent["y"]
    width = cfg["width"]
    vision = cfg["vision"]
    foods = _food_in_box(world, x, y, vision)

    result = None
    target = agent["target"]   # [x, y] or None
    if foods and target is not None and tuple(target) in foods:
        result = _steps_to(world, x, y, vision, {tuple(target)})
    if result is None and foods:
        result = _steps_to(world, x, y, vision, set(foods))
    if result is None:
        agent["target"] = None
        return _wander(world, agent, rng, "no reachable food in sight, so search",
                       mood + "no food within %d tiles that I can walk to, searching"
                       % vision)

    (tx, ty), steps, first = result
    agent["target"] = [tx, ty]
    dx, dy = DIRS[first]
    note = "food in sight at (%d, %d)" % (tx, ty)
    around = ""
    if steps > max(abs(tx - x), abs(ty - y)):
        around = ", going around water"
    return {"action": "move", "dx": dx, "dy": dy, "heading": first,
            "note": note + around,
            "why": mood + "nearest reachable food is %d step%s away at (%d, %d)%s"
                   % (steps, "" if steps == 1 else "s", tx, ty, around)}
