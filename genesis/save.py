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
}

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

    if "next_id" not in world:
        world["next_id"] = max([a["id"] for a in world["agents"]] + [0]) + 1
        _note(world, "next_id missing: set to %d" % world["next_id"])


def _migrate_1_to_2(world):
    world["version"] = 2   # same layout; the repair step does the real work


MIGRATIONS = {1: _migrate_1_to_2}


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
    while world["version"] < SAVE_VERSION:
        before = world["version"]
        MIGRATIONS[before](world)
    _repair(world)
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
