"""Would memory have anything useful to DO?  A read-only count.

Candidate first use of encounter memory: a well-fed agent carrying food gives
one to a starving agent it knows. Before building anything like that, count
how often the situation even happens in today's world (default settings:
homes and memory on). Nothing is changed; the script only looks.

At the end of every tick (after memory is updated):
  starving   energy <= 20 and nothing in the pack
  giver      energy above eat_below (80, not hungry) and at least 1 food in the pack
  near       within 1 tile (the same distance as a meeting)
  familiar   the giver remembers 2+ separate meetings with it (standing
             near someone is itself a meeting, so "remembers it at all"
             would always be true and says nothing)
  friend     5+ meetings;  family = parent/child/sibling

Reports: of all starving agent-ticks, how many have a giver near (any, known,
familiar, family); and of all starvation deaths, how many had such a giver
near at some point in their last 20 ticks.

Run:  python3 experiments/sharing_opportunity.py    (5 seeds x 3000 ticks, ~1.5 min)
Writes experiments/results/sharing_opportunity.txt (printout) and .json.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step  # noqa: E402
from genesis.memory import meeting_pairs  # noqa: E402

SEEDS = ["42", "1", "2", "3", "4"]
TICKS = 3000
WARMUP = 500
LOOKBACK = 20
KINDS = ["any", "familiar", "friend", "family"]
LABELS = {"any": "anyone", "familiar": "someone who met it 2+ times",
          "friend": "someone who met it 5+ times", "family": "family"}


def is_family(a, b):
    return (a["parent"] == b["id"] or b["parent"] == a["id"]
            or (a["parent"] is not None and a["parent"] == b["parent"]))


def run(seed):
    w = create_world(seed, {"history_keep": 0})
    cfg = w["config"]
    starving_ticks = 0
    with_giver = dict.fromkeys(KINDS, 0)
    last_seen = {}            # starving agent id -> {kind: last tick a giver was near}
    deaths = 0
    deaths_with = dict.fromkeys(KINDS, 0)
    for _ in range(TICKS):
        events = step(w)
        t = w["tick"]
        if t <= WARMUP:
            continue
        for e in events:
            if e["action"] == "die" and e["cause"] == "starved":
                deaths += 1
                seen = last_seen.pop(e["agent"], {})
                for k in KINDS:
                    if k in seen and t - seen[k] <= LOOKBACK:
                        deaths_with[k] += 1
        found = {}
        for a, b in meeting_pairs(w["agents"], cfg["width"]):
            for giver, taker in ((a, b), (b, a)):
                if not (taker["energy"] <= 20 and taker["food"] == 0):
                    continue
                if not (giver["energy"] > cfg["eat_below"] and giver["food"] > 0):
                    continue
                kinds = found.setdefault(taker["id"], set())
                kinds.add("any")
                entry = next((m for m in giver["memory"] if m[0] == taker["id"]), None)
                if entry is not None and entry[3] >= 2:
                    kinds.add("familiar")
                    if entry[3] >= 5:
                        kinds.add("friend")
                if is_family(giver, taker):
                    kinds.add("family")
        for ag in w["agents"]:
            if ag["energy"] <= 20 and ag["food"] == 0:
                starving_ticks += 1
                for k in found.get(ag["id"], ()):
                    with_giver[k] += 1
                    last_seen.setdefault(ag["id"], {})[k] = t
    return {"seed": seed, "starving_ticks": starving_ticks, "with_giver": with_giver,
            "starved_deaths": deaths, "deaths_with_giver_near": deaths_with}


def main():
    rows = [run(s) for s in SEEDS]
    print("Sharing opportunity: default settings (homes, memory on), seeds %s, %d ticks,"
          % (",".join(SEEDS), TICKS))
    print("counted after tick %d. 'Giver' = not hungry and carrying food, within 1 tile." % WARMUP)
    print()

    def line(label, vals):
        m = sum(vals) / len(vals)
        sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1))
        print("  %-52s %6.1f%% +/- %4.1f" % (label, m, sd))

    print("Starving agent-ticks (energy <= 20, empty pack) with a giver near:")
    for k in KINDS:
        line("giver is %s" % LABELS[k],
             [100.0 * r["with_giver"][k] / r["starving_ticks"] for r in rows])
    print()
    print("Starvation deaths that had a giver near in their last %d ticks:" % LOOKBACK)
    for k in KINDS:
        line("giver is %s" % LABELS[k],
             [100.0 * r["deaths_with_giver_near"][k] / r["starved_deaths"] for r in rows])
    print()
    print("Starvation deaths counted: %d (per seed %s)."
          % (sum(r["starved_deaths"] for r in rows),
             ", ".join(str(r["starved_deaths"]) for r in rows)))
    with open(os.path.join(ROOT, "experiments", "results", "sharing_opportunity.json"), "w") as f:
        json.dump({"seeds": SEEDS, "ticks": TICKS, "warmup": WARMUP, "rows": rows}, f,
                  indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
