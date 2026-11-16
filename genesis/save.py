"""Saving and loading worlds.

A world is a plain dictionary, so a save file is just that dictionary
written as JSON text. You can open a save in any text editor.
"""

import hashlib
import json
import os

from .world import SAVE_VERSION


def world_to_json(world):
    # sort_keys makes the text identical for identical worlds.
    return json.dumps(world, sort_keys=True)


def world_from_json(text):
    world = json.loads(text)
    if not isinstance(world, dict) or world.get("version") != SAVE_VERSION:
        raise ValueError("This save file is not a version %d Genesis world."
                         % SAVE_VERSION)
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
