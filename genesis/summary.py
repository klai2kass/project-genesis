"""A readable report about one run.

Only things the simulation really records are reported. Anything it does not
record is listed at the end as "not tracked" instead of being guessed.

How to use (see run_headless.py --summary):
    rec = RunRecorder(world)         # before the first step
    ... each tick:  rec.update(world, events)
    print(rec.report(world))
"""


class RunRecorder:
    def __init__(self, world):
        self.seed = world["seed"]
        self.start_tick = world["tick"]
        self.start_pop = len(world["agents"])
        self.births = 0
        self.deaths = {"starved": 0, "old age": 0}
        self.death_ages = {"starved": [], "old age": []}
        self.pop = [self.start_pop]          # population after each tick
        self.food_total = []                 # total food lying on the map, per tick
        cfg = world["config"]
        self.food_capacity = sum(cfg["food_cap"][t] for t in world["terrain"])
        self.land_tiles = sum(1 for t in world["terrain"] if t != 0)

    def update(self, world, events):
        for e in events:
            if e["action"] == "born":
                self.births += 1
            elif e["action"] == "die":
                self.deaths[e["cause"]] += 1
                self.death_ages[e["cause"]].append(e["age"])
        self.pop.append(len(world["agents"]))
        self.food_total.append(sum(world["food"]))

    # ------------------------------------------------------------------
    def report(self, world):
        ticks = len(self.pop) - 1
        deaths = sum(self.deaths.values())
        all_ages = self.death_ages["starved"] + self.death_ages["old age"]
        L = []
        L.append("RUN SUMMARY")
        L.append("-----------")
        L.append("seed                 %s" % self.seed)
        L.append("ticks run            %d (tick %d to %d)"
                 % (ticks, self.start_tick, world["tick"]))
        L.append("population           start %d, end %d (lowest %d, highest %d)"
                 % (self.start_pop, self.pop[-1], min(self.pop), max(self.pop)))
        L.append("births               %d" % self.births)
        L.append("deaths               %d" % deaths)
        for cause in ("starved", "old age"):
            share = (100.0 * self.deaths[cause] / deaths) if deaths else 0.0
            L.append("  %-18s %d (%.1f%% of deaths)"
                     % (cause, self.deaths[cause], share))
        L.append("starved share        %s of deaths, %s of births"
                 % (_pct(self.deaths["starved"], deaths),
                    _pct(self.deaths["starved"], self.births)))
        L.append("average age at death %s ticks (starved: %s, old age: %s)"
                 % (_avg(all_ages), _avg(self.death_ages["starved"]),
                    _avg(self.death_ages["old age"])))
        adult = world["config"]["repro_min_age"]
        young = sum(1 for a in all_ages if a < adult)
        L.append("died before adult   %s of deaths (before age %d)"
                 % (_pct(young, deaths), adult))

        L.append("")
        L.append("Population over time (alive after this tick):")
        L.append("  " + "  ".join(self._samples()))

        L.append("")
        L.append("Food on the map (total units lying on tiles, every tick):")
        if self.food_total:
            f = self.food_total
            L.append("  average %.0f, lowest %d, highest %d, at the end %d"
                     % (sum(f) / float(len(f)), min(f), max(f), f[-1]))
            L.append("  map could hold at most %d; at the end it holds %s"
                     % (self.food_capacity, _pct(f[-1], self.food_capacity)))
            with_food = sum(1 for v in world["food"] if v > 0)
            L.append("  tiles with any food at the end: %d of %d land tiles"
                     % (with_food, self.land_tiles))
        else:
            L.append("  no ticks were run")

        L.append("")
        L.append("Not tracked (the simulation does not record these):")
        L.append("  food eaten per agent, distance walked, energy over time,")
        L.append("  births per generation, family trees, agent-to-agent contact.")
        return "\n".join(L)

    def _samples(self):
        ticks = len(self.pop) - 1
        if ticks <= 0:
            return ["(no ticks run)"]
        marks = sorted(set(max(1, ticks * i // 10) for i in range(1, 11)))
        return ["t%d:%d" % (self.start_tick + m, self.pop[m]) for m in marks]


def _avg(values):
    return "%.1f" % (sum(values) / float(len(values))) if values else "n/a"


def _pct(part, whole):
    return "%.1f%%" % (100.0 * part / whole) if whole else "n/a"
