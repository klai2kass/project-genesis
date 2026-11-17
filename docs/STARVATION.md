# Why do about two thirds of deaths come from starvation?

Written 2026-11-17. Measured with `experiments/starvation_study.py` (read-only:
it runs the normal `step()` and only watches; code defaults untouched).
Raw output: `experiments/results/starvation_default.txt` and
`starvation_sweep.txt`. Setup: seeds 42, 1, 2, 3, 4 x 3,000 ticks, default
settings (regrow 6) unless a row says otherwise. Check it yourself:
`python3 experiments/starvation_study.py` (about 25 s) and `--sweep` (about 4 min).

Labels: **FACT** = measured here. **PREDICTION** = what I expect, not tested.
**GUESS** = plausible, no evidence yet.

## Short answer

**FACT:** the map's food supply decides HOW MANY agents live (about 91 at
regrow 6; the map can feed at most about 98). Nothing in the rules limits
births when the map is full: an agent with energy 90 or more, age 80 or more
and no cooldown always has a child. So births keep going until the extra
children starve. Starvation is the "overflow valve" of the population. It is
not an accident or a bug in food search.

**Evidence for that (FACT):** slowing births (`repro_cooldown=400`) drops the
starved share from 67.7% to 45.5% while the population barely changes
(mean 84 against 89). Speeding births (`repro_cooldown=100`) raises it to
78.4%. More food (earlier regrow sweep, and `food_energy=30` here) gives more
agents and the same starved share (about 72%).

## The numbers

### 1. Who starves, by age (FACT, 2,959 starvation deaths, 4,369 deaths in total)

| Age band | starved | old age | starved per 1000 agent-ticks |
| --- | --- | --- | --- |
| 0-49 | 0 | 0 | 0 (a newborn has 50 energy, so cannot die yet) |
| 50-79 | 775 | 0 | **6.4** |
| 80-199 | 1215 | 0 | 3.3 |
| 200-399 | 730 | 0 | 1.8 |
| 400+ | 239 | 1410 | 1.1 |

- A newborn that never finds food dies at age 50 on the dot: 430 deaths
  (14.5% of starvation) are at age 48 to 52 and never ate once.
- 26% of starvation deaths happen before the adult age of 80.
- The risk falls with age: the older an agent is, the better it survives.

### 2. What it was doing, and was food nearby? (FACT)

- Last 10 decisions before starving: 6.7 "search" (no reachable food in
  sight) and 3.3 "walk to food". It was almost never eating or gathering.
- Over all agents, 45.8% of all decisions are "search", 37.0% "walk to food",
  5.4% eat, 5.5% gather. Agents spend most of their lives looking for food.
- Time since the last food was picked up: median 45 ticks, 90% under 66,
  longest 143. 93% were between 21 and 100 ticks.
- Food in the visible 9 x 9 box at the start of the death tick (approx):
  40.5% yes, 59.5% no. So about 6 in 10 starved agents had no food in sight.
- 33.8% had a child before starving; 14.5% never ate at all.
- **Found a small flaw (FACT):** 182 starved agents (6.2%) died ONE tick after
  picking up food. They gathered it with 1 energy left, and eating is a
  separate action on the next tick. (Checked on seeds 42 and 1: all 75 such
  cases had gathered exactly one tick before dying.)

### 3. Energy arithmetic (FACT unless noted)

- Living costs 1 energy per tick. A full life (avg 550 ticks) costs 550
  energy = 27.5 food at 20 energy per food.
- A child costs the parent 50 energy (2.5 food) but the child STARTS with
  those 50. So reproduction moves energy, it does not destroy it. It is
  also not free: the child is born with a 50-tick clock.
- Agents that died of old age ate 33.7 food (674 energy) and had 2.2
  children. Agents that starved ate 7.1 food (142 energy) in 172 ticks and
  had 0.4 children.
- The map: 6 regrow tries per tick, 82% succeed (the rest hit a full tile),
  so real new food is 4.9 per tick = 98 energy per tick = enough for about
  98 agents. Mean population was 91.1, that is 93% of the ceiling.
