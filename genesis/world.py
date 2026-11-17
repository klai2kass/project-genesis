"""Building a brand new world from a seed.

The whole world is ONE plain dictionary of numbers, text and lists.
Keeping it that plain is what makes save/load trivial: we can write the
dictionary to a file and read it back, and nothing is lost.
"""

import copy

from .config import DEFAULT_CONFIG
from .rng import Rng, seed_to_state
from .traits import founder_traits, neutral_traits

SAVE_VERSION = 3

# Terrain codes stored in world["terrain"]
WATER, GRASS, FOREST = 0, 1, 2
TERRAIN_NAMES = ["water", "grass", "forest"]


def tile_index(world, x, y):
    """The map is stored as one long list, row after row."""
    return y * world["config"]["width"] + x


def is_land(world, x, y):
    cfg = world["config"]
    if x < 0 or y < 0 or x >= cfg["width"] or y >= cfg["height"]:
        return False
    return world["terrain"][y * cfg["width"] + x] != WATER


def make_agent(agent_id, x, y, energy, age, rng, cfg, parent=None, generation=0,
               traits=None):
    return {
        "id": agent_id,
        "x": x,
        "y": y,
        "energy": energy,
        "age": age,
        "max_age": rng.between(cfg["max_age_min"], cfg["max_age_max"]),
        "food": 0,                 # food carried in the pack
        "heading": rng.below(8),   # direction it drifts in when wandering
        "cooldown": 0,             # ticks until it may reproduce again
        "parent": parent,
        "generation": generation,
        "target": None,            # food it is walking to: [x, y], or None
        # Milestone 2 (whole numbers; see genesis/needs.py and traits.py)
        "needs": {"rest": 100},    # 100 = fully rested
        "resting": False,          # was its last action a voluntary rest?
        "drain_acc": 0,            # half-rate energy drain counter (resting)
        "tire_acc": 0,             # tiring counter (moving)
        "traits": traits if traits is not None else neutral_traits(),
        "last_action": "born",
        "last_why": "placed in the world at the start" if parent is None
                    else "child of #%d" % parent,
    }


def create_world(seed, config=None):
    """Make a new world. The same seed always makes the same world."""
    cfg = copy.deepcopy(DEFAULT_CONFIG)
    if config:
        cfg.update(copy.deepcopy(config))

    rng = Rng(seed_to_state(seed))
    terrain = _make_terrain(cfg, rng)

    # A share of the tiles start with some food (a random amount up to the
    # tile's cap); the rest start bare and fill in as food regrows.
    food = [rng.between(0, cfg["food_cap"][t])
            if rng.chance(cfg["start_food_share"]) else 0
            for t in terrain]

    # Drop the first agents on random land tiles, with mixed ages so they
    # do not all die of old age on the same day.
    width = cfg["width"]
    land = [i for i, t in enumerate(terrain) if t != WATER]
    agents = []
    for agent_id in range(1, cfg["start_agents"] + 1):
        spot = rng.choice(land)
        age = rng.between(0, 200)
        agent = make_agent(agent_id, spot % width, spot // width,
                           cfg["start_energy"], age, rng, cfg,
                           traits=founder_traits(str(seed), agent_id, cfg))
        # Stagger first children too, so there is no baby boom at tick 1.
        agent["cooldown"] = rng.between(0, cfg["repro_cooldown"])
        agents.append(agent)

    return {
        "version": SAVE_VERSION,
        "seed": str(seed),
        "tick": 0,
        "rng": rng.state,          # where the dice are right now
        "config": cfg,
        "terrain": terrain,
        "food": food,
        "agents": agents,
        "next_id": cfg["start_agents"] + 1,
        "history": {},
        "history_dead": [],
        "stats": {"births": 0, "deaths_starved": 0, "deaths_old_age": 0},
    }


def _make_terrain(cfg, rng):
    """Random heights, smoothed into blobs, then cut into water/grass/forest."""
    width, height = cfg["width"], cfg["height"]
    heights = [rng.random() for _ in range(width * height)]

    # Smooth 4 times: each tile becomes the average of itself and neighbours.
    for _ in range(4):
        smoothed = []
        for y in range(height):
            for x in range(width):
                total, count = 0.0, 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < width and 0 <= ny < height:
                            total += heights[ny * width + nx]
                            count += 1
                smoothed.append(total / count)
        heights = smoothed

    # Lowest tiles become water, highest become forest, the rest grass.
    ordered = sorted(heights)
    water_line = ordered[int(len(ordered) * cfg["water_share"])]
    forest_line = ordered[int(len(ordered) * (1 - cfg["forest_share"]))]
    terrain = []
    for h in heights:
        if h < water_line:
            terrain.append(WATER)
        elif h >= forest_line:
            terrain.append(FOREST)
        else:
            terrain.append(GRASS)
    return terrain
