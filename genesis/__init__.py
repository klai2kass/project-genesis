"""Project Genesis: the simulation core.

Nothing in this folder knows about windows, browsers or web servers.
That is on purpose: the world can run "headless" (no UI) for tests.
"""

from .world import create_world
from .sim import step, run
from .save import world_to_json, world_from_json, save_world, load_world, fingerprint

__all__ = [
    "create_world",
    "step",
    "run",
    "world_to_json",
    "world_from_json",
    "save_world",
    "load_world",
    "fingerprint",
]
