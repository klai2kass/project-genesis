"""Do agents meet the SAME individuals again?  A read-only measurement.

Question behind it: is "recognise individuals and remember encounters" worth
building next? Remembering someone only matters if you meet them again. This
script runs the default world (code defaults except home_radius) and only LOOKS:

  meeting    two living agents stand within 1 tile of each other (they touch)
  encounter  a pair STARTS a meeting (they were not within 1 tile last tick)
  in sight   two agents within `vision` tiles (4) of each other
  reunion    a repeat encounter after at least 100 ticks since the pair last
             STARTED a meeting (so not just two neighbours drifting apart
             and back)

It reports how often agents meet, how many different agents each one meets,
how often an encounter is a REPEAT (the pair met before), how much of it is
family (parent/child, siblings), how long between repeats, and how far an
agent's life spreads over the map (home range).

It compares three settings of the real "home" rule (genesis/agents.py,
_step_home): home_radius 0 (homes off = Milestone 2), 6 (the default) and 3.
(Before homes were built, this script tested a throwaway prototype of the
same idea; that version and its results are in commit 2e4d82a.)

Run:  python3 experiments/encounter_probe.py           (3 variants x 5 seeds x 3000 ticks, ~3 min)
      python3 experiments/encounter_probe.py --quick   (2 seeds x 1000 ticks)
Writes experiments/results/encounter_probe.json; the printout is saved as
experiments/results/encounter_probe.txt.
"""
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step  # noqa: E402

SEEDS = ["42", "1", "2", "3", "4"]
TICKS = 3000
if "--quick" in sys.argv:
    SEEDS, TICKS = ["42", "1"], 1000
WARMUP = 500   # count encounters only after the start-up boom
LONG_GAP = 100  # a repeat after at least this many ticks apart is a real reunion

