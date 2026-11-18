"""How far does a family's home move from one generation to the next?

With home_inherit=0 a child's home is the tile where it was born, next to
wherever its parent stood (up to about 6-7 tiles from the parent's own
home), so a family's home drifts a little every generation. With the family
home (home_inherit=1, measured in step 5, off by default) it should not move.
Both are run. Read-only; history off.

Reports per seed: mean distance (steps) from a child's home to its parent's
home, and for agents of generation 10 or more alive at the end, the
straight-line distance from their home to their founder's home.

Run:  python3 experiments/home_drift.py      (2 settings x 5 seeds x 3000 ticks, ~1 min)
Printout saved as experiments/results/home_drift.txt.
"""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step  # noqa: E402

SEEDS = ["42", "1", "2", "3", "4"]
TICKS = 3000


def main():
    for inherit in (0, 1):
        report(inherit)
        print()


def report(inherit):
    print("Home drift: home_inherit=%d (%s), seeds %s, %d ticks."
          % (inherit, "family home" if inherit else "birth-tile home", ",".join(SEEDS), TICKS))
    print("%-6s %28s %40s" % ("seed", "child home to parent home", "generation 10+: home to founder's home"))
    for seed in SEEDS:
        w = create_world(seed, {"history_keep": 0, "home_inherit": inherit})
        home = {a["id"]: a["home"] for a in w["agents"]}
        root = {a["id"]: a["id"] for a in w["agents"]}
        gen = {a["id"]: 0 for a in w["agents"]}
        steps = []
        for _ in range(TICKS):
            for e in step(w):
                if e["action"] == "born":
                    c = next(x for x in w["agents"] if x["id"] == e["agent"])
                    p = c["parent"]
                    home[c["id"]], root[c["id"]], gen[c["id"]] = c["home"], root[p], gen[p] + 1
                    steps.append(max(abs(c["home"][0] - home[p][0]), abs(c["home"][1] - home[p][1])))
        far = [math.hypot(a["home"][0] - home[root[a["id"]]][0], a["home"][1] - home[root[a["id"]]][1])
               for a in w["agents"] if gen[a["id"]] >= 10]
        print("%-6s %18.1f tiles (n=%4d) %28.1f tiles (n=%3d)"
              % (seed, sum(steps) / len(steps), len(steps), sum(far) / max(1, len(far)), len(far)))


if __name__ == "__main__":
    main()
