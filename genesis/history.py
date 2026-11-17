"""Each agent's recent decisions, kept INSIDE the world so saves carry them.

Layout in the world dictionary (ids are text because JSON keys are text):
    world["history"]       {"12": [record, record, ...], ...}   oldest first
    world["history_dead"]  ["7", "9", ...]  ids of dead agents still kept,
                           oldest death first

A record is a short list, to keep save files small:
    [tick, action, x, y, need, why, options]
    options = [[action, 1 or 0, note], ...]

Limits (settings, so they can be changed with --set):
    history_keep       how many recent records are kept per agent
    dead_history_keep  how many dead agents' histories are kept
When a limit is reached the OLDEST records / the longest-dead agents go
first. Nothing here uses dice, so it never affects how the world behaves.
"""


def record(world, event):
    """Store one decision event in its agent's history."""
    cfg = world["config"]
    keep = cfg["history_keep"]
    if keep <= 0:
        return
    key = str(event["agent"])
    store = world["history"]
    records = store.get(key)
    if records is None:
        records = store[key] = []
    records.append([event["tick"], event["action"], event["x"], event["y"],
                    event["need"], event["why"],
                    [[o["action"], 1 if o["ok"] else 0, o["note"]]
                     for o in event["options"]]])
    if len(records) > keep:
        del records[:len(records) - keep]

    if event["action"] == "die":
        dead = world["history_dead"]
        dead.append(key)
        while len(dead) > cfg["dead_history_keep"]:
            store.pop(dead.pop(0), None)


def events_for(world, agent_id):
    """An agent's kept history as event-shaped dicts (what the page and
    format_decision expect). Empty list if nothing is kept."""
    out = []
    for tick, action, x, y, need, why, options in world["history"].get(str(agent_id), []):
        out.append({"tick": tick, "agent": agent_id, "action": action,
                    "need": need, "why": why, "x": x, "y": y,
                    "options": [{"action": a, "ok": bool(ok), "note": n}
                                for a, ok, n in options]})
    return out