- Rough split of the food (FACT, from the numbers above): about two thirds of
  the energy eaten ends up in lives that reach old age, about one third is
  spent on lives that end in starvation.
- The ledger check (energy at start + eaten - child costs - ticks lived = 0
  for every starved agent) holds for all 2,959. So the tracking is right.

### 4. Steady or waves? (FACT)

- One big boom and bust at the start: seed 42 grows from 50 to 131 by tick
  300, then starvation peaks (52 deaths in ticks 300-400) and the population
  falls to 79 by tick 500.
- After tick 500 it is mostly steady: population stays between 72 and 106 on
  all five seeds (about plus or minus 15%). Starvation per 100 ticks varies
  moderately (spread/average 0.17 to 0.32). Births in one window predict
  starvation in the next only weakly to moderately (correlation 0.02 to 0.65
  by seed). So: one real wave, then small ripples, not repeating boom-bust.

### 5. Small sweep, one setting at a time (FACT; 5 seeds, no error bars)

| setting | mean pop | starved % of deaths | avg age at death | died before 80 | never ate (of starved) | food eaten per life |
| --- | --- | --- | --- | --- | --- | --- |
| default (cost 50, energy 20, cooldown 200) | 89 | 67.7 | 295 | 17.7% | 14.5% | 15.5 |
| repro_cost=30 | 85 | 62.4 | 269 | 38.4% | 33.8% | 14.5 |
| repro_cost=70 | 93 | 80.1 | 278 | 4.1% | 5.2% | 14.2 |
| food_energy=15 | 68 | 63.7 | 324 | 10.0% | 6.8% | 22.2 |
| food_energy=30 | 119 | 71.9 | 269 | 18.5% | 25.7% | 10.7 |
| repro_cooldown=100 | 93 | 78.4 | 253 | 21.6% | 14.2% | 12.9 |
| repro_cooldown=400 | 84 | **45.5** | 372 | 11.9% | 14.8% | 20.3 |

No run died out. Old-age share is just 100% minus the starved share.

## What the data supports

1. **Supported:** the population sits at the food ceiling, and births are not
   limited by crowding, so the overflow dies of hunger. The cooldown test is
   the strongest evidence: births down, starvation share down, headcount
   about the same.
2. **Supported:** a lot of the early death is newborns. They start with 50
   ticks of energy and spend most of their time with nothing in sight. With
   a bigger starting reserve (`repro_cost=70`) early deaths fall from 17.7%
   to 4.1%, but the starved share rises (80%): those children survive the
   first 50 ticks and then starve later. So protecting children moves
   starvation to a later age, it does not remove it.
3. **Supported:** the real bottleneck for an individual is FINDING food, not
   the eating rule: 46% of all decisions are searching, and 6 in 10 starved
   agents had nothing in sight.

## What is only a guess

- **GUESS:** newborns start next to a parent who just took the food there,
  so they begin in a locally empty spot. (Not measured. Test: count food in
  view at birth against a random land tile.)
- **GUESS:** agents with similar targets crowd the same food and leave
  others empty. (Not measured; targets are tracked per agent but not
  conflicts.)
- **GUESS:** why `repro_cost=70` gives a higher starved share. (Fewer old-age
  deaths cannot explain it alone; not investigated.)
- Starvation share by the exact moment of death is approximate: the food
  snapshot is from the start of the tick.

## What this means for you

- **PREDICTION:** any rule that lets agents have children without regard to
  crowding will keep starvation as the main killer. Getting starvation below
  half needs something that reduces births when food is short (for example a
  longer cooldown, or "not hungry enough to reproduce" rules), not more food.
- This matters for Milestone 2: a "company" or "rest" need that changes how
  many children are born will change the starved share a lot. That is why
  `docs/MILESTONE2_V2.md` starts from this baseline.
- Small fix candidate (NOT done, it would change behaviour): let an agent
  that stands on food with 1 to 2 energy eat directly, or eat what it just
  gathered. It would save about 6% of starvation deaths. Your decision.
- Not tracked: how many food units were taken by someone else before an agent
  arrived, and food in view at birth.
