"""Does curiosity really change behaviour?  A read-only measurement.

Curiosity (genesis/traits.py) has ONE effect in the code: the chance that a
WANDERING agent turns on a tick, 15% + (curiosity - 50) * 20 / 100, so
curiosity 10 -> 7%, 50 -> 15%, 90 -> 23%. Wandering happens only when the
agent sees no food it can walk to ("search") or its pack is full ("explore").
This script measures what that does, in two kinds of world:

  forced  every founder gets the same curiosity (10, 50 or 90) and children
          copy it (trait_mutation=0). Same seeds, so low and high share the
          same map and start: the per-seed difference high - low is paired.
  mixed   one world per seed; founders get 10, 50, 90 in turn (id % 3) and
          children copy it. The three groups share the same world at the
          same time, so food and luck are the same for all of them.

Everything else uses the code defaults. The script only READS events.

Run:  python3 experiments/curiosity_probe.py          (10 seeds x 3000 ticks, ~4 min)
      python3 experiments/curiosity_probe.py --mixed-extra  (mixed worlds only,
            30 more seeds 10..39, ~4 min)
Add --homes-off for the Milestone 2 world (MILESTONE2_RULES): that reproduces
curiosity_probe.json/.txt and curiosity_mixed_extra.json/.txt exactly.
Without it homes are on and files end in _home (curiosity_probe_home.json ...).
      python3 experiments/curiosity_probe.py --quick  (3 seeds x 1000 ticks)
Writes experiments/results/curiosity_probe.json (every per-seed number) and
prints the tables that docs/MILESTONE2_REPORT.md quotes
(experiments/results/curiosity_probe.txt is that printout).
"""
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step  # noqa: E402
from genesis.save import MILESTONE2_RULES  # noqa: E402

