"""`--set name=value` for the command-line tools.

Turns text like "regrow_per_tick=6" into a checked settings dictionary.
Names come from the real DEFAULT_CONFIG, so a new setting added there
becomes valid here only after it is given a row in RULES below
(a test fails if a setting has no rule). Config files are never touched.
"""

from .config import DEFAULT_CONFIG

# name: (kind, low, high)   kind is "int", "float" or "int_list3"
RULES = {
    "width": ("int", 5, 200),
    "height": ("int", 5, 200),
    "water_share": ("float", 0.0, 0.9),
    "forest_share": ("float", 0.0, 1.0),
    "food_cap": ("int_list3", 0, 100),
    "start_food_share": ("float", 0.0, 1.0),
    "regrow_per_tick": ("int", 0, 100000),
    "food_energy": ("int", 1, 1000),
    "start_agents": ("int", 0, 1000),
    "start_energy": ("int", 1, 1000),
    "max_energy": ("int", 1, 1000),
    "eat_below": ("int", 0, 1000),
    "carry_max": ("int", 0, 100),
    "vision": ("int", 1, 30),
    "repro_min_energy": ("int", 0, 1000),
    "repro_min_age": ("int", 0, 100000),
    "repro_cost": ("int", 0, 1000),
    "repro_cooldown": ("int", 0, 100000),
    "max_age_min": ("int", 1, 100000),
    "max_age_max": ("int", 1, 100000),
    "history_keep": ("int", 0, 1000),
    "dead_history_keep": ("int", 0, 100000),
    "rest_below": ("int", 0, 101),
    "rest_resume": ("int", 0, 101),
    "rest_gain": ("int", 0, 100),
    "rest_drain_units": ("int", 0, 1000),
    "drain_units_per_energy": ("int", 1, 1000),
    "tire_base": ("int", 0, 10000),
    "tire_span": ("int", 0, 10000),
    "tire_scale": ("int", 1, 10000),
    "turn_chance": ("int", 0, 100),
    "turn_span": ("int", 0, 200),
    "trait_founder_min": ("int", 0, 100),
    "trait_founder_max": ("int", 0, 100),
    "trait_mutation": ("int", 0, 100),
    "home_radius": ("int", 0, 200),
    "home_inherit": ("int", 0, 1),
    "memory_keep": ("int", 0, 1000),
    "memory_fade": ("int", 0, 100000),
    "share_min_meetings": ("int", 0, 1000),
}

# Only used while a world is being created; changing them on a loaded world
# would do nothing or break the map.
CREATION_ONLY = ["width", "height", "water_share", "forest_share",
                 "start_food_share", "start_agents", "start_energy",
                 "trait_founder_min", "trait_founder_max"]


def valid_names():
    return sorted(DEFAULT_CONFIG)


def _bad(text):
    raise ValueError(text)


def _parse_value(name, raw):
    kind, low, high = RULES[name]
    raw = raw.strip()
    try:
        if kind == "int":
            value = int(raw)
        elif kind == "float":
            value = float(raw)
        else:
            parts = [p for p in raw.split(",")]
            if len(parts) != 3:
                _bad("%s needs exactly 3 whole numbers separated by commas "
                     "(water,grass,forest), like %s=0,3,8"
                     % (name, name))
            value = [int(p) for p in parts]
    except ValueError:
        want = {"int": "a whole number", "float": "a number",
                "int_list3": "3 whole numbers like 0,3,8"}[kind]
        _bad("%s=%s is not valid: %s must be %s." % (name, raw, name, want))
    for v in (value if isinstance(value, list) else [value]):
        if v != v or v < low or v > high:   # v != v catches nan
            _bad("%s=%s is out of range: allowed values are %s to %s."
                 % (name, raw, low, high))
    return value


def parse_overrides(items):
    """items: list of "name=value" strings. Returns {name: value}.
    If a name is given twice, the last one wins. Raises ValueError with a
    plain-language message."""
    result = {}
    for item in items or []:
        if "=" not in item:
            _bad("'%s' should look like name=value, for example "
                 "regrow_per_tick=6." % item)
        name, raw = item.split("=", 1)
        name = name.strip()
        if name not in DEFAULT_CONFIG or name not in RULES:
            _bad("'%s' is not a setting. Valid names: %s."
                 % (name, ", ".join(valid_names())))
        result[name] = _parse_value(name, raw)
    return result


def check_combined(config):
    """Rules that involve more than one setting."""
    if config["water_share"] + config["forest_share"] > 1.0:
        _bad("water_share + forest_share must not be more than 1.")
    if config["max_age_min"] > config["max_age_max"]:
        _bad("max_age_min must not be larger than max_age_max.")
    if config["start_energy"] > config["max_energy"]:
        _bad("start_energy must not be larger than max_energy.")
    if config["trait_founder_min"] > config["trait_founder_max"]:
        _bad("trait_founder_min must not be larger than trait_founder_max.")
    if config["rest_drain_units"] > config["drain_units_per_energy"]:
        _bad("rest_drain_units must not be larger than drain_units_per_energy "
             "(resting may not cost more than moving).")


def apply_to_loaded(world, overrides):
    """Overrides on a loaded world change only the in-memory copy."""
    for name in overrides:
        if name in CREATION_ONLY:
            _bad("%s only matters when a world is created, so it cannot be "
                 "changed on a loaded save. Use --seed instead of --load."
                 % name)
    merged = dict(world["config"])
    merged.update(overrides)
    check_combined(merged)
    world["config"].update(overrides)


def build_new_config(overrides):
    merged = dict(DEFAULT_CONFIG)
    merged.update(overrides)
    check_combined(merged)
    return overrides


def add_set_option(parser):
    parser.add_argument("--set", dest="overrides", action="append", default=[],
                        metavar="NAME=VALUE",
                        help="change a setting for this run only; repeatable, "
                             "e.g. --set regrow_per_tick=6")


def make_world_from_args(args, parser, create_world, load_world):
    """Shared by run_headless.py and why.py. Exits with a plain message on
    bad input."""
    try:
        overrides = parse_overrides(args.overrides)
        if args.load:
            world = load_world(args.load)
            apply_to_loaded(world, overrides)
        else:
            world = create_world(args.seed, build_new_config(overrides))
    except (ValueError, OSError) as err:
        parser.error(str(err))
    return world
