"""Regrowth experiment: run_headless.py --summary for several regrow_per_tick
values and seeds, then print one comparison table. Does not change any file.
Run:  python3 experiments/regrow_sweep.py   (about 1 minute)
"""
import subprocess, re, sys, json
from concurrent.futures import ThreadPoolExecutor
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALUES = [2, 3, 4, 6, 8, 12]
SEEDS = ["42", "1", "2", "3", "4"]
TICKS = 3000
def run(v, seed):
    out = subprocess.run([sys.executable, ROOT + "/run_headless.py", "--seed", seed, "--ticks", str(TICKS),
        "--every", "0", "--summary", "--set", "regrow_per_tick=%d" % v, "--set", "history_keep=0"],
        capture_output=True, text=True, cwd=ROOT).stdout
    g = lambda pat: re.search(pat, out)
    pop = g(r"population\s+start (\d+), end (\d+) \(lowest (\d+), highest (\d+)\)")
    starved = g(r"starved share\s+([\d.]+)% of deaths")
    age = g(r"average age at death ([\d.]+)")
    food = g(r"average (\d+), lowest (\d+), highest (\d+), at the end (\d+)")
    births = g(r"births\s+(\d+)")
    samples = re.findall(r"t(\d+):(\d+)", out)
    ended = g(r"tick=(\d+) alive=(\d+)")
    return dict(v=v, seed=seed, end=int(pop[2]), low=int(pop[3]), high=int(pop[4]), starved=float(starved[1]),
        age=float(age[1]), food=int(food[1]), births=int(births[1]), samples=[(int(a), int(b)) for a, b in samples],
        tick=int(ended[1]), extinct=int(ended[1]) < TICKS)
jobs = [(v, s) for v in VALUES for s in SEEDS]
with ThreadPoolExecutor(4) as ex:
    res = list(ex.map(lambda j: run(*j), jobs))
print("%6s %7s %9s %9s %9s %8s %7s %8s  %s" % ("regrow", "extinct", "end pop", "low pop", "high pop", "starved%", "age", "food avg", "pop at t300,t1500,t3000 (mean)"))
for v in VALUES:
    r = [x for x in res if x["v"] == v]
    m = lambda k: sum(x[k] for x in r) / float(len(r))
    def at(t):
        vals = [dict(x["samples"]).get(t) for x in r]
        vals = [a for a in vals if a is not None]
        return "%.0f" % (sum(vals) / len(vals)) if vals else "-"
    print("%6d %4d/%d %9.1f %9.1f %9.1f %8.1f %7.1f %8.0f  %s / %s / %s" % (v, sum(x["extinct"] for x in r), len(r), m("end"), m("low"), m("high"), m("starved"), m("age"), m("food"), at(300), at(1500), at(3000)))
