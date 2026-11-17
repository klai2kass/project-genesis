"""Why do agents starve?  A read-only study of the simulation.

It runs `step()` exactly as the real program does and only LOOKS at the
events and the world. It changes no setting and no code default, so the
world is identical to a normal run (check: the end fingerprint it prints for
seed 42 / 500 ticks equals run_headless.py's).

Run:
    python3 experiments/starvation_study.py            # default settings, 5 seeds x 3000 ticks
    python3 experiments/starvation_study.py --sweep    # repro_cost, food_energy, repro_cooldown
Options: --ticks N   --seeds 42,1,2   --set name=value (repeatable)

Anything marked "approx" is measured from a snapshot taken at the START of
the tick, not at the exact moment of death.
"""
import argparse
import os
import sys
from collections import Counter, deque

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from genesis import create_world, fingerprint, step  # noqa: E402
from genesis.agents import _food_in_box, _steps_to  # noqa: E402

SEEDS = ["42", "1", "2", "3", "4"]
TICKS = 3000
BANDS = [(0, 50, "0-49 (still on birth reserve)"), (50, 80, "50-79 (young)"),
         (80, 200, "80-199"), (200, 400, "200-399"), (400, 10 ** 9, "400+")]
KINDS = ["eat", "gather", "reproduce", "to_food", "search", "explore", "rest"]


def band(age):
    for i, (lo, hi, _) in enumerate(BANDS):
        if lo <= age < hi:
            return i
    return len(BANDS) - 1


def move_kind(why):
    if "no food within" in why:
        return "search"      # nothing reachable in sight, wandering
    if "so exploring" in why:
        return "explore"     # pack full, not hungry
    return "to_food"         # walking toward food it can see


def new_rec(t, energy):
    return {"t0": t, "e0": energy, "eats": 0, "gathers": 0, "repros": 0,
            "last_gain": None, "acts": deque(maxlen=10)}


def study(seed, ticks, overrides):
    cfg = {"history_keep": 0}
    cfg.update(overrides)
    world = create_world(seed, cfg)
    c = world["config"]
    w, vision = c["width"], c["vision"]
    recs = {a["id"]: new_rec(world["tick"], a["energy"]) for a in world["agents"]}
    # agents that existed at the start: age0 known, so "full life" = born in run
    initial = set(recs)
    food_start = sum(world["food"])
    exposure = [0] * len(BANDS)
    deaths = [Counter() for _ in BANDS]          # per band: starved / old age
    use = Counter()
    starved, lives = [], []
    pop, births, st, old = [], [], [], []
    gathers_total = 0
    ledger_bad = 0
    for _ in range(ticks):
        pre = {a["id"]: (a["x"], a["y"], a["energy"], a["food"], a["age"])
               for a in world["agents"]}
        food_before = list(world["food"])
        for p in pre.values():
            exposure[band(p[4])] += 1
        events = step(world)
        t = world["tick"]
        b = s = o = 0
        for e in events:
            act, aid = e["action"], e["agent"]
            if act == "born":
                recs[aid] = new_rec(t, c["repro_cost"])
                b += 1
                continue
            r = recs[aid]
            if act == "die":
                px, py, pe, pf, page = pre[aid]
                cause = e["cause"]
                deaths[band(e["age"])][cause] += 1
                ledger = (r["e0"] + c["food_energy"] * r["eats"]
                          - c["repro_cost"] * r["repros"] - (t - r["t0"]))
                lives.append({"cause": cause, "age": e["age"], "eats": r["eats"],
                              "gathers": r["gathers"], "repros": r["repros"],
                              "full": aid not in initial})
                if cause == "starved":
                    s += 1
                    if ledger != 0:
                        ledger_bad += 1
                    stub = {"config": c, "food": food_before, "terrain": world["terrain"]}
                    foods = _food_in_box(stub, px, py, vision)
                    own = food_before[py * w + px] > 0
                    reach = own or (bool(foods) and
                                    _steps_to(stub, px, py, vision, set(foods)) is not None)
                    gain = r["last_gain"] if r["last_gain"] is not None else r["t0"]
                    starved.append({"age": e["age"], "pack": pf, "eats": r["eats"],
                                    "gathers": r["gathers"], "repros": r["repros"],
                                    "since_gain": t - gain,
                                    "in_view": bool(foods) or own, "reach": reach,
                                    "acts": Counter(r["acts"]), "full": aid not in initial})
                else:
                    o += 1
                continue
            kind = move_kind(e["why"]) if act == "move" else act
            use[kind] += 1
            r["acts"].append(kind)
            if act == "eat":
                r["eats"] += 1
            elif act == "gather":
                r["gathers"] += 1
                r["last_gain"] = t
                gathers_total += 1
            elif act == "reproduce":
                r["repros"] += 1
        births.append(b)
        st.append(s)
        old.append(o)
        pop.append(len(world["agents"]))
        if not world["agents"]:
            break
    nominal = c["regrow_per_tick"] * len(pop)
    effective = gathers_total + (sum(world["food"]) - food_start)
    return {"seed": seed, "ticks": len(pop), "pop": pop, "births": births,
            "st": st, "old": old, "exposure": exposure, "deaths": deaths,
            "use": use, "starved": starved, "lives": lives,
            "nominal": nominal, "effective": effective, "ledger_bad": ledger_bad,
            "alive_end": len(world["agents"]), "fp": fingerprint(world), "cfg": c}


