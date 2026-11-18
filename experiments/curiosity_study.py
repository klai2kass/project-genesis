"""Curiosity study: does curiosity change how agents explore? (read-only)

Worlds where EVERY agent has the same curiosity (10, 50 or 90) and neutral
industriousness (50). How it is set, from outside the simulation code:
  create_world(seed, {"trait_founder_min": 50, "trait_founder_max": 50,
                      "trait_mutation": 0})      (public settings: all traits 50)
  then each founder's agent["traits"]["curiosity"] = level (plain data);
  with trait_mutation 0 every child copies its parent, so the whole world
  keeps that level. Nothing in genesis/ is edited or patched. Trait dice are
  separate from the world's dice (genesis/traits.py), so the map, food and
  starting places are the same for every level.

Each agent is TRACKED for its first WINDOW ticks (from tick 0 for founders,
from birth for children; children born too late to finish a window are left
out). "Survivors" are alive at the end of their window; "early-dying" die
inside it. Every number is given for both groups, so a difference in
survival cannot pass for a difference in exploring.

Per agent, read only from the events and the agent's own fields:
  wander ticks      moves chosen by _wander (no reachable food in sight, or
                    pack full): why ends in "searching" / "so exploring";
                    "heading home" steps (Milestone 3 homes) are counted apart
  cells per 1,000   distinct tiles entered on wander ticks, per 1,000 wander
  wander ticks      ticks (MAIN METRIC; pooled per seed: sum of each agent's
                    distinct tiles / sum of its wander ticks x 1,000)
  distance          straight-line tiles from its start tile to where it is at
                    the END of its window (or where it died)
  turns             share of free wander ticks on which its heading changed
  water turns       share of free wander ticks on which the tile ahead was
                    water (a forced turn: an "obstacle hit")
  wander share      wander ticks / ticks alive (diagnostic only)
  first food        ticks until its first "gather" (no gather: left out)
  food eaten        "eat" events per 100 ticks alive
  resting           share of ticks spent resting
  starved           share of agents that starve inside their window

Spread: per seed means, then mean, sd, min and max over seeds, and a per-seed
table of the main metric. Raw per-seed numbers are saved as JSON.

Run:  python3 experiments/curiosity_study.py --out before
      (3 levels x 30 seeds x 1,500 ticks, two worlds: homes on as today and
       homes off; about 10 minutes)
      --rule old|new   only after the curiosity fix: choose the turn rule
                       (setting curiosity_straight 0 / 1); without it the
                       code default is used
      --quick          3 seeds x 600 ticks, nothing saved
Writes experiments/results/curiosity_<out>.txt and .json.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step  # noqa: E402
from genesis.agents import DIRS  # noqa: E402
from genesis.config import DEFAULT_CONFIG  # noqa: E402
from genesis.world import is_land  # noqa: E402

LEVELS = [10, 50, 90]
SEEDS = [str(i) for i in range(1, 31)]
TICKS = 1500
WINDOW = 300
WORLDS = [("homes on (today's default)", {}), ("homes off", {"home_radius": 0})]
if "--quick" in sys.argv:
    SEEDS, TICKS = ["1", "2", "3"], 600


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


RULE = arg("--rule")
OUT = arg("--out", "study")


def settings(extra):
    cfg = {"trait_founder_min": 50, "trait_founder_max": 50, "trait_mutation": 0,
           "history_keep": 0}
    cfg.update(extra)
    if RULE is not None:
        if "curiosity_straight" not in DEFAULT_CONFIG:
            sys.exit("--rule needs the curiosity_straight setting (after the fix)")
        cfg["curiosity_straight"] = {"old": 0, "new": 1}[RULE]
    return cfg


def run(seed, level, extra):
    w = create_world(seed, settings(extra))
    for a in w["agents"]:
        a["traits"]["curiosity"] = level
    track = {}                 # id -> per-agent record while tracked
    done = []

    def start(a, t0):
        track[a["id"]] = {"t0": t0, "start": (a["x"], a["y"]), "alive": 0,
                          "wander": 0, "home_steps": 0, "cells": set(), "turns": 0,
                          "water": 0, "free": 0, "first_food": None, "eaten": 0,
                          "rest": 0, "heading": a["heading"], "pos": (a["x"], a["y"])}

    for a in w["agents"]:
        start(a, 0)
    for _ in range(TICKS):
        before = {a["id"]: (a["x"], a["y"], a["heading"]) for a in w["agents"]}
        events = step(w)
        t = w["tick"]
        by_id = {a["id"]: a for a in w["agents"]}
        for e in events:
            r = track.get(e["agent"])
            act = e["action"]
            if act == "born":
                if t + WINDOW <= TICKS:
                    start(by_id[e["agent"]], t)
                continue
            if r is None:
                continue
            if act == "die":
                r["end"], r["died"], r["cause"] = (e["x"], e["y"]), True, e["cause"]
                done.append(track.pop(e["agent"]))
                continue
            r["alive"] += 1
            if act == "move" and (e["why"].endswith("searching")
                                  or e["why"].endswith("so exploring")):
                r["wander"] += 1
                r["free"] += 1
                r["cells"].add((e["x"], e["y"]))
                x0, y0, h0 = before[e["agent"]]
                dx, dy = DIRS[h0]
                if not is_land(w, x0 + dx, y0 + dy):
                    r["water"] += 1
                if by_id[e["agent"]]["heading"] != h0:
                    r["turns"] += 1
            elif act == "move" and "heading home" in e["why"]:
                r["wander"] += 1
                r["home_steps"] += 1
                r["cells"].add((e["x"], e["y"]))
            elif act == "gather" and r["first_food"] is None:
                r["first_food"] = t - r["t0"]
            elif act == "eat":
                r["eaten"] += 1
            elif act == "rest":
                r["rest"] += 1
        # end of window: stop tracking survivors
        for aid in [i for i, r in track.items() if t - r["t0"] >= WINDOW]:
            r = track.pop(aid)
            a = by_id[aid]
            r["end"], r["died"], r["cause"] = (a["x"], a["y"]), False, None
            done.append(r)
    return summarize(done)


def summarize(done):
    out = {}
    for group, keep in (("survivors", lambda r: not r["died"]),
                        ("early-dying", lambda r: r["died"]), ("all", lambda r: True)):
        rs = [r for r in done if keep(r)]
        wander = sum(r["wander"] for r in rs)
        free = sum(r["free"] for r in rs)
        alive = sum(r["alive"] for r in rs)
        ff = [r["first_food"] for r in rs if r["first_food"] is not None]

        def avg(v):
            return sum(v) / float(len(v)) if v else None
        out[group] = {
            "agents": len(rs),
            "cells_per_1000_wander": 1000.0 * sum(len(r["cells"]) for r in rs) / wander
            if wander else None,
            "distance": avg([math.hypot(r["end"][0] - r["start"][0], r["end"][1] - r["start"][1])
                             for r in rs]),
            "turns_pct": 100.0 * sum(r["turns"] for r in rs) / free if free else None,
            "water_turns_pct": 100.0 * sum(r["water"] for r in rs) / free if free else None,
            "wander_share_pct": 100.0 * wander / alive if alive else None,
            "home_steps_pct_of_wander": 100.0 * sum(r["home_steps"] for r in rs) / wander
            if wander else None,
            "first_food": avg(ff),
            "never_found_food_pct": 100.0 * (len(rs) - len(ff)) / len(rs) if rs else None,
            "eaten_per_100": 100.0 * sum(r["eaten"] for r in rs) / alive if alive else None,
            "rest_pct": 100.0 * sum(r["rest"] for r in rs) / alive if alive else None,
            "ticks_alive": avg([r["alive"] for r in rs]),
        }
    n = len(done)
    out["starved_pct"] = 100.0 * sum(r["cause"] == "starved" for r in done) / n if n else None
    return out


def spread(v):
    v = [x for x in v if x is not None]
    if not v:
        return "-"
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return "%.1f sd %.1f [%.1f..%.1f]" % (m, sd, min(v), max(v))


ROWS = [("cells_per_1000_wander", "cells / 1,000 wander ticks (MAIN)"),
        ("distance", "distance from start at end"),
        ("turns_pct", "turns % of free wander ticks"),
        ("water_turns_pct", "water ahead % of free wander"),
        ("wander_share_pct", "wander share % (diagnostic)"),
        ("home_steps_pct_of_wander", "home steps % of wander"),
        ("first_food", "ticks to first food"),
        ("never_found_food_pct", "never gathered food %"),
        ("eaten_per_100", "food eaten per 100 ticks"),
        ("rest_pct", "resting % of ticks"),
        ("ticks_alive", "ticks alive in window"),
        ("agents", "agents tracked")]


def main():
    res = {"seeds": SEEDS, "ticks": TICKS, "window": WINDOW, "levels": LEVELS,
           "rule": RULE or "code default", "worlds": {}}
    lines = ["Curiosity study: every agent at one curiosity, industriousness 50.",
             "Seeds %s..%s (%d), %d ticks, each agent tracked %d ticks. Turn rule: %s."
             % (SEEDS[0], SEEDS[-1], len(SEEDS), TICKS, WINDOW, res["rule"]),
             "Cells: mean sd [min..max] over seeds of the per-seed value."]
    for wname, extra in WORLDS:
        per = {lv: [run(s, lv, extra) for s in SEEDS] for lv in LEVELS}
        sys.stderr.write("%s done\n" % wname)
        res["worlds"][wname] = {str(lv): per[lv] for lv in LEVELS}
        lines += ["", "=== %s ===" % wname,
                  "%-36s" % "starved % of tracked agents" + "".join(
                      "%30s" % spread([r["starved_pct"] for r in per[lv]]) for lv in LEVELS)]
        for group in ("survivors", "early-dying"):
            lines += ["", "-- %s --" % group,
                      "%-36s" % "" + "".join("%30s" % ("curiosity %d" % lv) for lv in LEVELS)]
            for key, label in ROWS:
                lines.append("%-36s" % label + "".join(
                    "%30s" % spread([r[group][key] for r in per[lv]]) for lv in LEVELS))
        lines += ["", "Per seed, survivors, cells / 1,000 wander ticks:",
                  "%-6s" % "seed" + "".join("%14s" % ("cur %d" % lv) for lv in LEVELS)
                  + "%16s" % "90 minus 10"]
        for i, s in enumerate(SEEDS):
            vals = [per[lv][i]["survivors"]["cells_per_1000_wander"] for lv in LEVELS]
            lines.append("%-6s" % s + "".join("%14.1f" % v for v in vals)
                         + "%16.1f" % (vals[-1] - vals[0]))
        diffs = [per[90][i]["survivors"]["cells_per_1000_wander"]
                 - per[10][i]["survivors"]["cells_per_1000_wander"] for i in range(len(SEEDS))]
        lines.append("curiosity 90 explores more (survivors) in %d of %d seeds"
                     % (sum(d > 0 for d in diffs), len(diffs)))
    text = "\n".join(lines)
    print(text)
    if "--quick" not in sys.argv:
        base = os.path.join(ROOT, "experiments", "results", "curiosity_" + OUT)
        with open(base + ".txt", "w") as f:
            f.write(text + "\n")
        with open(base + ".json", "w") as f:
            json.dump(res, f, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
