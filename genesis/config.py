"""All the numbers that shape the world, in one place.

Change a number here, run again, and watch what happens.
A copy of these settings is stored inside every world (and every save),
so an old save keeps the rules it was created with.
"""

DEFAULT_CONFIG = {
    # --- Map ---
    "width": 60,
    "height": 40,
    "water_share": 0.18,   # lowest 18% of the land becomes water
    "forest_share": 0.25,  # highest 25% becomes forest (grows more food)

    # --- Food ---
    # Most food a tile can hold, by terrain: [water, grass, forest]
    "food_cap": [0, 3, 8],
    "start_food_share": 0.08,  # share of tiles that start with food on them
    # Each tick this many random tiles try to grow 1 food.
    "regrow_per_tick": 6,
    "food_energy": 20,     # energy gained by eating 1 food

    # --- Agents ---
    "start_agents": 50,
    "start_energy": 60,
    "max_energy": 100,
    "eat_below": 80,       # eat when energy is at or below this
    "carry_max": 3,        # food an agent can carry
    "vision": 4,           # how many tiles away an agent can see food

    # --- Reproduction ---
    "repro_min_energy": 90,
    "repro_min_age": 80,
    "repro_cost": 50,      # parent pays this; the child starts with it
    "repro_cooldown": 200, # ticks to wait before the next child

    # --- Lifespan (each agent gets a random number in this range) ---
    "max_age_min": 400,
    "max_age_max": 700,

    # --- Rest (Milestone 2; see docs/MILESTONE2_V2.md section 4) ---
    # A not-hungry agent rests when rest < rest_below and keeps resting
    # until rest >= rest_resume. Each resting tick gives rest_gain rest.
    "rest_below": 30,
    "rest_resume": 70,
    "rest_gain": 3,
    # Resting halves the energy drain: each resting tick adds
    # rest_drain_units to a counter; 1 energy is paid per
    # drain_units_per_energy units (1 of 2 = half rate). Whole numbers only.
    "rest_drain_units": 1,
    "drain_units_per_energy": 2,
    # Tiring while moving, in 1/tire_scale rest points per move:
    # tire_base - (industriousness - 50) * tire_span / 100  -> 150..50
    "tire_base": 100,
    "tire_span": 100,
    "tire_scale": 100,

    # --- Personality traits (0-100, 50 = neutral) ---
    # Chance (percent) to turn on each wandering tick:
    # turn_chance + (curiosity - 50) * turn_span / 100  -> 5..25
    "turn_chance": 15,
    "turn_span": 20,
    "trait_founder_min": 40,   # first agents: each trait in this range
    "trait_founder_max": 60,
    "trait_mutation": 5,       # child = parent +/- up to this, per trait

    # --- Home (Milestone 3; see docs/MILESTONE3.md) ---
    # Every agent remembers the tile where it was born (founders: where they
    # were placed). A WANDERING agent (no reachable food in sight, or pack
    # full) that is more than home_radius tiles from home steps back toward
    # it. 0 = off (old saves load with 0 and keep their old behaviour).
    "home_radius": 6,

    # --- Memory of decisions (kept in saves) ---
    "history_keep": 20,        # recent decisions remembered per agent
    "dead_history_keep": 50,   # how many dead agents' decisions are kept
}
