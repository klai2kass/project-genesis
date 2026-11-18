"""Are there GROUPS?  A read-only measurement (Milestone 3, step 4).

Builds a "know each other well" network from the agents' own memories
(genesis/memory.py) and looks for groups in it. Nothing in the simulation is
changed; the script only looks.

  tie        two LIVING agents that BOTH remember at least K separate
             meetings with each other (K = 5 main, K = 2 for comparison)
  group      a connected set of 3 or more agents (a friend of a friend of a
             friend ... is in the same group)
  snapshot   taken every 250 ticks from tick 500 to the end

For every snapshot:
  - number of groups, sizes, share of living agents that are in a group
  - share of ties inside a group that are family (parent/child/sibling)
  - how spread out members' homes are (mean distance from the group's
    average home, in tiles)
Does a group last?
  - kept: of a group's members still alive 250 ticks later, the largest
    share found together in ONE later group (1.0 = all still together)
  - traced: follow a group from snapshot to snapshot: at each step, take the
    later group holding most of its living members; the trace goes on while
    that group holds at least half of them (and at least 2 are alive). The
    group of the next step is followed next, so members can change: like a
    village, a group can outlive everyone who started it. Reported: mean
    ticks a group can be traced, the share traced 1,000+ ticks (about three
    lifetimes; only groups starting at least 1,000 ticks before the end
    count), and of those, the share in which every first member has died.
For gifts (sharing): of the gifts in the 250 ticks after a snapshot, the
share between two members of the same group, next to the share of all
"met 2+ times" pairs that lie inside a group (what chance alone would give).

Three worlds per seed: the family home (home_inherit=1: a child takes its
parent's home), the default world (home_inherit=0: home = birth tile, the
step 1-4 rule) and homes off (home_radius=0) as the control. Also reported per world:
population after tick 500, births, starved share and age at death, to check
the Milestone 2 bands.

Run:  python3 experiments/community_probe.py          (3 worlds x 5 seeds x 3000 ticks, ~6 min)
      python3 experiments/community_probe.py --quick  (2 seeds x 1500 ticks)
Writes experiments/results/community_probe.json; printout in community_probe.txt.
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
    SEEDS, TICKS = ["42", "1"], 1500
FIRST, EVERY = 500, 250
THRESHOLDS = [5, 2]
WORLDS = [("family home", {"home_inherit": 1}),
          ("birth-tile home (default)", {"home_inherit": 0}),
          ("homes off (control)", {"home_radius": 0, "home_inherit": 0})]


def ties(agents, k):
    """Mutual ties between living agents: both remember k+ meetings."""
    alive = {a["id"]: a for a in agents}
    strong = {a["id"]: {e[0] for e in a["memory"] if e[3] >= k and e[0] in alive}
              for a in agents}
    return {(a, b) for a, bs in strong.items() for b in bs if a < b and a in strong.get(b, ())}


def groups_of(edges):
    """Connected groups of 3+ agents. Fixed order (sorted), no chance."""
    nbr = {}
    for a, b in sorted(edges):
        nbr.setdefault(a, []).append(b)
        nbr.setdefault(b, []).append(a)
    seen, out = set(), []
    for start in sorted(nbr):
        if start in seen:
            continue
        comp, todo = [], [start]
        seen.add(start)
        while todo:
            n = todo.pop()
            comp.append(n)
            for m in nbr[n]:
                if m not in seen:
                    seen.add(m)
                    todo.append(m)
        if len(comp) >= 3:
            out.append(frozenset(comp))
    return out


def trace(snaps, i, group, k):
    """(steps, all_first_members_dead) following `group` from snapshot i."""
    cur, n = group, 0
    for j in range(i + 1, len(snaps)):
        survivors = cur & snaps[j]["alive"]
        if len(survivors) < 2:
            break
        later = snaps[j]["k"][k]["groups"]
        best = max(later, key=lambda h: (len(survivors & h), -min(h)), default=None)
        if best is None or len(survivors & best) * 2 < len(survivors):
            break
        n += 1
        cur = best
    # every first member has died by the last snapshot the trace reached
    gone = n > 0 and not (group & snaps[i + n]["alive"])
    return n, gone


def kept(group, later_groups, alive_later):
    survivors = group & alive_later
    if len(survivors) < 2:
        return None
    best = max([len(survivors & h) for h in later_groups] or [0])
    return best / float(len(survivors))


def run(seed, extra):
    w = create_world(seed, dict({"history_keep": 0}, **extra))
    parent = {a["id"]: a["parent"] for a in w["agents"]}
    snaps = []                  # per snapshot: tick, alive ids, homes, groups per K, ties
    gifts = []                  # (tick, giver, receiver)
    pops, ages = [], []
    for _ in range(TICKS):
        for e in step(w):
            if e["action"] == "die":
                ages.append(e["age"])
            if e["action"] == "born":
                parent[e["agent"]] = next(c["parent"] for c in w["agents"] if c["id"] == e["agent"])
            elif e["action"] == "give":
                gifts.append((e["tick"], e["agent"], e["to"]))
        t = w["tick"]
        pops.append(len(w["agents"]))
        if t >= FIRST and (t - FIRST) % EVERY == 0:
            snap = {"tick": t, "alive": {a["id"] for a in w["agents"]},
                    "home": {a["id"]: a["home"] for a in w["agents"]}, "k": {}}
            for k in THRESHOLDS + [2]:
                e2 = ties(w["agents"], k)
                snap["k"][k] = {"ties": e2, "groups": groups_of(e2)}
            snaps.append(snap)

    def family(a, b):
        return (parent.get(a) == b or parent.get(b) == a
                or (parent.get(a) is not None and parent.get(a) == parent.get(b)))

    st = w["stats"]
    out = {"seed": seed,
           "world": {"mean_pop": sum(pops[FIRST:]) / float(len(pops[FIRST:])),
                     "births": st["births"],
                     "starved_pct": 100.0 * st["deaths_starved"]
                     / (st["deaths_starved"] + st["deaths_old_age"]),
                     "age_at_death": sum(ages) / float(len(ages)),
                     "gifts": st["gifts"], "extinct": int(not w["agents"])}}
    for k in THRESHOLDS:
        n_groups, in_group, sizes, biggest, fam, spread = [], [], [], [], [], []
        kept250, traced, long_, long_gone = [], [], 0, 0
        gift_in, gift_n, ref_in, ref_n = 0, 0, 0, 0
        for i, s in enumerate(snaps):
            gs = s["k"][k]["groups"]
            n_groups.append(len(gs))
            members = set().union(*gs) if gs else set()
            in_group.append(100.0 * len(members) / max(1, len(s["alive"])))
            sizes.extend(len(g) for g in gs)
            biggest.append(max([len(g) for g in gs] or [0]))
            where = {m: j for j, g in enumerate(gs) for m in g}
            inside = [p for p in s["k"][k]["ties"] if p[0] in where and where[p[0]] == where.get(p[1])]
            if inside:
                fam.append(100.0 * sum(family(a, b) for a, b in inside) / len(inside))
            for g in gs:
                hs = [s["home"][m] for m in g]
                cx = sum(h[0] for h in hs) / float(len(hs))
                cy = sum(h[1] for h in hs) / float(len(hs))
                spread.append(sum(math.hypot(h[0] - cx, h[1] - cy) for h in hs) / len(hs))
            if i + 1 < len(snaps):
                later = snaps[i + 1]
                for g in gs:
                    v = kept(g, later["k"][k]["groups"], later["alive"])
                    if v is not None:
                        kept250.append(v)
            if i + 4 < len(snaps):          # 1,000+ ticks of room left
                for g in gs:
                    n, gone = trace(snaps, i, g, k)
                    traced.append(n * EVERY)
                    if n >= 4:
                        long_ += 1
                        long_gone += gone
            # gifts in the next 250 ticks: inside a group?
            for t, a, b in gifts:
                if s["tick"] < t <= s["tick"] + EVERY and a in s["alive"] and b in s["alive"]:
                    gift_n += 1
                    gift_in += a in where and where[a] == where.get(b)
            for a, b in s["k"][2]["ties"]:
                ref_n += 1
                ref_in += a in where and where[a] == where.get(b)

        def mean(v):
            return sum(v) / float(len(v)) if v else None
        out["K%d" % k] = {"groups_per_snapshot": mean(n_groups), "in_group_pct": mean(in_group),
                  "group_size": mean(sizes), "biggest_group": mean(biggest),
                  "family_ties_pct": mean(fam), "home_spread": mean(spread),
                  "kept_250_pct": 100.0 * mean(kept250) if kept250 else None,
                  "traced_ticks": mean(traced),
                  "traced_1000_pct": 100.0 * long_ / len(traced) if traced else None,
                  "outlived_founders_pct": 100.0 * long_gone / long_ if long_ else None,
                  "gifts_inside_pct": 100.0 * gift_in / gift_n if gift_n else None,
                  "known_pairs_inside_pct": 100.0 * ref_in / ref_n if ref_n else None,
                  "gifts_counted": gift_n}
    return out


def stats(v):
    v = [x for x in v if x is not None]
    if not v:
        return "-"
    m = sum(v) / len(v)
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
    return "%.1f +/- %.1f" % (m, sd)


ROWS = [("groups_per_snapshot", "groups (3+ agents) per snapshot"),
        ("in_group_pct", "living agents in a group %"),
        ("group_size", "group size, mean"),
        ("biggest_group", "biggest group, mean"),
        ("family_ties_pct", "ties inside groups that are family %"),
        ("home_spread", "home spread in a group (tiles)"),
        ("kept_250_pct", "kept together 250 ticks later %"),
        ("traced_ticks", "group can be traced, ticks (mean)"),
        ("traced_1000_pct", "groups traced 1,000+ ticks %"),
        ("outlived_founders_pct", "  of those, all first members dead %"),
        ("gifts_inside_pct", "gifts inside a group %"),
        ("known_pairs_inside_pct", "  vs met-2+ pairs inside a group %"),
        ("gifts_counted", "gifts counted")]


def main():
    out = {"seeds": SEEDS, "ticks": TICKS, "first": FIRST, "every": EVERY, "worlds": {}}
    for name, extra in WORLDS:
        out["worlds"][name] = [run(s, extra) for s in SEEDS]
        sys.stderr.write("%s done\n" % name)
    print("Community probe: seeds %s, %d ticks, snapshot every %d ticks from tick %d."
          % (",".join(SEEDS), TICKS, EVERY, FIRST))
    print("Tie = both living agents remember K+ meetings with each other. Group = 3+")
    print("agents connected by ties. Cells: mean over snapshots, then mean +/- sd over seeds.")
    print()
    print("== The world (Milestone 2 bands: pop 80-98, starved 62-73, births 830-1010, age 265-325) ==")
    print("%-42s" % "" + "".join("%28s" % n for n, _ in WORLDS))
    for key, label in [("mean_pop", "population after tick 500"), ("births", "births"),
                       ("starved_pct", "starved % of deaths"), ("age_at_death", "age at death"),
                       ("gifts", "gifts of food"), ("extinct", "died out (0/1)")]:
        print("%-42s" % label + "".join(
            "%28s" % stats([r["world"][key] for r in out["worlds"][n]]) for n, _ in WORLDS))
    for k in THRESHOLDS:
        print()
        print("== K = %d ==" % k)
        print("%-42s" % "" + "".join("%28s" % n for n, _ in WORLDS))
        for key, label in ROWS:
            print("%-42s" % label + "".join(
                "%28s" % stats([r["K%d" % k][key] for r in out["worlds"][n]]) for n, _ in WORLDS))
    if "--quick" not in sys.argv:
        with open(os.path.join(ROOT, "experiments", "results", "community_probe.json"), "w") as f:
            json.dump(out, f, indent=1, sort_keys=True,
                      default=lambda o: sorted(o) if isinstance(o, (set, frozenset)) else str(o))


if __name__ == "__main__":
    main()
