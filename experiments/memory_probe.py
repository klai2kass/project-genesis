"""What do agents remember, what does it cost, and what does the cap forget?

Encounter memory (genesis/memory.py) never changes behaviour, so a world run
with memory_keep=10 (the default) and the same world with memory_keep=1000
(nothing ever forgotten) have EXACTLY the same agents doing exactly the same
things. Comparing the two shows what the cap of 10 throws away.

For every agent alive at the end and at least 200 ticks old ("adults"):
  - how many agents it remembers, and its most-met agent
  - how many of its remembered agents are family (parent, child, sibling)
  - "friends": agents it met 5+ times (true count from the uncapped memory);
    what share of them the capped memory still holds
  - whether its living parent / living siblings are still remembered
Plus the cost: ticks per second and save size, memory on (10) vs off (0),
default settings (history on), same seeds.

Run:  python3 experiments/memory_probe.py           (5 seeds x 3000 ticks, ~3 min)
      python3 experiments/memory_probe.py --quick   (2 seeds x 1000 ticks)
Writes experiments/results/memory_probe.json; printout in memory_probe.txt.
"""
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step, world_to_json  # noqa: E402
from genesis.digest import behaviour_digest  # noqa: E402

SEEDS = ["42", "1", "2", "3", "4"]
TICKS = 3000
if "--quick" in sys.argv:
    SEEDS, TICKS = ["42", "1"], 1000
ADULT = 200
FRIEND = 5


def timed_run(seed, keep):
    w = create_world(seed, {"memory_keep": keep})
    t0 = time.time()
    for _ in range(TICKS):
        step(w)
    return w, time.time() - t0


def family(a, b_id, living):
    b = living.get(b_id)
    if b_id == a["parent"]:
        return "parent"
    if b is not None and b["parent"] == a["id"]:
        return "child"
    if b is not None and a["parent"] is not None and b["parent"] == a["parent"]:
        return "sibling"
    return None


def analyse(capped, full):
    """capped, full: the same world (same behaviour) with keep 10 and 1000."""
    assert behaviour_digest(capped) == behaviour_digest(full)
    living = {a["id"]: a for a in capped["agents"]}
    fullmem = {a["id"]: {e[0]: e for e in a["memory"]} for a in full["agents"]}
    adults = [a for a in capped["agents"] if a["age"] >= ADULT]
    known, top, fam_share, friends_total, friends_kept = [], [], [], 0, 0
    has_friend = 0
    kin_total = kin_kept = 0
    for a in adults:
        mem = {e[0]: e for e in a["memory"]}
        known.append(len(mem))
        top.append(max([e[3] for e in mem.values()] or [0]))
        if mem:
            fam_share.append(sum(1 for i in mem if family(a, i, living)) / float(len(mem)))
        friends = [i for i, e in fullmem[a["id"]].items() if e[3] >= FRIEND]
        friends_total += len(friends)
        friends_kept += sum(1 for i in friends if i in mem)
        has_friend += any(e[3] >= FRIEND for e in mem.values())
        # living close family: parent and siblings that are alive now
        kin = [b["id"] for b in capped["agents"]
               if b["id"] != a["id"] and family(a, b["id"], living) in ("parent", "sibling")]
        kin_met = [i for i in kin if i in fullmem[a["id"]]]
        kin_total += len(kin_met)
        kin_kept += sum(1 for i in kin_met if i in mem)
    full_known = [len(fullmem[a["id"]]) for a in adults]
    n = float(len(adults))
    return {"adults": len(adults),
            "known_mean": sum(known) / n,
            "known_full_mean": sum(full_known) / n,
            "full_memory_pct": 100.0 * sum(k >= capped["config"]["memory_keep"] for k in known) / n,
            "most_met_mean": sum(top) / n,
            "family_share_of_memory_pct": 100.0 * sum(fam_share) / max(1, len(fam_share)),
            "adults_with_a_friend_pct": 100.0 * has_friend / n,
            "friends_per_adult_full": friends_total / n,
            "friends_kept_pct": 100.0 * friends_kept / max(1, friends_total),
            "met_kin_kept_pct": 100.0 * kin_kept / max(1, kin_total)}


def main():
    rows = []
    for seed in SEEDS:
        capped, t_on = timed_run(seed, 10)
        full, _ = timed_run(seed, 1000)
        off, t_off = timed_run(seed, 0)
        r = analyse(capped, full)
        r.update({"seed": seed, "ticks_per_s_on": TICKS / t_on, "ticks_per_s_off": TICKS / t_off,
                  "save_kb_on": len(world_to_json(capped)) / 1000.0,
                  "save_kb_off": len(world_to_json(off)) / 1000.0,
                  "same_behaviour_on_off": behaviour_digest(capped) == behaviour_digest(off)})
        rows.append(r)
        sys.stderr.write("seed %s done\n" % seed)
    keys = [("adults", "adults (alive at end, age >= %d)" % ADULT, 1),
            ("known_mean", "agents remembered (cap 10)", 1),
            ("known_full_mean", "agents met in life so far (no cap)", 1),
            ("full_memory_pct", "adults whose memory is full (%)", 1),
            ("most_met_mean", "meetings with its most-met agent", 1),
            ("family_share_of_memory_pct", "remembered agents that are family (%)", 1),
            ("adults_with_a_friend_pct", "adults remembering someone met 5+ times (%)", 1),
            ("friends_per_adult_full", "agents met 5+ times, per adult (no cap)", 2),
            ("friends_kept_pct", "of those, still in the capped memory (%)", 1),
            ("met_kin_kept_pct", "living parent/siblings met, still remembered (%)", 1),
            ("ticks_per_s_on", "ticks per second, memory on", 0),
            ("ticks_per_s_off", "ticks per second, memory off", 0),
            ("save_kb_on", "save size at the end, KB, memory on", 0),
            ("save_kb_off", "save size at the end, KB, memory off", 0)]
    print("Memory probe: default settings (homes on, history on), seeds %s, %d ticks."
          % (",".join(SEEDS), TICKS))
    print("Same world with memory_keep 10, 1000 and 0 (behaviour identical: %s)."
          % all(r["same_behaviour_on_off"] for r in rows))
    print("%-48s %9s %7s %8s %8s" % ("", "mean", "sd", "min", "max"))
    for k, label, d in keys:
        v = [r[k] for r in rows]
        m = sum(v) / len(v)
        sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
        print("%-48s %9.*f %7.*f %8.*f %8.*f" % (label, d, m, d, sd, d, min(v), d, max(v)))
    if "--quick" not in sys.argv:
        with open(os.path.join(ROOT, "experiments", "results", "memory_probe.json"), "w") as f:
            json.dump({"seeds": SEEDS, "ticks": TICKS, "rows": rows}, f, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
