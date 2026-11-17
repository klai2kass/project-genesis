"""Reference results from the Milestone 1 decision rules (the old `decide()`).

Why this exists: Milestone 2 changes decisions. Instead of keeping two
decision systems alive in the program, we freeze what the OLD rules produce
here and compare later code against it.

  python3 experiments/baseline/make_baseline.py --check    # recompute and compare, print differences

baseline.json is FROZEN (made on 2026-11-17 from the unchanged Milestone 1
code). Since Milestone 2 the check runs the new code with MILESTONE1_RULES
(nobody rests, all traits 50), which must reproduce Milestone 1 exactly. The
full-world `fingerprint` is shown but not compared: Milestone 2 agents carry
new fields, so it changes by design; the behaviour and event digests are the
real guard. Writing a new baseline.json needs --rewrite-frozen (do not).

baseline.json holds
  short: per seed, 500 ticks at default settings: behaviour digest, event
         digest, full-world fingerprint, counters. Must match EXACTLY for
         every stage that promises "behaviour unchanged".
  long:  per seed, 3000 ticks (history off): population, births, starved
         share, average age at death. For stages that change behaviour on
         purpose: compare against these with the bands in docs/MILESTONE2_V2.md.
  save:  the digest after loading tests/fixtures/save_v2_seed42_t300.json and
         running 200 more ticks.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

from genesis import create_world, fingerprint, load_world, step  # noqa: E402
from genesis.digest import EventDigest, behaviour_digest  # noqa: E402
from genesis.save import MILESTONE1_RULES  # noqa: E402

PATH = os.path.join(ROOT, "experiments", "baseline", "baseline.json")
FIXTURE = os.path.join(ROOT, "tests", "fixtures", "save_v2_seed42_t300.json")
SHORT_SEEDS, SHORT_TICKS = ["42", "1", "2"], 500
LONG_SEEDS, LONG_TICKS = ["42", "1", "2", "3", "4"], 3000
FIXTURE_MORE_TICKS = 200


def short_run(seed, rules=MILESTONE1_RULES):
    world = create_world(seed, dict(rules))
    ed = EventDigest()
    for _ in range(SHORT_TICKS):
        ed.add(step(world))
    s = world["stats"]
    return {"alive": len(world["agents"]), "births": s["births"],
            "starved": s["deaths_starved"], "old_age": s["deaths_old_age"],
            "behaviour_digest": behaviour_digest(world),
            "event_digest": ed.hexdigest(), "fingerprint": fingerprint(world)}


def long_run(seed, rules=MILESTONE1_RULES):
    cfg = dict(rules)
    cfg["history_keep"] = 0
    world = create_world(seed, cfg)
    pops, ages = [], []
    for _ in range(LONG_TICKS):
        for e in step(world):
            if e["action"] == "die":
                ages.append(e["age"])
        pops.append(len(world["agents"]))
    s = world["stats"]
    deaths = s["deaths_starved"] + s["deaths_old_age"]
    return {"end_pop": pops[-1], "mean_pop_after_500": round(sum(pops[500:]) / len(pops[500:]), 1),
            "births": s["births"], "starved": s["deaths_starved"],
            "starved_share_pct": round(100.0 * s["deaths_starved"] / deaths, 1),
            "mean_age_at_death": round(sum(ages) / len(ages), 1)}


def fixture_run():
    world = load_world(FIXTURE)
    for _ in range(FIXTURE_MORE_TICKS):
        step(world)
    return {"tick": world["tick"], "behaviour_digest": behaviour_digest(world)}


def compute(with_long=True):
    out = {"note": "Milestone 1 decision rules, regrow_per_tick=6. Do not regenerate on changed code.",
           "short": {s: short_run(s) for s in SHORT_SEEDS}, "save": fixture_run()}
    if with_long:
        out["long"] = {s: long_run(s) for s in LONG_SEEDS}
    return out


def main():
    check = "--check" in sys.argv
    if not check and "--rewrite-frozen" not in sys.argv:
        print("baseline.json is frozen. Use --check (or --rewrite-frozen to overwrite it).")
        return
    new = compute()
    if not check:
        with open(PATH, "w") as f:
            json.dump(new, f, indent=1, sort_keys=True)
        print("wrote", PATH)
        return
    old = json.load(open(PATH))
    for part in (old, new):
        for run in part["short"].values():
            run.pop("fingerprint", None)   # changes by design since Milestone 2
    bad = 0
    for part in ("short", "long", "save"):
        if old.get(part) != new.get(part):
            bad += 1
            print("DIFFERENT:", part)
            print("  stored:", json.dumps(old.get(part), sort_keys=True)[:600])
            print("  now   :", json.dumps(new.get(part), sort_keys=True)[:600])
    print("baseline check:", "ALL SAME" if not bad else "%d part(s) differ" % bad)


if __name__ == "__main__":
    main()