SEEDS = ["42", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
TICKS = 3000
if "--quick" in sys.argv:
    SEEDS, TICKS = ["42", "1", "2"], 1000
LEVELS = [("low", 10), ("neutral", 50), ("high", 90)]
# Milestone 2 results were made before homes existed. --homes-off uses
# MILESTONE2_RULES (homes, sharing and the family home off, memory 10 that
# never fades, the old curiosity rule), which reproduces them exactly (files
# without a suffix). Until 2026-11-18 it only set home_radius=0, which
# stopped matching once sharing (step 3) was on by default.
# Without it, homes are on (the default) and files get the suffix "_home".
HOMES_OFF = "--homes-off" in sys.argv
SUFFIX = "" if HOMES_OFF else "_home"
MIN_EPISODE = 10      # wander episodes at least this long count for straightness
WINDOW = 100          # displacement is measured over this many ticks of life


def move_kind(why):
    """Same classification as experiments/starvation_study.py."""
    if "no food within" in why:
        return "search"      # hungry-ish, nothing reachable in sight, wandering
    if "so exploring" in why:
        return "explore"     # pack full, not hungry, wandering
    return "to_food"         # walking toward food it can see


def new_group():
    return {"life_ticks": 0, "decisions": 0, "rest": 0, "gather": 0, "moves": 0,
            "wander_moves": 0, "wander_pairs": 0, "turns": 0,
            "ep_n": 0, "ep_len": 0, "straight_n": 0, "straight_sum": 0.0,
            "search_n": 0, "search_found": 0, "search_found_len": 0, "search_died": 0,
            "tiles_rates": [], "disp_sum": 0.0, "disp_n": 0,
            "born": 0, "born_dead": 0, "born_dead_never_fed": 0,
            "first_gather_age_sum": 0, "first_gather_n": 0,
            "deaths": 0, "starved": 0, "age_sum": 0, "alive_end": 0}


def close_episode(g, ag):
    """An agent stopped wandering: record length and straightness."""
    n = ag["ep_len"]
    if n == 0:
        return
    g["ep_n"] += 1
    g["ep_len"] += n
    if n >= MIN_EPISODE and ag["ep_path"] > 0:
        dx = ag["x"] - ag["ep_start"][0]
        dy = ag["y"] - ag["ep_start"][1]
        g["straight_n"] += 1
        g["straight_sum"] += math.hypot(dx, dy) / ag["ep_path"]
    ag["ep_len"], ag["ep_path"] = 0, 0.0


def close_search(g, ag, outcome):
    n = ag["search_len"]
    if n == 0:
        return
    g["search_n"] += 1
    if outcome == "found":
        g["search_found"] += 1
        g["search_found_len"] += n
    elif outcome == "died":
        g["search_died"] += 1
    ag["search_len"] = 0


def run(seed, mode, value=None):
    cfg = {"history_keep": 0, "trait_mutation": 0}
    if HOMES_OFF:
        cfg.update(MILESTONE2_RULES)
    w = create_world(seed, cfg)
    for a in w["agents"]:
        if mode == "forced":
            a["traits"]["curiosity"] = value
        else:
            a["traits"]["curiosity"] = LEVELS[a["id"] % 3][1]
    names = {v: n for n, v in LEVELS}
    groups = {n: new_group() for n, _ in LEVELS}
    track = {}

    def start(agent, born_in_run):
        track[agent["id"]] = {
            "g": names[agent["traits"]["curiosity"]], "x": agent["x"], "y": agent["y"],
            "life": 0, "tiles": {(agent["x"], agent["y"])}, "born": born_in_run,
            "fed": False, "last_dir": None, "was_wander": False,
            "ep_len": 0, "ep_path": 0.0, "ep_start": None, "search_len": 0,
            "anchor": (agent["x"], agent["y"])}
        if born_in_run:
            groups[track[agent["id"]]["g"]]["born"] += 1

    for a in w["agents"]:
        start(a, False)
    pops, births = [], 0
    t0 = time.time()
    for _ in range(TICKS):
        for e in step(w):
            act = e["action"]
            if act == "born":
                births += 1
                child = next(c for c in w["agents"] if c["id"] == e["agent"])
                start(child, True)
                continue
            ag = track[e["agent"]]
            g = groups[ag["g"]]
            if act == "die":
                close_episode(g, ag)
                close_search(g, ag, "died")
                g["deaths"] += 1
                g["age_sum"] += e["age"]
                if e["cause"] == "starved":
                    g["starved"] += 1
                if ag["born"]:
                    g["born_dead"] += 1
                    if not ag["fed"]:
                        g["born_dead_never_fed"] += 1
                if ag["life"] >= 50:
                    g["tiles_rates"].append(100.0 * len(ag["tiles"]) / ag["life"])
                del track[e["agent"]]
                continue

            ag["life"] += 1
            g["life_ticks"] += 1
            g["decisions"] += 1
            kind = move_kind(e["why"]) if act == "move" else act
            wander = kind in ("search", "explore")
            if act == "rest":
                g["rest"] += 1
            if act == "gather":
                g["gather"] += 1
                if not ag["fed"] and ag["born"]:
                    g["first_gather_age_sum"] += ag["life"]
                    g["first_gather_n"] += 1
                ag["fed"] = True

            # search episodes: how long until food comes into reachable sight
            if kind == "search":
                ag["search_len"] += 1
            elif ag["search_len"]:
                close_search(g, ag, "found" if kind in ("to_food", "gather") else "other")

            if act == "move":
                g["moves"] += 1
                d = (e["x"] - ag["x"], e["y"] - ag["y"])
                if wander:
                    g["wander_moves"] += 1
                    if ag["was_wander"] and ag["last_dir"] is not None:
                        g["wander_pairs"] += 1
                        g["turns"] += d != ag["last_dir"]
                    if ag["ep_len"] == 0:
                        ag["ep_start"] = (ag["x"], ag["y"])
                    ag["ep_len"] += 1
                    ag["ep_path"] += math.hypot(d[0], d[1])
                ag["last_dir"] = d
                ag["tiles"].add((e["x"], e["y"]))
            if not wander:
                close_episode(g, ag)
            ag["was_wander"] = wander
            ag["x"], ag["y"] = e["x"], e["y"]
            if ag["life"] % WINDOW == 0:
                g["disp_sum"] += math.hypot(ag["x"] - ag["anchor"][0], ag["y"] - ag["anchor"][1])
                g["disp_n"] += 1
                ag["anchor"] = (ag["x"], ag["y"])
        pops.append(len(w["agents"]))
        if not w["agents"]:
            break
    for aid, ag in track.items():
        g = groups[ag["g"]]
        close_episode(g, ag)
        g["alive_end"] += 1
        if ag["life"] >= 50:
            g["tiles_rates"].append(100.0 * len(ag["tiles"]) / ag["life"])
    after = pops[500:] or pops
    return {"seed": seed, "mode": mode, "value": value, "groups": groups,
            "mean_pop": sum(after) / float(len(after)), "end_pop": pops[-1],
            "births": births, "extinct": len(pops) < TICKS, "secs": time.time() - t0}


def metrics(g):
    """Turn raw counters into the numbers in the report (None if no data)."""
    def div(a, b, k=1.0):
        return k * a / b if b else None
    return {
        "tiles_per_100": div(sum(g["tiles_rates"]), len(g["tiles_rates"])),
        "disp_per_100": div(g["disp_sum"], g["disp_n"]),
        "turn_pct": div(g["turns"], g["wander_pairs"], 100),
        "straightness": div(g["straight_sum"], g["straight_n"]),
        "wander_pct": div(g["wander_moves"], g["decisions"], 100),
        "episode_len": div(g["ep_len"], g["ep_n"]),
        "search_found_pct": div(g["search_found"], g["search_n"], 100),
        "ticks_to_find": div(g["search_found_len"], g["search_found"]),
        "first_gather_age": div(g["first_gather_age_sum"], g["first_gather_n"]),
        "newborn_never_fed_pct": div(g["born_dead_never_fed"], g["born_dead"], 100),
        "gather_per_100": div(g["gather"], g["life_ticks"], 100),
        "rest_pct": div(g["rest"], g["decisions"], 100),
        "starved_pct": div(g["starved"], g["deaths"], 100),
        "age_at_death": div(g["age_sum"], g["deaths"]),
        "alive_end": g["alive_end"],
        "born": g["born"],
    }


COLUMNS = [("tiles_per_100", "tiles/100t", 1), ("disp_per_100", "disp/100t", 2),
           ("turn_pct", "turn%", 1), ("straightness", "straight", 3),
           ("wander_pct", "wander%", 1), ("episode_len", "ep.len", 1),
           ("search_found_pct", "found%", 1), ("ticks_to_find", "t.find", 2),
           ("first_gather_age", "1st.food", 1), ("newborn_never_fed_pct", "never%", 1),
           ("gather_per_100", "gath/100", 2), ("rest_pct", "rest%", 1),
           ("starved_pct", "starved%", 1), ("age_at_death", "age", 0)]


def stats(values):
    vals = [v for v in values if v is not None]
    n = len(vals)
    if not n:
        return None
    m = sum(vals) / n
    sd = math.sqrt(sum((v - m) ** 2 for v in vals) / (n - 1)) if n > 1 else 0.0
    return {"mean": m, "sd": sd, "min": min(vals), "max": max(vals), "n": n}


def fmt(s, d):
    if s is None:
        return "-"
    return "%.*f +/- %.*f" % (d, s["mean"], d, s["sd"])


def print_block(title, per_label):
    """per_label: list of (label, [metrics dict per seed])."""
    print(title)
    for key, head, d in COLUMNS:
        cells = [fmt(stats([m[key] for m in rows]), d) for _, rows in per_label]
        print("  %-11s" % head + "".join("%22s" % c for c in cells))


def paired(rows_lo, rows_hi, key):
    """Per-seed difference high - low; how many seeds agree on the sign."""
    diffs = [h[key] - l[key] for l, h in zip(rows_lo, rows_hi)
             if l[key] is not None and h[key] is not None]
    s = stats(diffs)
    pos = sum(d > 0 for d in diffs)
    return s, pos, len(diffs)


def mixed_extra():
    """Only the mixed-world lineage question, on 30 more seeds (10..39)."""
    seeds = [str(i) for i in range(10, 40)]
    rows = []
    for seed in seeds:
        r = run(seed, "mixed")
        rows.append({"seed": seed, "metrics": {n: metrics(r["groups"][n]) for n, _ in LEVELS}})
        sys.stderr.write("mixed extra seed %s: %.1fs\n" % (seed, r["secs"]))
    print("Mixed worlds, extra seeds %s..%s (%d seeds), %d ticks." % (seeds[0], seeds[-1], len(seeds), TICKS))
    if not HOMES_OFF:
        print("Homes ON (home_radius = code default).")
    print("%-11s" % "" + "".join("%22s" % ("%s (%d)" % (n, v)) for n, v in LEVELS))
    for key, head, d in [("alive_end", "alive end", 1), ("born", "born", 1),
                         ("gather_per_100", "gath/100", 2), ("starved_pct", "starved%", 1),
                         ("age_at_death", "age", 0), ("tiles_per_100", "tiles/100t", 1)]:
        cells = [fmt(stats([r["metrics"][n][key] for r in rows]), d) for n, _ in LEVELS]
        print("%-11s" % head + "".join("%22s" % c for c in cells))
    print("Per seed, high minus low:")
    for key, head, d in [("alive_end", "alive end", 1), ("born", "born", 1),
                         ("gather_per_100", "gath/100", 2)]:
        s, k, n = paired([r["metrics"]["low"] for r in rows], [r["metrics"]["high"] for r in rows], key)
        print("  %-11s %26s   positive in %d/%d seeds" % (head, fmt(s, d), k, n))
    zero = [sum(r["metrics"][n]["alive_end"] == 0 for r in rows) for n, _ in LEVELS]
    print("Seeds where the group is extinct at the end: low %d, neutral %d, high %d" % tuple(zero))
    path = os.path.join(ROOT, "experiments", "results", "curiosity_mixed_extra%s.json" % SUFFIX)
    with open(path, "w") as f:
        json.dump({"seeds": seeds, "ticks": TICKS, "rows": rows}, f, indent=1, sort_keys=True)


def main():
    if "--mixed-extra" in sys.argv:
        return mixed_extra()
    out = {"seeds": SEEDS, "ticks": TICKS, "levels": LEVELS, "forced": {}, "mixed": []}
    t_all = time.time()
    for name, value in LEVELS:
        out["forced"][name] = []
        for seed in SEEDS:
            r = run(seed, "forced", value)
            out["forced"][name].append({
                "seed": seed, "mean_pop": r["mean_pop"], "end_pop": r["end_pop"],
                "births": r["births"], "extinct": r["extinct"],
                "metrics": metrics(r["groups"][name])})
            sys.stderr.write("forced %s seed %s: %.1fs\n" % (name, seed, r["secs"]))
    for seed in SEEDS:
        r = run(seed, "mixed")
        out["mixed"].append({"seed": seed, "mean_pop": r["mean_pop"],
                             "end_pop": r["end_pop"], "extinct": r["extinct"],
                             "metrics": {n: metrics(r["groups"][n]) for n, _ in LEVELS}})
        sys.stderr.write("mixed seed %s: %.1fs\n" % (seed, r["secs"]))

    print("Curiosity probe: seeds %s, %d ticks each. Cells: mean +/- sd over seeds."
          % (",".join(SEEDS), TICKS))
    if not HOMES_OFF:
        print("Homes ON (home_radius = code default).")
    print("Turn chance while wandering: low (10) 7%, neutral (50) 15%, high (90) 23%.")
    print()
    fr = {n: [x["metrics"] for x in out["forced"][n]] for n, _ in LEVELS}
    print("%-13s" % "" + "".join("%22s" % ("%s (%d)" % (n, v)) for n, v in LEVELS))
    print_block("A. FORCED worlds (everyone has the same curiosity)",
                [(n, fr[n]) for n, _ in LEVELS])
    for key, head in [("mean_pop", "pop>500"), ("births", "births")]:
        cells = [fmt(stats([x[key] for x in out["forced"][n]]), 1) for n, _ in LEVELS]
        print("  %-11s" % head + "".join("%22s" % c for c in cells))
    ext = [sum(x["extinct"] for x in out["forced"][n]) for n, _ in LEVELS]
    print("  %-11s" % "died out" + "".join("%22s" % ("%d/%d" % (e, len(SEEDS))) for e in ext))
    print()
    mx = {n: [x["metrics"][n] for x in out["mixed"]] for n, _ in LEVELS}
    print_block("B. MIXED worlds (a third of founders each; same world, same time)",
                [(n, mx[n]) for n, _ in LEVELS])
    for key, head in [("alive_end", "alive end"), ("born", "born")]:
        cells = [fmt(stats([m[key] for m in mx[n]]), 1) for n, _ in LEVELS]
        print("  %-11s" % head + "".join("%22s" % c for c in cells))
    print()
    print("C. Is it luck? Per-seed difference HIGH minus LOW (same seed = same map).")
    print("   'k/n' = in how many seeds the difference is positive.")
    print("  %-11s %26s %8s %26s %8s" % ("", "forced: hi - lo", "", "mixed: hi - lo", ""))
    for key, head, d in COLUMNS + [("alive_end", "alive end", 1)]:
        if key == "alive_end":
            fcell, fk = "-", ""
        else:
            s, k, n = paired(fr["low"], fr["high"], key)
            fcell, fk = fmt(s, d), "%d/%d" % (k, n)
        s2, k2, n2 = paired(mx["low"], mx["high"], key)
        print("  %-11s %26s %8s %26s %8s" % (head, fcell, fk, fmt(s2, d), "%d/%d" % (k2, n2)))
    print()
    print("Legend: tiles/100t = distinct tiles visited per 100 ticks of life (agents living")
    print(">= 50 ticks); disp/100t = straight-line distance covered per 100 ticks of life;")
    print("turn% = wandering moves whose direction differs from the previous wandering move;")
    print("straight = net distance / path walked, wander stretches of >= %d moves (1 = a"
          % MIN_EPISODE)
    print("straight line); wander% = share of decisions that are wandering moves; ep.len =")
    print("mean wander stretch in moves; found% = search stretches that end with food in")
    print("reachable sight (the rest end in death or eating from the pack); t.find = moves")
    print("in a successful search stretch; 1st.food = age at first gather, agents born in")
    print("the run; never% = agents born in the run that died without ever gathering;")
    print("gath/100 = gathers per 100 ticks of life; rest% = share of decisions that rest;")
    print("starved% = share of deaths by starvation; age = mean age at death.")
    print("Total run time %.0f s." % (time.time() - t_all))

    if "--quick" not in sys.argv:
        path = os.path.join(ROOT, "experiments", "results", "curiosity_probe%s.json" % SUFFIX)
        with open(path, "w") as f:
            json.dump(out, f, indent=1, sort_keys=True)
        sys.stderr.write("wrote %s\n" % path)


if __name__ == "__main__":
    main()
