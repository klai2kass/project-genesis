"""Saving and loading worlds.

A world is a plain dictionary, so a save file is just that dictionary
written as JSON text. You can open a save in any text editor.
"""

import hashlib
import json
import os

import copy

from .config import DEFAULT_CONFIG
from .world import SAVE_VERSION

# ---------------------------------------------------------------------------
# Save format versions
#   1  first format (Milestone 1).
#   2  same layout, but loading (any version) repairs older/partial saves: settings and
#      fields missing from the file are filled with the documented defaults
#      below. Anything the file has that we do not know is kept untouched.
#   3  Milestone 2: agents have needs (rest), traits (curiosity,
#      industriousness) and two counters. A version 1 or 2 save is migrated so
#      that it KEEPS ITS OLD RULES: every agent gets neutral traits (50) and
#      the world gets rest_below=0 (nobody ever rests) and neutral trait
#      settings for newborns. So an old world continues exactly as before
#      (tested against the frozen baseline). To try the new rules on an old
#      world: --set rest_below=30 --set trait_mutation=5.
#   4  Milestone 3 step 1: every agent has a home [x, y] (where it was born).
#      A version 3 (or older) save is migrated so it KEEPS ITS OLD RULES:
#      home_radius=0 (homes are remembered but never used) and each living
#      agent's home is set to where it stands now (its birthplace was never
#      recorded). To try homes on an old world: --set home_radius=6.
# Every change made while loading is written to world["migration_log"] (only
# when something changed), so nothing happens silently.
# To add a new version: bump SAVE_VERSION in world.py, write a function
# _migrate_N_to_M below and add it to MIGRATIONS.
# ---------------------------------------------------------------------------

# Parts of a save that cannot be invented: without them we refuse to load.
REQUIRED_KEYS = ["seed", "tick", "rng", "config", "terrain", "food", "agents"]

# Defaults for agent fields (used if an old save lacks them).
AGENT_DEFAULTS = {
    "food": 0, "heading": 0, "target": None, "cooldown": 0, "parent": None, "generation": 0,
    "last_action": "unknown (old save)", "last_why": "unknown (old save)",
    "needs": {"rest": 100}, "resting": False, "drain_acc": 0, "tire_acc": 0,
    "traits": {"curiosity": 50, "industriousness": 50},
}

# Settings that make the Milestone 2 rules behave exactly like Milestone 1.
# Used when migrating a version 1/2 save, so old worlds keep their rules.
MILESTONE1_RULES = {"rest_below": 0, "trait_founder_min": 50,
                    "trait_founder_max": 50, "trait_mutation": 0, "home_radius": 0}

# Settings that make the new rules behave exactly like Milestone 2.
MILESTONE2_RULES = {"home_radius": 0}

# Defaults for the counters in world["stats"].
STATS_DEFAULTS = {"births": 0, "deaths_starved": 0, "deaths_old_age": 0}


def world_to_json(world):
    # sort_keys makes the text identical for identical worlds.
    return json.dumps(world, sort_keys=True)


def _note(world, text):
    world.setdefault("migration_log", []).append(text)


def _repair(world):
    """Fill anything missing with defaults, and say what was filled.
    Runs on EVERY load (not only old versions), so adding a new optional
    field later never needs a version bump."""
    cfg = world["config"]
    if not isinstance(cfg, dict):
        raise ValueError("This save's config is damaged (not a dictionary).")
    for key, value in DEFAULT_CONFIG.items():
        if key not in cfg:
            cfg[key] = copy.deepcopy(value)
            _note(world, "config.%s missing: used default %r" % (key, value))

    stats = world.setdefault("stats", {})
    for key, value in STATS_DEFAULTS.items():
        if key not in stats:
            stats[key] = value
            _note(world, "stats.%s missing: used %r" % (key, value))

    for agent in world["agents"]:
        for key, value in AGENT_DEFAULTS.items():
            if key not in agent:
                agent[key] = copy.deepcopy(value)
                _note(world, "agent %s: %s missing: used %r"
                      % (agent.get("id", "?"), key, value))
        if "home" not in agent:
            agent["home"] = [agent["x"], agent["y"]]
            _note(world, "agent %s: home missing: set to where it stands (%d, %d)"
                  % (agent.get("id", "?"), agent["x"], agent["y"]))

    for key, empty in (("history", {}), ("history_dead", [])):
        if key not in world:
            world[key] = empty
            _note(world, "%s missing (old save): starting with no remembered "
                         "decisions" % key)

    if "next_id" not in world:
        world["next_id"] = max([a["id"] for a in world["agents"]] + [0]) + 1
        _note(world, "next_id missing: set to %d" % world["next_id"])


