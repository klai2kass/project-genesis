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
    "regrow_per_tick": 4,
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
}