# ---------------------------------------------------------------- helpers
def mean(v):
    v = list(v)
    return sum(v) / float(len(v)) if v else 0.0


def pct(a, b):
    return 100.0 * a / b if b else 0.0


def pearson(x, y):
    if len(x) < 3:
        return 0.0
    mx, my = mean(x), mean(y)
    sx = sum((a - mx) ** 2 for a in x) ** 0.5
    sy = sum((b - my) ** 2 for b in y) ** 0.5
    if sx == 0 or sy == 0:
        return 0.0
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / (sx * sy)


def windows(series, size=100):
    return [sum(series[i:i + size]) for i in range(0, len(series) - size + 1, size)]


def percentile(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(p * len(v)))] if v else 0


# ---------------------------------------------------------------- report
def report(runs, overrides):
    P = print
    c = runs[0]["cfg"]
    P("STARVATION STUDY  seeds=%s  ticks=%d  overrides=%s"
      % (",".join(r["seed"] for r in runs), runs[0]["ticks"], overrides or "none"))
    P("settings: regrow=%d food_energy=%d repro_cost=%d repro_cooldown=%d eat_below=%d vision=%d"
      % (c["regrow_per_tick"], c["food_energy"], c["repro_cost"],
         c["repro_cooldown"], c["eat_below"], c["vision"]))
    P("")
    starved = [d for r in runs for d in r["starved"]]
    lives = [d for r in runs for d in r["lives"]]
    n_st = len(starved)
    n_dead = len(lives)
    P("== 1. Deaths overall (all seeds pooled) ==")
    P("deaths %d, starved %d (%.1f%%), old age %d" % (n_dead, n_st, pct(n_st, n_dead), n_dead - n_st))
    P("ledger check (energy start + eaten - child cost - ticks lived == 0 for starved): "
      "%d mismatches out of %d" % (sum(r["ledger_bad"] for r in runs), n_st))
    P("")
    P("== 2. Starvation by age band ==")
    P("%-30s %8s %8s %12s %12s" % ("age band", "starved", "old age", "agent-ticks", "starved/1000"))
    for i, (_, _, name) in enumerate(BANDS):
        s = sum(r["deaths"][i]["starved"] for r in runs)
        o = sum(r["deaths"][i]["old age"] for r in runs)
        ex = sum(r["exposure"][i] for r in runs)
        P("%-30s %8d %8d %12d %12.2f" % (name, s, o, ex, 1000.0 * s / ex if ex else 0))
    at50 = sum(1 for d in starved if 48 <= d["age"] <= 52)
    P("starved at age 48-52 (a newborn that never found food): %d (%.1f%% of starved)"
      % (at50, pct(at50, n_st)))
    P("starved before adult age %d: %d (%.1f%%)"
      % (c["repro_min_age"], sum(1 for d in starved if d["age"] < c["repro_min_age"]),
         pct(sum(1 for d in starved if d["age"] < c["repro_min_age"]), n_st)))
    P("")
    P("== 3. What the starved agent was doing in its last 10 decisions (mean count) ==")
    tot = Counter()
    for d in starved:
        tot.update(d["acts"])
    n10 = sum(tot.values())
    P("  ".join("%s %.1f" % (k, tot[k] / float(n_st) if n_st else 0) for k in KINDS))
    P("(search = no reachable food in sight; to_food = walking to food it sees; "
      "explore = pack full)")
    P("")
    P("== 4. How long without food, and was food in view ==")
    sg = [d["since_gain"] for d in starved]
    P("ticks since the agent last picked up food (or was born): mean %.0f, median %d, "
      "p90 %d, max %d" % (mean(sg), percentile(sg, .5), percentile(sg, .9), max(sg or [0])))
    for lo, hi in ((0, 20), (21, 50), (51, 100), (101, 10 ** 9)):
        k = sum(1 for x in sg if lo <= x <= hi)
        P("  %4s to %-4s ticks: %5d (%.1f%%)" % (lo, hi if hi < 10 ** 9 else "more", k, pct(k, n_st)))
    P("never gathered any food in life: %d (%.1f%%); never ate: %d (%.1f%%)"
      % (sum(1 for d in starved if d["gathers"] == 0), pct(sum(1 for d in starved if d["gathers"] == 0), n_st),
         sum(1 for d in starved if d["eats"] == 0), pct(sum(1 for d in starved if d["eats"] == 0), n_st)))
    P("food in the visible box (approx, start of death tick): %.1f%%; reachable by walking: %.1f%%"
      % (pct(sum(1 for d in starved if d["in_view"]), n_st), pct(sum(1 for d in starved if d["reach"]), n_st)))
    P("carried food in the pack when starving (should be 0; eats at energy<=%d): %d"
      % (c["eat_below"], sum(1 for d in starved if d["pack"] > 0)))
    P("had at least one child before starving: %.1f%%"
      % pct(sum(1 for d in starved if d["repros"] > 0), n_st))
    P("")
    P("== 5. Energy budget (measured, completed lives of agents born inside the run) ==")
    for cause in ("starved", "old age"):
        L = [d for d in lives if d["full"] and d["cause"] == cause]
        if L:
            P("%-8s n=%d  lifespan %.0f  food eaten %.1f (= %.0f energy)  food gathered %.1f  children %.2f"
              % (cause, len(L), mean(d["age"] for d in L), mean(d["eats"] for d in L),
                 c["food_energy"] * mean(d["eats"] for d in L), mean(d["gathers"] for d in L),
                 mean(d["repros"] for d in L)))
    avg_life = (c["max_age_min"] + c["max_age_max"]) / 2.0
    P("plain arithmetic: living costs 1 energy/tick, so a full lifespan (avg %.0f ticks) needs "
      "%.0f energy = %.1f food at %d energy per food."
      % (avg_life, avg_life, avg_life / c["food_energy"], c["food_energy"]))
    P("a child costs the parent %d energy (%.1f food) but the child STARTS with those %d energy, "
      "so a birth moves energy, it does not destroy it."
      % (c["repro_cost"], c["repro_cost"] / float(c["food_energy"]), c["repro_cost"]))
    P("a newborn with %d energy that finds no food starves at age %d."
      % (c["repro_cost"], c["repro_cost"]))
    tk = sum(r["ticks"] for r in runs)
    P("map food supply: %d regrow tries per tick; real new food per tick %.2f (%.0f%% of tries "
      "succeeded; the rest hit a full tile)."
      % (c["regrow_per_tick"], sum(r["effective"] for r in runs) / float(tk),
         pct(sum(r["effective"] for r in runs), sum(r["nominal"] for r in runs))))
    P("so the map can feed at most %.0f energy/tick = about %.0f living agents; mean population was %.1f."
      % (sum(r["effective"] for r in runs) / float(tk) * c["food_energy"],
         sum(r["effective"] for r in runs) / float(tk) * c["food_energy"],
         mean(p for r in runs for p in r["pop"])))
    P("")
    P("== 6. What agents spend their decisions on (all agent-ticks) ==")
    use = Counter()
    for r in runs:
        use.update(r["use"])
    tu = float(sum(use.values()))
    P("  ".join("%s %.1f%%" % (k, 100 * use[k] / tu) for k in KINDS))
    P("")
    P("== 7. Steady or waves? (per 100-tick window) ==")
    P("%-5s %9s %9s %10s %10s %12s" % ("seed", "pop min", "pop max", "starved CV", "births CV",
                                        "corr(births, starved next window)"))
    for r in runs:
        ws, wb = windows(r["st"]), windows(r["births"])
        ws5, wb5 = ws[5:], wb[5:]    # skip the first 500 ticks (start-up)
        cv = lambda v: (mean((x - mean(v)) ** 2 for x in v) ** 0.5 / mean(v)) if mean(v) else 0
        lag1 = pearson(wb5[:-1], ws5[1:])
        pp = r["pop"][500:] or r["pop"]
        P("%-5s %9d %9d %10.2f %10.2f %12.2f" % (r["seed"], min(pp), max(pp), cv(ws5), cv(wb5), lag1))
    r0 = runs[0]
    P("seed %s per 100 ticks  [pop at end / births / starved / old age]:" % r0["seed"])
    ws, wb, wo = windows(r0["st"]), windows(r0["births"]), windows(r0["old"])
    P(" ".join("%d:%d/%d/%d/%d" % ((i + 1) * 100, r0["pop"][(i + 1) * 100 - 1], wb[i], ws[i], wo[i])
               for i in range(len(ws))))


