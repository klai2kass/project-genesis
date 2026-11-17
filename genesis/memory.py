"""Encounter memory (Milestone 3, step 2): who did I meet, when, where.

A MEETING is two living agents standing within 1 tile of each other (the 8
tiles around, or the same tile) at the end of a tick. While they stay that
close it is ONE meeting; walking apart and coming back is a new one.

Each agent keeps a short list, agent["memory"], one entry per agent it met:

    [other_id, first_tick, last_tick, meetings, x, y]

    first_tick  tick of the very first meeting
    last_tick   last tick they were within 1 tile
    meetings    how many separate meetings
    x, y        where THIS agent stood when the latest meeting began

How "same meeting" is known without saving anything extra: memory is updated
every tick, so an entry whose last_tick is the previous tick means they were
together a moment ago and still are.

At most `memory_keep` entries (config, default 10; 0 = no memory). When the
list is too long, the agent forgets the one it met the FEWEST times (ties:
met longest ago, then the lower id), but never someone it is meeting right
now unless everyone in the list is. So close contacts are kept and a new
face gets a place by pushing out an old passing acquaintance.
Chosen by measurement (experiments/memory_probe.py, docs/MILESTONE3.md): the
first rule, "forget whoever was met longest ago", kept only about half of the
agents met 5+ times and reset a friend's count to 1 after forgetting it.
Whole numbers, fixed order, no dice.

Memory is a RECORD only: nothing in decide() reads it, so the world behaves
exactly as without it (tests/test_memory.py checks this against the frozen
reference experiments/baseline/milestone3_home.json).
"""


def meeting_pairs(agents):
    """Every pair (a, b) of agents within 1 tile, a["id"] < b["id"], in a fixed
    order. A grid of 2 x 2 tile cells keeps it to one pass over the agents."""
    cells = {}
    for a in agents:
        cells.setdefault((a["x"] // 2, a["y"] // 2), []).append(a)
    pairs = []
    for a in agents:
        cx, cy = a["x"] // 2, a["y"] // 2
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for b in cells.get((cx + dx, cy + dy), ()):
                    if (b["id"] > a["id"] and abs(a["x"] - b["x"]) <= 1
                            and abs(a["y"] - b["y"]) <= 1):
                        pairs.append((a, b))
    pairs.sort(key=lambda p: (p[0]["id"], p[1]["id"]))
    return pairs


def _remember(agent, other_id, tick):
    """Note that `agent` is within 1 tile of `other_id` at `tick`.
    Returns True if this starts a new meeting."""
    for entry in agent["memory"]:
        if entry[0] == other_id:
            if entry[2] == tick - 1:          # together last tick: same meeting
                entry[2] = tick
                return False
            entry[2] = tick
            entry[3] += 1
            entry[4], entry[5] = agent["x"], agent["y"]
            return True
    agent["memory"].append([other_id, tick, tick, 1, agent["x"], agent["y"]])
    return True


def _trim(agent, keep):
    mem = agent["memory"]
    while len(mem) > keep:
        newest = max(e[2] for e in mem)
        pool = [e for e in mem if e[2] != newest] or mem
        mem.remove(min(pool, key=lambda e: (e[3], e[2], e[0])))


def update_memories(world):
    """Called once per tick by sim.step, after every agent has acted.
    Returns the number of NEW meetings that started this tick."""
    keep = world["config"]["memory_keep"]
    if keep <= 0:
        return 0
    tick = world["tick"]
    started = 0
    touched = set()
    for a, b in meeting_pairs(world["agents"]):
        started += _remember(a, b["id"], tick)
        _remember(b, a["id"], tick)
        touched.add(a["id"])
        touched.add(b["id"])
    for agent in world["agents"]:
        if agent["id"] in touched and len(agent["memory"]) > keep:
            _trim(agent, keep)
    return started


def strongest(agent, n=5):
    """The n entries with the most meetings (ties: met more recently, then
    lower id). For the page and reports."""
    return sorted(agent["memory"], key=lambda e: (-e[3], -e[2], e[0]))[:n]