def pairs_within(agents, r):
    """All pairs (id_a < id_b) with Chebyshev distance <= r, via a grid."""
    cells = {}
    for a in agents:
        cells.setdefault((a["x"] // (r + 1), a["y"] // (r + 1)), []).append(a)
    out = set()
    for (cx, cy), here in cells.items():
        near = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                near.extend(cells.get((cx + dx, cy + dy), ()))
        for a in here:
            for b in near:
                if a["id"] < b["id"] and max(abs(a["x"] - b["x"]), abs(a["y"] - b["y"])) <= r:
                    out.add((a["id"], b["id"]))
    return out


def run(seed, home_radius):
    w = create_world(seed, {"history_keep": 0, "home_radius": home_radius})
    pops = []
    vision = w["config"]["vision"]
    parent = {a["id"]: a["parent"] for a in w["agents"]}
    pos = {}                     # id -> list of (x, y) over its observed life
    touching = set()
    met = {}                     # pair -> [count, last_tick]
    enc = rep = kin_enc = kin_rep = long_rep = 0
    gaps = []
    life_ticks = 0
    sight_sum = 0
    partners = {}                # id -> set of ids met (encounters)
    lives = []                   # (life ticks, distinct partners, repeat encounters) of the dead
    seen_life = {}
    t0 = time.time()
    for _ in range(TICKS):
        for e in step(w):
            if e["action"] == "born":
                parent[e["agent"]] = next(c for c in w["agents"] if c["id"] == e["agent"])["parent"]
            elif e["action"] == "die":
                i = e["agent"]
                if w["tick"] > WARMUP and seen_life.get(i, 0) >= 50:
                    lives.append((seen_life[i], len(partners.get(i, ())), pos.get(i, [])))
                pos.pop(i, None)
        t = w["tick"]
        agents = w["agents"]
        pops.append(len(agents))
        for a in agents:
            pos.setdefault(a["id"], []).append((a["x"], a["y"]))
            seen_life[a["id"]] = seen_life.get(a["id"], 0) + 1
        now = pairs_within(agents, 1)
        if t > WARMUP:
            life_ticks += len(agents)
            sight_sum += 2 * len(pairs_within(agents, vision))
            for p in now - touching:
                a, b = p
                is_kin = (parent.get(a) == b or parent.get(b) == a
                          or (parent.get(a) is not None and parent.get(a) == parent.get(b)))
                enc += 1
                kin_enc += is_kin
                if p in met:
                    rep += 1
                    kin_rep += is_kin
                    gaps.append(t - met[p][1])
                    met[p][0] += 1
                    if t - met[p][1] >= LONG_GAP:
                        long_rep += 1
                        met[p][2] += 1
                else:
                    met[p] = [1, t, 0]
                met[p][1] = t
                partners.setdefault(a, set()).add(b)
                partners.setdefault(b, set()).add(a)
        touching = now
    st = w["stats"]

    def spread(path):
        """Radius of gyration: typical distance from the centre of its life."""
        if not path:
            return 0.0
        mx = sum(p[0] for p in path) / float(len(path))
        my = sum(p[1] for p in path) / float(len(path))
        return math.sqrt(sum((p[0] - mx) ** 2 + (p[1] - my) ** 2 for p in path) / len(path))

    counts = [c for c, _, _ in met.values()]
    gaps.sort()
    return {
        "seed": seed,
        "encounters_per_agent_per_100": 100.0 * 2 * enc / life_ticks,
        "in_sight_avg": sight_sum / float(life_ticks),
        "repeat_pct": 100.0 * rep / enc,
        "kin_pct_of_encounters": 100.0 * kin_enc / enc,
        "kin_pct_of_repeats": 100.0 * kin_rep / rep if rep else 0.0,
        "pairs": len(met),
        "pairs_met_2plus_pct": 100.0 * sum(c >= 2 for c in counts) / len(counts),
        "pairs_met_5plus_pct": 100.0 * sum(c >= 5 for c in counts) / len(counts),
        "reunion_pct_of_encounters": 100.0 * long_rep / enc,
        "pairs_reunited_pct": 100.0 * sum(r >= 1 for _, _, r in met.values()) / len(met),
        "repeat_gap_median": gaps[len(gaps) // 2] if gaps else None,
        "repeat_gap_p90": gaps[int(len(gaps) * 0.9)] if gaps else None,
        "partners_per_life": sum(n for _, n, _ in lives) / float(len(lives)),
        "life_ticks_mean": sum(l for l, _, _ in lives) / float(len(lives)),
        "home_range_radius": sum(spread(p) for _, _, p in lives) / float(len(lives)),
        "lives_counted": len(lives),
        "mean_pop": sum(pops[WARMUP:]) / float(len(pops[WARMUP:])),
        "starved_pct": 100.0 * st["deaths_starved"] / (st["deaths_starved"] + st["deaths_old_age"]),
        "births": st["births"],
        "secs": time.time() - t0,
    }


KEYS = [("encounters_per_agent_per_100", "encounters per agent per 100 ticks", 1),
        ("in_sight_avg", "other agents in sight (4 tiles), average", 1),
        ("repeat_pct", "encounters that are a repeat (%)", 1),
        ("pairs_met_2plus_pct", "pairs that meet 2+ times (%)", 1),
        ("pairs_met_5plus_pct", "pairs that meet 5+ times (%)", 1),
        ("reunion_pct_of_encounters", "encounters after >= 100 ticks apart (%)", 1),
        ("pairs_reunited_pct", "pairs that meet again after >= 100 ticks (%)", 1),
        ("repeat_gap_median", "ticks between repeats, median", 0),
        ("repeat_gap_p90", "ticks between repeats, 90th percentile", 0),
        ("kin_pct_of_encounters", "encounters that are family (%)", 1),
        ("kin_pct_of_repeats", "repeats that are family (%)", 1),
        ("partners_per_life", "different agents met in a life", 1),
        ("life_ticks_mean", "observed life of those agents (ticks)", 0),
        ("home_range_radius", "home range radius (tiles; map is 60 x 40)", 1),
        ("mean_pop", "population after tick 500, mean", 1),
        ("starved_pct", "deaths by starvation (%)", 1),
        ("births", "births", 0)]
VARIANTS = [("homes off (home_radius 0 = Milestone 2)", 0),
            ("homes, home_radius 6 (default)", 6), ("homes, home_radius 3", 3)]


def main():
    out = {"seeds": SEEDS, "ticks": TICKS, "warmup": WARMUP, "long_gap": LONG_GAP,
           "variants": {}}
    print("Encounter probe: seeds %s, %d ticks, counted after tick %d."
          % (",".join(SEEDS), TICKS, WARMUP))
    print("Meeting = within 1 tile. Family = parent/child or same parent. Home range and")
    print("partners: agents that died after tick %d having lived >= 50 ticks." % WARMUP)
    for name, radius in VARIANTS:
        rows = []
        for s in SEEDS:
            rows.append(run(s, radius))
            sys.stderr.write("%s seed %s: %.1fs\n" % (name, s, rows[-1]["secs"]))
        out["variants"][name] = rows
        print()
        print("== %s ==" % name)
        print("%-44s %10s %8s %8s %8s" % ("", "mean", "sd", "min", "max"))
        for k, label, d in KEYS:
            vals = [r[k] for r in rows if r[k] is not None]
            m = sum(vals) / len(vals)
            sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (len(vals) - 1)) if len(vals) > 1 else 0
            print("%-44s %10.*f %8.*f %8.*f %8.*f" % (label, d, m, d, sd, d, min(vals), d, max(vals)))
        sys.stdout.flush()
    if "--quick" not in sys.argv:
        path = os.path.join(ROOT, "experiments", "results", "encounter_probe.json")
        with open(path, "w") as f:
            json.dump(out, f, indent=1, sort_keys=True)
        sys.stderr.write("wrote %s\n" % path)


if __name__ == "__main__":
    main()
