"""Milestone 2 against the frozen Milestone 1 baseline.

Runs the SAME code twice per seed: with the Milestone 2 defaults, and with
MILESTONE1_RULES (nobody rests, traits 50), which reproduces Milestone 1
exactly (tests/test_baseline.py). Also runs forced-trait worlds (every agent,
and every child, gets one fixed trait value) to see what each trait does.
Prints measurements only; it does not judge them.

Since homes (Milestone 3) "defaults" and the forced-trait rows have homes
on; "M2 rules (homes off)" reproduces Milestone 2. The Milestone 2 printout is
experiments/results/stage_compare.txt; the one with homes is
experiments/results/stage_compare_home.txt. Since the curiosity fix
(2026-11-18) "defaults" use the fixed rule and "defaults, old curiosity" the
old one; printout experiments/results/stage_compare_curiosity_fix.txt.

Run:  python3 experiments/stage_compare.py            (about 4 minutes)
      python3 experiments/stage_compare.py --quick    (2 seeds, 1500 ticks)
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, step  # noqa: E402
from genesis.save import MILESTONE1_RULES, MILESTONE2_RULES  # noqa: E402

SEEDS, TICKS = ["42", "1", "2", "3", "4"], 3000
if "--quick" in sys.argv:
    SEEDS, TICKS = ["42", "1"], 1500


def run(seed, rules, force=None):
    cfg = dict(rules)
    cfg["history_keep"] = 0
    if force:
        cfg["trait_mutation"] = 0
    w = create_world(seed, cfg)
    if force:
        for a in w["agents"]:
            a["traits"].update(force)
    pops, ages, young = [], [], 0
    acts = {"rest": 0, "move": 0, "gather": 0, "eat": 0, "reproduce": 0}
    rest_sum = rest_n = 0
    tiles, alive_ticks = {}, {}
    t0 = time.time()
    for _ in range(TICKS):
        for e in step(w):
            a = e["action"]
            if a == "die":
                ages.append(e["age"])
                young += e["age"] < w["config"]["repro_min_age"]
            elif a in acts:
                acts[a] += 1
                tiles.setdefault(e["agent"], set()).add((e["x"], e["y"]))
                alive_ticks[e["agent"]] = alive_ticks.get(e["agent"], 0) + 1
        pops.append(len(w["agents"]))
        for ag in w["agents"]:
            rest_sum += ag["needs"]["rest"]
            rest_n += 1
        if not w["agents"]:
            break
    secs = time.time() - t0
    s = w["stats"]
    deaths = s["deaths_starved"] + s["deaths_old_age"]
    decisions = float(sum(acts.values()))
    roam = [100.0 * len(tiles[i]) / alive_ticks[i] for i in tiles if alive_ticks[i] >= 50]
    living = w["agents"]
    return {"mean_pop": sum(pops[500:]) / float(len(pops[500:])), "end_pop": pops[-1],
            "births": s["births"], "starved_pct": 100.0 * s["deaths_starved"] / deaths,
            "age": sum(ages) / float(len(ages)), "young_pct": 100.0 * young / deaths,
            "rest_pct": 100.0 * acts["rest"] / decisions,
            "move_pct": 100.0 * acts["move"] / decisions,
            "gather_per_100": 100.0 * acts["gather"] / decisions,
            "mean_rest": rest_sum / float(rest_n),
            "tiles_per_100": sum(roam) / len(roam),
            "cur": sum(a["traits"]["curiosity"] for a in living) / float(len(living)),
            "ind": sum(a["traits"]["industriousness"] for a in living) / float(len(living)),
            "tps": len(pops) / secs, "extinct": len(pops) < TICKS}


def avg(rows, k):
    return sum(r[k] for r in rows) / float(len(rows))


def table(label, rows):
    return ("%-24s %6.1f %6.1f %7.0f %8.1f %6.0f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f %6.1f %5.0f  %d/%d" % (
        label, avg(rows, "mean_pop"), avg(rows, "end_pop"), avg(rows, "births"),
        avg(rows, "starved_pct"), avg(rows, "age"), avg(rows, "young_pct"),
        avg(rows, "rest_pct"), avg(rows, "mean_rest"), avg(rows, "tiles_per_100"),
        avg(rows, "gather_per_100"), avg(rows, "cur"), avg(rows, "ind"), avg(rows, "tps"),
        sum(r["extinct"] for r in rows), len(rows)))


def main():
    base = json.load(open(os.path.join(ROOT, "experiments", "baseline", "baseline.json")))["long"]
    print("seeds %s, %d ticks. Means over seeds. pop = mean population after tick 500."
          % (",".join(SEEDS), TICKS))
    print("%-24s %6s %6s %7s %8s %6s %6s %6s %6s %6s %6s %6s %6s %5s  %s" % (
        "run", "pop", "end", "births", "starved%", "age", "<80%", "rest%", "rest", "tiles",
        "gath%", "cur", "ind", "tick/s", "died out"))
    if TICKS == 3000 and SEEDS == ["42", "1", "2", "3", "4"]:
        b = list(base.values())
        print("%-24s %6.1f %6.1f %7.0f %8.1f %6.0f   (frozen baseline.json, Milestone 1 code)" % (
            "frozen M1 baseline", avg(b, "mean_pop_after_500"), avg(b, "end_pop"),
            avg(b, "births"), avg(b, "starved_share_pct"), avg(b, "mean_age_at_death")))
    runs = [("M1 rules (new code)", MILESTONE1_RULES, None),
            ("M2 rules (homes off)", MILESTONE2_RULES, None),
            ("defaults (homes on)", {}, None),
            ("defaults, old curiosity", {"curiosity_straight": 0}, None),
            ("all industrious 10", {}, {"industriousness": 10}),
            ("all industrious 90", {}, {"industriousness": 90}),
            ("all curiosity 10", {}, {"curiosity": 10}),
            ("all curiosity 90", {}, {"curiosity": 90})]
    for label, rules, force in runs:
        rows = [run(s, rules, force) for s in SEEDS]
        print(table(label, rows))
        sys.stdout.flush()
    print("rest% = share of decisions that are rest; rest = mean rest need of the living;")
    print("tiles = distinct tiles visited per 100 ticks of an agent's life; gath% = gathers per")
    print("100 decisions; cur/ind = mean trait of the living at the end; tick/s on this Mac.")


if __name__ == "__main__":
    main()
