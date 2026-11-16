"""The heartbeat of the world: `step()` moves time forward by one tick.

`step()` changes the world and returns a list of events. Every agent
decision becomes one event holding its need, the options it considered and
a short "why", so you can always ask "why did agent #12 do that?".
"""

from .agents import DIRS, decide
from .rng import Rng
from .world import is_land, make_agent, tile_index


def step(world):
    """Advance the world by one tick. Returns the list of events."""
    cfg = world["config"]
    rng = Rng(world["rng"])
    world["tick"] += 1
    tick = world["tick"]
    events = []

    def log(agent, action, why, need=None, options=None):
        # x, y is where the agent stands AFTER the action.
        events.append({"tick": tick, "agent": agent["id"], "action": action,
                       "need": need, "options": options or [], "why": why,
                       "x": agent["x"], "y": agent["y"]})

    _regrow_food(world, rng)

    survivors = []
    newborns = []
    # Agents always act in the same order (oldest id first), never at random.
    for agent in world["agents"]:
        # Living costs 1 energy per tick.
        agent["age"] += 1
        agent["energy"] -= 1
        if agent["cooldown"] > 0:
            agent["cooldown"] -= 1

        if agent["energy"] <= 0:
            world["stats"]["deaths_starved"] += 1
            log(agent, "die", "starved: energy ran out at age %d" % agent["age"])
            continue
        if agent["age"] >= agent["max_age"]:
            world["stats"]["deaths_old_age"] += 1
            log(agent, "die", "old age: reached its lifespan of %d ticks"
                % agent["max_age"])
            continue

        decision = decide(world, agent, rng)
        child = _apply(world, agent, decision, rng)
        agent["last_action"] = decision["action"]
        agent["last_why"] = decision["why"]
        log(agent, decision["action"], decision["why"],
            decision["need"], decision["options"])
        survivors.append(agent)

        if child is not None:
            newborns.append(child)
            world["stats"]["births"] += 1
            log(child, "born", "child of #%d (generation %d)"
                % (agent["id"], child["generation"]))

    # Newborns join at the end and take their first turn next tick.
    world["agents"] = survivors + newborns
    world["rng"] = rng.state
    return events


def run(world, ticks):
    """Run many ticks in a row. Returns every event that happened."""
    events = []
    for _ in range(ticks):
        events.extend(step(world))
    return events


def _regrow_food(world, rng):
    """A few random tiles each grow 1 food, if they are below their cap."""
    cfg = world["config"]
    terrain, food, caps = world["terrain"], world["food"], cfg["food_cap"]
    for _ in range(cfg["regrow_per_tick"]):
        i = rng.below(len(food))
        if food[i] < caps[terrain[i]]:
            food[i] += 1


def _apply(world, agent, decision, rng):
    """Carry out a decision. Returns a new child agent, or None."""
    cfg = world["config"]
    action = decision["action"]

    if action == "eat":
        agent["food"] -= 1
        agent["energy"] = min(cfg["max_energy"],
                              agent["energy"] + cfg["food_energy"])
    elif action == "gather":
        world["food"][tile_index(world, agent["x"], agent["y"])] -= 1
        agent["food"] += 1
    elif action == "move":
        agent["x"] += decision["dx"]
        agent["y"] += decision["dy"]
        agent["heading"] = decision["heading"]
    elif action == "reproduce":
        agent["energy"] -= cfg["repro_cost"]
        agent["cooldown"] = cfg["repro_cooldown"]
        # The child appears on a free neighbouring land tile (or the same tile).
        spots = [(agent["x"] + dx, agent["y"] + dy) for dx, dy in DIRS
                 if is_land(world, agent["x"] + dx, agent["y"] + dy)]
        cx, cy = rng.choice(spots) if spots else (agent["x"], agent["y"])
        child = make_agent(world["next_id"], cx, cy, cfg["repro_cost"], 0, rng,
                           cfg, parent=agent["id"],
                           generation=agent["generation"] + 1)
        world["next_id"] += 1
        return child
    # "rest" changes nothing.
    return None
