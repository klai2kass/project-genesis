"""What does sharing food do?  Measures only; the rule is in genesis/agents.py.

Same seeds, three settings of share_min_meetings: 0 (no sharing = the world
before step 3), 2 (default) and 5 (only with agents met 5+ times). Default
settings otherwise (homes, memory on), history off for speed.

Reports:
  world      population after tick 500, births, starved share of deaths,
             age at death, extinctions (the Milestone 2 bands)
  gifts      how many, how many went to family (parent/child/sibling)
  who dies   starvation deaths by age band
  receivers  of agents that got food: share still alive 20 ticks later
  givers     share of givers that starved within 100 ticks of giving
  return     of gifts a -> b, share where b later gave food to a; and of
             pairs with any gift, share with gifts both ways. NOTE: the rule
             never looks at past gifts, so any "return" comes only from the
             same agents living near each other and knowing each other.

Run:  python3 experiments/sharing_probe.py          (3 settings x 5 seeds x 3000 ticks, ~4 min)
      python3 experiments/sharing_probe.py --quick  (2 seeds x 1000 ticks)
Writes experiments/results/sharing_probe.json; printout in sharing_probe.txt.
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step  # noqa: E402

SEEDS = ["42", "1", "2", "3", "4"]
TICKS = 3000
if "--quick" in sys.argv:
    SEEDS, TICKS = ["42", "1"], 1000
WARMUP = 500
SETTINGS = [("no sharing (0)", 0), ("share, met 2+ (default)", 2), ("share, met 5+", 5)]
BANDS = [(0, 80, "0-79"), (80, 200, "80-199"), (200, 400, "200-399"), (400, 10 ** 9, "400+")]


def run(seed, share):
    w = create_world(seed, {"history_keep": 0, "share_min_meetings": share})
    parent = {a["id"]: a["parent"] for a in w["agents"]}
    pops = []
    starved_by_band = [0] * len(BANDS)
    deaths = starved = age_sum = 0
    gifts = []                       # (tick, giver, receiver)
    death_tick, death_cause = {}, {}
    for _ in range(TICKS):
        for e in step(w):
            a = e["action"]
            if a == "born":
                parent[e["agent"]] = next(c["parent"] for c in w["agents"]
                                          if c["id"] == e["agent"])
            elif a == "die":
                death_tick[e["agent"]] = e["tick"]
                death_cause[e["agent"]] = e["cause"]
                deaths += 1
                age_sum += e["age"]
                if e["cause"] == "starved":
                    starved += 1
                    for i, (lo, hi, _) in enumerate(BANDS):
                        if lo <= e["age"] < hi:
                            starved_by_band[i] += 1
            elif a == "give":
                gifts.append((e["tick"], e["agent"], e["to"]))
        pops.append(len(w["agents"]))
        if not w["agents"]:
            break

    def family(a, b):
        return (parent.get(a) == b or parent.get(b) == a
                or (parent.get(a) is not None and parent.get(a) == parent.get(b)))

    end = w["tick"]
    # receivers alive 20 ticks after their gift (only gifts with 20 ticks left)
    rec = [(t, b) for t, _, b in gifts if t + 20 <= end]
    rec_alive = sum(1 for t, b in rec if death_tick.get(b, 10 ** 9) > t + 20)
    giv = [(t, a) for t, a, _ in gifts if t + 100 <= end]
    giv_starved = sum(1 for t, a in giv if death_cause.get(a) == "starved"
                      and death_tick[a] <= t + 100)
    later = {}
    for t, a, b in gifts:
        later.setdefault((a, b), []).append(t)
    returned = sum(1 for t, a, b in gifts if any(t2 > t for t2 in later.get((b, a), [])))
    pairs = {tuple(sorted((a, b))) for _, a, b in gifts}
    both = sum(1 for p in pairs if (p[0], p[1]) in later and (p[1], p[0]) in later)
    after = pops[WARMUP:] or pops
    n = len(gifts)
    return {
        "seed": seed, "mean_pop": sum(after) / float(len(after)), "births": w["stats"]["births"],
        "starved_pct": 100.0 * starved / deaths, "age_at_death": age_sum / float(deaths),
        "extinct": len(pops) < TICKS, "gifts": n,
        "gifts_per_1000_ticks": 1000.0 * n / TICKS,
        "gifts_to_family_pct": 100.0 * sum(family(a, b) for _, a, b in gifts) / n if n else None,
        "starved_band_pct": [100.0 * c / starved for c in starved_by_band],
        "receivers_alive_20_pct": 100.0 * rec_alive / len(rec) if rec else None,
        "givers_starved_100_pct": 100.0 * giv_starved / len(giv) if giv else None,
        "returned_pct": 100.0 * returned / n if n else None,
        "pairs_both_ways_pct": 100.0 * both / len(pairs) if pairs else None,
        "distinct_pairs": len(pairs),
    }


def stats(v):
    v = [x for x in v if x is not None]
    if not v:
        return None
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return m, sd


def cell(v, d):
    s = stats(v)
    return "-" if s is None else "%.*f +/- %.*f" % (d, s[0], d, s[1])


def main():
    out = {"seeds": SEEDS, "ticks": TICKS, "settings": {}}
    for name, share in SETTINGS:
        out["settings"][name] = [run(s, share) for s in SEEDS]
        sys.stderr.write("%s done\n" % name)
    print("Sharing probe: seeds %s, %d ticks, default settings except share_min_meetings."
          % (",".join(SEEDS), TICKS))
    print("Cells: mean +/- sd over seeds.")
    print("%-40s" % "" + "".join("%26s" % n for n, _ in SETTINGS))
    rows = [("mean_pop", "population after tick 500", 1), ("births", "births", 0),
            ("starved_pct", "starved % of deaths", 1), ("age_at_death", "age at death", 0),
            ("gifts", "gifts of food", 0), ("gifts_per_1000_ticks", "gifts per 1,000 ticks", 1),
            ("distinct_pairs", "different giver-receiver pairs", 0),
            ("gifts_to_family_pct", "gifts to family %", 1),
            ("receivers_alive_20_pct", "receivers alive 20 ticks later %", 1),
            ("givers_starved_100_pct", "givers starved within 100 ticks %", 1),
            ("returned_pct", "gifts later returned b -> a %", 1),
            ("pairs_both_ways_pct", "pairs with gifts both ways %", 1)]
    for key, label, d in rows:
        print("%-40s" % label + "".join(
            "%26s" % cell([r[key] for r in out["settings"][n]], d) for n, _ in SETTINGS))
    for i, (_, _, band) in enumerate(BANDS):
        print("%-40s" % ("starvation deaths aged %s %%" % band) + "".join(
            "%26s" % cell([r["starved_band_pct"][i] for r in out["settings"][n]], 1)
            for n, _ in SETTINGS))
    ext = ["%d/%d" % (sum(r["extinct"] for r in out["settings"][n]), len(SEEDS))
           for n, _ in SETTINGS]
    print("%-40s" % "died out" + "".join("%26s" % e for e in ext))
    if "--quick" not in sys.argv:
        with open(os.path.join(ROOT, "experiments", "results", "sharing_probe.json"), "w") as f:
            json.dump(out, f, indent=1, sort_keys=True)


if __name__ == "__main__":
    main()