def _migrate_1_to_2(world):
    world["version"] = 2   # same layout; the repair step does the real work


def _migrate_2_to_3(world):
    cfg = world["config"]
    for key, value in MILESTONE1_RULES.items():
        if key not in cfg:
            cfg[key] = value
            _note(world, "config.%s missing (save from before Milestone 2): set "
                         "to %r so this world keeps its old rules" % (key, value))
    changed = 0
    for agent in world["agents"]:
        missing = [k for k in ("needs", "resting", "drain_acc", "tire_acc", "traits")
                   if k not in agent]
        for key in missing:
            agent[key] = copy.deepcopy(AGENT_DEFAULTS[key])
        changed += bool(missing)
    if changed:
        _note(world, "version 2 -> 3: %d agents given rest 100 and neutral traits "
                     "(curiosity 50, industriousness 50)" % changed)
    world["version"] = 3


def _migrate_3_to_4(world):
    cfg = world["config"]
    for key, value in MILESTONE2_RULES.items():
        if key not in cfg:
            cfg[key] = value
            _note(world, "config.%s missing (save from before homes): set to %r "
                         "so this world keeps its old rules" % (key, value))
    changed = 0
    for agent in world["agents"]:
        if "home" not in agent:
            agent["home"] = [agent["x"], agent["y"]]
            changed += 1
    if changed:
        _note(world, "version 3 -> 4: %d agents given a home where they stand now "
                     "(birthplaces were not recorded before version 4)" % changed)
    world["version"] = 4


MIGRATIONS = {1: _migrate_1_to_2, 2: _migrate_2_to_3, 3: _migrate_3_to_4}


def world_from_json(text):
    try:
        world = json.loads(text)
    except ValueError:
        raise ValueError("This is not a Genesis save file (not valid JSON).")
    if not isinstance(world, dict) or not isinstance(world.get("version"), int):
        raise ValueError("This is not a Genesis save file (no version number).")
    version = world["version"]
    if version > SAVE_VERSION or version < 1:
        raise ValueError("This save is format version %s; this program "
                         "understands versions 1 to %d."
                         % (version, SAVE_VERSION))
    missing = [k for k in REQUIRED_KEYS if k not in world]
    if missing:
        raise ValueError("This save is missing essential data: %s."
                         % ", ".join(missing))
    # Unknown extra keys are deliberately left in place, never discarded.
    try:
        while world["version"] < SAVE_VERSION:
            MIGRATIONS[world["version"]](world)
        _repair(world)
    except (KeyError, TypeError, AttributeError, IndexError):
        raise ValueError("This save file is damaged: its contents do not "
                         "have the shape Genesis expects.")
    return world


def save_world(world, path):
    """Write the world to a file. Writes a temp file first, then swaps it in,
    so a crash halfway can never leave a broken save behind."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    temp_path = path + ".tmp"
    with open(temp_path, "w", encoding="utf-8") as f:
        f.write(world_to_json(world))
    os.replace(temp_path, path)


def load_world(path):
    with open(path, "r", encoding="utf-8") as f:
        return world_from_json(f.read())


def fingerprint(world):
    """A short code that is the same only if two worlds are exactly equal.
    Handy for checking "same seed = same result" by eye."""
    return hashlib.sha256(world_to_json(world).encode("utf-8")).hexdigest()[:16]
