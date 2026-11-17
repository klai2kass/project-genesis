"""Do traits get SELECTED, or do they only drift by chance?  Read-only.

Runs the default world (founders 40-60, children parent +/-5) and a neutral
CONTROL that is identical except that traits do nothing:
turn_span=0 (everyone turns 15% of the time) and tire_span=0 (everyone tires
1 rest per move). In the control any change in the average trait is pure
chance (drift). If the real run moves further than the control does across
seeds, the trait is being selected.

Run:  python3 experiments/trait_drift.py          (10 seeds x 3000 ticks, ~2 min)
Writes experiments/results/trait_drift.json; printout in trait_drift.txt.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step  # noqa: E402

SEEDS = ["42", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
TICKS = 3000
VARIANTS = [("real (defaults)", {}),
            ("control (traits do nothing)", {"turn_span": 0, "tire_span": 0})]


def run(seed, extra):
    cfg = {"history_keep": 0}
    cfg.update(extra)
    w = create_world(seed, cfg)
    start = {k: sum(a["traits"][k] for a in w["agents"]) / float(len(w["agents"]))
             for k in ("curiosity", "industriousness")}
    for _ in range(TICKS):
        step(w)
    living = w["agents"]
    end = {k: sum(a["traits"][k] for a in living) / float(len(living))
           for k in ("curiosity", "industriousness")}
    spread = {k: math.sqrt(sum((a["traits"][k] - end[k]) ** 2 for a in living) / len(living))
              for k in ("curiosity", "industriousness")}
    return {"seed": seed, "start": start, "end": end, "spread_end": spread,
            "max_generation": max(a["generation"] for a in living), "pop": len(living)}


def sd(v):
    m = sum(v) / len(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))


def main():
    out = {"seeds": SEEDS, "ticks": TICKS, "variants": {}}
    print("Trait drift: seeds %s, %d ticks. Change = (mean trait of the living at the end)"
          % (",".join(SEEDS), TICKS))
    print("minus (mean trait of the founders). Cells: mean +/- sd over seeds [min .. max].")
    for name, extra in VARIANTS:
        rows = [run(s, extra) for s in SEEDS]
        out["variants"][name] = rows
        print()
        print("== %s ==" % name)
        for k in ("curiosity", "industriousness"):
            ch = [r["end"][k] - r["start"][k] for r in rows]
            sp = [r["spread_end"][k] for r in rows]
            print("  %-16s change %+5.1f +/- %4.1f [%+5.1f .. %+5.1f]   spread within world at end %4.1f"
                  % (k, sum(ch) / len(ch), sd(ch), min(ch), max(ch), sum(sp) / len(sp)))
        gens = [r["max_generation"] for r in rows]
        print("  deepest generation alive at the end: %.1f (min %d, max %d)"
              % (sum(gens) / float(len(gens)), min(gens), max(gens)))
        sys.stdout.flush()
    with open(os.path.join(ROOT, "experiments", "results", "trait_drift.json"), "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