def sweep(seeds, ticks, base):
    grid = [("default", {})]
    for name, vals in (("repro_cost", (30, 70)), ("food_energy", (15, 30)),
                       ("repro_cooldown", (100, 400))):
        for v in vals:
            grid.append(("%s=%d" % (name, v), {name: v}))
    print("SWEEP seeds=%s ticks=%d (averages over seeds; overrides on top of %s)"
          % (",".join(seeds), ticks, base or "defaults"))
    print("%-18s %7s %7s %8s %8s %10s %8s %9s %9s %9s" %
          ("setting", "end pop", "mean", "low", "starved%", "age@death", "<80 of", "never", "eaten per", "extinct"))
    print("%-18s %7s %7s %8s %8s %10s %8s %9s %9s %9s" %
          ("", "", "pop", "pop", "of deaths", "(all)", "deaths%", "ate %", "life", ""))
    for label, ov in grid:
        o = dict(base)
        o.update(ov)
        runs = [study(s, ticks, o) for s in seeds]
        lives = [d for r in runs for d in r["lives"]]
        st = [d for r in runs for d in r["starved"]]
        pops = [p for r in runs for p in r["pop"][500:]]
        young = sum(1 for d in lives if d["age"] < runs[0]["cfg"]["repro_min_age"])
        print("%-18s %7.1f %7.1f %8.1f %8.1f %10.0f %8.1f %9.1f %9.1f %6d/%d" % (
            label, mean(r["alive_end"] for r in runs), mean(pops), mean(min(r["pop"][500:] or [0]) for r in runs),
            pct(len(st), len(lives)), mean(d["age"] for d in lives), pct(young, len(lives)),
            pct(sum(1 for d in st if d["eats"] == 0), len(st)), mean(d["eats"] for d in lives),
            sum(1 for r in runs if r["ticks"] < ticks), len(runs)))
        sys.stdout.flush()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--sweep", action="store_true")
    ap.add_argument("--ticks", type=int, default=TICKS)
    ap.add_argument("--seeds", default=",".join(SEEDS))
    ap.add_argument("--set", action="append", default=[], metavar="NAME=VALUE")
    a = ap.parse_args()
    ov = {}
    for item in a.set:
        k, v = item.split("=")
        ov[k] = int(v) if v.lstrip("-").isdigit() else float(v)
    seeds = a.seeds.split(",")
    if a.sweep:
        sweep(seeds, a.ticks, ov)
    else:
        runs = [study(s, a.ticks, ov) for s in seeds]
        for r in runs:
            if r["seed"] == "42" and r["ticks"] == 500:
                print("seed 42 fingerprint after 500 ticks: %s" % r["fp"])
        report(runs, ov)


if __name__ == "__main__":
    main()
