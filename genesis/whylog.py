"""Turning decision records into text a person can read.

Every decision made in `agents.py` is a small record with a need, the
options considered and a reason. The functions here only format them.
"""


def format_decision(event):
    """One decision as a few readable lines."""
    lines = ["tick %d   %s   (now at %d, %d)"
             % (event["tick"], event["action"].upper(), event["x"], event["y"])]
    if event.get("need"):
        lines.append("  need     " + event["need"])
    for i, option in enumerate(event.get("options", [])):
        if option["action"] == event["action"]:
            verdict = "CHOSEN"       # the first rule that fitted
        elif option["ok"]:
            verdict = "could"        # would also fit, but comes later in the order
        else:
            verdict = "no"
        label = "  options  " if i == 0 else "           "
        lines.append("%s%-10s %-7s %s" % (label, option["action"], verdict,
                                          option["note"]))
    lines.append("  why      " + event["why"])
    return "\n".join(lines)


def format_agent_history(agent_id, events, world):
    """The last decisions of one agent, newest last, with a status line."""
    agent = next((a for a in world["agents"] if a["id"] == agent_id), None)
    if agent is not None:
        status = ("alive at tick %d: energy %d, age %d of %d, carrying %d food, "
                  "generation %d" % (world["tick"], agent["energy"], agent["age"],
                                     agent["max_age"], agent["food"],
                                     agent["generation"]))
    elif events and events[-1]["action"] == "die":
        status = "died at tick %d" % events[-1]["tick"]
    elif agent_id >= world["next_id"] or agent_id < 1:
        return ("There is no agent #%d. So far the ids go from 1 to %d."
                % (agent_id, world["next_id"] - 1))
    else:
        status = "no longer alive"

    lines = ["Agent #%d: %s" % (agent_id, status)]
    if events:
        lines.append("Its last %d decision%s (oldest first):"
                     % (len(events), "" if len(events) == 1 else "s"))
        for event in events:
            lines.append("")
            lines.append(format_decision(event))
    else:
        lines.append("It did nothing in the ticks that were run.")
    return "\n".join(lines)


def format_agent_list(world):
    """A short table of everyone alive, to help pick an agent to inspect."""
    lines = ["%d agents alive at tick %d (seed %s):"
             % (len(world["agents"]), world["tick"], world["seed"]),
             "%6s %7s %5s %5s  %s" % ("id", "energy", "age", "food", "last action")]
    for agent in world["agents"]:
        lines.append("%6s %7d %5d %5d  %s"
                     % ("#%d" % agent["id"], agent["energy"], agent["age"],
                        agent["food"], agent["last_action"]))
    return "\n".join(lines)
