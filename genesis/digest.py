"""Short codes that say "did behaviour change?" even when new fields appear.

`fingerprint()` hashes the WHOLE world, so adding any new agent field (like
needs or traits) changes it even if every agent behaves exactly as before.
These two codes look only at behaviour:

  behaviour_digest(world)  the old core state: map, food, dice position,
                           counters and the old agent fields. New fields are
                           ignored.
  EventDigest              hashes (tick, agent, action, x, y) of every event.
                           The words (why / need / options) are ignored, so
                           better explanations never count as a change.

Reading only; nothing here touches the world or the dice.
"""

import hashlib
import json

CORE_AGENT_FIELDS = ["id", "x", "y", "energy", "age", "max_age", "food",
                     "heading", "cooldown", "parent", "generation", "target"]


def behaviour_digest(world):
    core = {
        "tick": world["tick"], "rng": world["rng"], "terrain": world["terrain"],
        "food": world["food"], "next_id": world["next_id"],
        "stats": {k: world["stats"][k]
                  for k in ("births", "deaths_starved", "deaths_old_age")},
        "agents": [[a[k] for k in CORE_AGENT_FIELDS] for a in world["agents"]],
    }
    return hashlib.sha256(json.dumps(core, sort_keys=True).encode("utf-8")).hexdigest()[:16]


class EventDigest:
    def __init__(self):
        self._h = hashlib.sha256()

    def add(self, events):
        for e in events:
            self._h.update(("%d,%d,%s,%d,%d;" % (e["tick"], e["agent"], e["action"],
                                                  e["x"], e["y"])).encode("utf-8"))

    def hexdigest(self):
        return self._h.hexdigest()[:16]
