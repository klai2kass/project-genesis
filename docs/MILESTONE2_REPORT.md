# Milestone 2 report: what rest and personality actually do

Written 2026-11-17 from simulation runs made the same day. Every number below
comes from a saved result file; the command that makes it is listed with it.
Nothing is estimated from memory. Labels: **FACT** = measured, **GUESS** =
plausible but not tested.

## Short answer

- **Rest works as designed.** About 9% of all decisions are now "rest". Lazy
  agents rest about twice as often as hard-working ones. The world is as
  harsh as before (all Milestone 2 bands hold).
- **Curiosity clearly changes how an agent walks.** High-curiosity agents
  zigzag more and cover about 5% less ground, in every seed.
- **When everyone has the same curiosity, nothing else changes**: the world
  has the same population, births and starvation at curiosity 10, 50 or 90.
- **When curious and incurious families share a world, the curious ones
  win**: they end up with more living descendants in 34 of 40 seeds. Each
  curious agent gathers only about 1.5% more food, but over 16 generations of
  competing for the same food that small edge adds up. This is the first
  real selection pressure in Genesis, and nobody wrote it as a rule.
- **The name is backwards.** In the code a "curious" agent turns more often,
  so it explores *less*. It wins because it stays near the food patch it is
  on, not because it explores.
- **In normal runs no trait is selected yet.** Founders only differ by
  40-60 (turn chance 13-17%), too little for the edge to beat chance in
  3,000 ticks: trait averages move no further than in a control world.
- Why the per-agent effect is small: wandering stretches are short (about 5
  moves), because food comes back into sight almost every time (94%).

## What was measured, and how

| Script (read-only) | Worlds | Result file |
| --- | --- | --- |
| `experiments/stage_compare.py` | 5 seeds x 3,000 ticks: Milestone 1 rules, Milestone 2 defaults, everyone industriousness 10 or 90, everyone curiosity 10 or 90 | `experiments/results/stage_compare.txt` (run in the implementation session) |
| `experiments/curiosity_probe.py` | 10 seeds (42, 1-9) x 3,000 ticks. **Forced**: every agent and child curiosity 10, 50 or 90. **Mixed**: one world per seed, a third of the founders each at 10 / 50 / 90, children copy the parent | `experiments/results/curiosity_probe.txt` and `.json` |
| `curiosity_probe.py --mixed-extra` | mixed worlds only, 30 more seeds (10-39) | `experiments/results/curiosity_mixed_extra.txt` and `.json` |
| `experiments/trait_drift.py` | 10 seeds x 3,000 ticks, defaults against a control with `turn_span=0`, `tire_span=0` (traits exist but do nothing) | `experiments/results/trait_drift.txt` and `.json` |

All runs use the code defaults (`regrow_per_tick` 6, history off for speed,
which does not change behaviour). In the probe, `trait_mutation=0` so children
keep their parent's curiosity. "+/-" is the standard deviation across seeds:
how much the result moves from one world to another by luck.

## 1. Rest and industriousness (FACT, `stage_compare.txt`, 5 seeds)

| run | population | births | starved % | age at death | rest % of decisions | tiles per 100 ticks |
| --- | --- | --- | --- | --- | --- | --- |
| Milestone 1 rules | 89.1 | 918 | 67.7 | 295 | 0.0 | 66.6 |
| Milestone 2 defaults | 93.0 | 946 | 66.5 | 300 | 8.7 | 63.5 |
| everyone industriousness 10 | 95.0 | 965 | 67.5 | 300 | 11.1 | 62.1 |
| everyone industriousness 90 | 92.1 | 938 | 66.3 | 300 | 5.9 | 64.7 |

- Resting is 8.7% of decisions, not the 25% a never-hungry agent would show,
  because agents are hungry (energy 80 or less) most of the time and rest is
  only allowed when they are not.
- Lazy agents (10) rest almost twice as often as hard-working ones (90).
- Milestone 2 carries about 4 more agents than Milestone 1 on the same food
  (GUESS: because resting halves energy use). The starved share hardly moved.
- That script reports no seed-to-seed spread, so the 3-agent gap between
  lazy and hard-working worlds is not proven to be more than luck.

## 2. Curiosity (FACT, `curiosity_probe.txt`, 10 seeds)

Turn chance while wandering: curiosity 10 = 7%, 50 = 15%, 90 = 23%.

### Forced worlds (everyone the same)

| | low (10) | neutral (50) | high (90) | high minus low, per seed |
| --- | --- | --- | --- | --- |
| direction changes while wandering | 16.4% | 22.5% | 28.6% | +12.2, all 10 seeds |
| straightness of a wander stretch (1 = straight line) | 0.53 | 0.47 | 0.43 | -0.10, all 10 seeds |
| distinct tiles per 100 ticks of life | 65.6 | 64.2 | 62.3 | -3.3 (-5%), all 10 seeds |
| distance covered per 100 ticks | 16.6 | 15.7 | 15.0 | -1.6 (-10%), all 10 seeds |
| share of decisions spent wandering | 45.9% | 46.5% | 46.8% | +0.9 |
| moves until food is in sight again | 4.76 | 4.84 | 4.86 | +0.1 |
| searches that end with food found | 94.0% | 94.0% | 94.0% | 0 |
| age at first food (newborns) | 15.5 | 15.4 | 15.6 | +0.1, 7 of 10 |
| gathers per 100 ticks | 5.26 | 5.26 | 5.26 | 0 |
| rest % | 8.7 | 8.5 | 8.5 | -0.2 |
| starved % of deaths | 66.9 +/- 1.0 | 66.1 +/- 0.8 | 65.9 +/- 1.0 | -1.0, 4 of 10 |
| age at death | 298 | 302 | 303 | +4, 10 of 10 |
| population after tick 500 | 93.5 +/- 0.6 | 93.2 +/- 0.6 | 93.5 +/- 0.6 | 0 |
| births | 956 | 942 | 942 | -14 |

Reading it: every **movement** measure changes in the same direction in
every one of the 10 seeds, so that is a real effect of curiosity, not luck.
Every **outcome** measure (finding food, gathering, starving, population)
stays within the luck range. The one small exception is age at death: about
4 ticks longer for curious agents in all 10 seeds (1%); GUESS: zigzagging
agents stay near the food patch they just emptied and pick up regrowth.

### Mixed worlds (all three groups in the same world)

| | low (10) | neutral (50) | high (90) |
| --- | --- | --- | --- |
| tiles per 100 ticks | 65.4 | 63.4 | 62.6 |
| straightness | 0.54 | 0.47 | 0.43 |
| gathers per 100 ticks | 5.20 | 5.25 | 5.28 |
| starved % | 67.8 +/- 2.6 | 65.5 +/- 1.6 | 65.3 +/- 2.0 |
| alive at tick 3,000 | 20.6 +/- 16.0 | 25.1 +/- 14.4 | 47.6 +/- 17.5 |
| born during the run | 230 +/- 80 | 301 +/- 79 | 414 +/- 110 |

The movement effect is the same as in forced worlds. In these 10 seeds the
high-curiosity families ended larger in 8 of 10 seeds, but the spread is
huge (in one world, which family takes over is partly luck), so 30 more
seeds were run (FACT, `curiosity_mixed_extra.txt`, seeds 10-39):

| | low (10) | neutral (50) | high (90) | high minus low, per seed |
| --- | --- | --- | --- | --- |
| alive at tick 3,000 | 17.3 +/- 14.1 | 34.1 +/- 15.8 | 42.8 +/- 14.1 | +25.5, **26 of 30 seeds** |
| born during the run | 249 +/- 79 | 330 +/- 86 | 364 +/- 79 | +115, 23 of 30 |
| gathers per 100 ticks | 5.20 | 5.26 | 5.28 | +0.08, **28 of 30** |
| starved % of deaths | 67.6 | 66.1 | 66.0 | |
| tiles per 100 ticks | 65.5 | 63.8 | 62.3 | |
| group extinct at the end | 1 seed | 0 | 0 | |

Together with the first 10 seeds: high beat low in 34 of 40 worlds. If
curiosity did nothing, that would happen by luck far less than once in
10,000 tries (coin-flip count). **So in competition, curiosity is a real
advantage**, and the order low < neutral < high holds for survivors,
births and gathering.

How can that be, when forced worlds show no difference? Food is shared. In
a forced world every agent has the same small edge, so nobody gains
relative to anyone else, and the food supply still feeds about 93 agents.
In a mixed world the zigzaggers get about 1.5% more of the same food, have
children slightly more often, and their families slowly crowd out the
straight walkers. GUESS (not measured): zigzagging keeps an agent near the
patch it just found, where food regrows, while a straight walker carries on
into emptier ground.

### Why the effect per agent is so small (from the code)

1. Curiosity is used in exactly one place: `_wander` in `genesis/agents.py`,
   the chance to turn on a wandering tick.
2. Wandering stops the moment any reachable food is within 4 tiles; then
   `_walk_to_food` takes over, and that is identical for every agent.
3. Food is in sight again after about 5 wandering moves in 94% of cases. In 5
   moves the difference between turning 7% and 23% of the time is about 0.8
   turns.
4. A turn picks a random open direction, which can be the old one or even
   straight back, so a turn does not mean "look somewhere new".
5. Starvation is set by how many agents the food can feed, not by how fast
   one agent finds food (`docs/STARVATION.md`: births overflow the food
   supply). A better searcher only takes food that someone else would have
   eaten. That is exactly why the effect shows up as competition between
   families and not as a bigger or healthier world.

### Recommendation for curiosity

Curiosity does something real, so **keep it and do not tune it**. A bigger
`turn_span` would only make the result look bigger. Two honest changes,
neither urgent:

1. **Describe it honestly** in the page and docs as "how often it turns
   while searching (high = searches its patch thoroughly, low = walks off
   in straight lines)". No code change; the saved key stays `curiosity`.
2. **Later, once agents have a home** (the proposed next step, `STATUS.md`),
   consider letting curiosity also set how far from home an agent roams,
   which would match the word. Only with the same measurements before and
   after, because it would change which families win.

Flipping its direction (curious = straighter) is rejected: the data says
that would simply make "curious" the losing trait.

## 3. Was any trait selected? (FACT, `trait_drift.txt`, 10 seeds)

Change of the average trait from the founders to the living at tick 3,000:

| | real run | control (traits do nothing) |
| --- | --- | --- |
| curiosity | +1.6 +/- 4.1 | -0.8 +/- 3.2 |
| industriousness | -1.2 +/- 4.6 | +0.5 +/- 3.3 |

The real changes are smaller than the seed-to-seed spread and the same size
as in the control. About 16 generations fit into 3,000 ticks. **Honest
result: no selection visible in normal runs.** Curiosity moves the right
way (+1.6, the direction the mixed worlds predict) but not by more than
chance. The reason fits section 2: normal founders differ only by 40-60, so
the difference in turn chance is about a quarter of the 10-against-90 one (13-17% against 7-23%), and drift (traits
spread to about 11.5 within a world) drowns it. Longer runs or more seeds
might show it; not tested.

## 4. What emerged, what did not, what surprised

**Emerged (not written as a rule anywhere):**
- **Competition between families decided by a walking style.** Families
  that search their patch thoroughly (high curiosity) out-breed families
  that walk off in straight lines, in 34 of 40 mixed worlds, while the
  world as a whole stays the same size.
- A rest rhythm that depends on how hungry the world is: most agents almost
  never get to rest because they are rarely full.
- Lazy worlds carry slightly more agents, because resting is cheap living
  (not proven against luck).
- In mixed worlds, families rise and fall by chance: three founder groups
  of equal size end very unequal (seed 1: 6 / 5 / 81 of 92 alive; seed 2:
  43 / 1 / 54; seed 5: 36 / 32 / 31).

**Did not emerge:**
- Any change to the world as a whole (population, starvation) from either
  trait when everyone shares the same value.
- Selection beyond chance in normal runs (founders too similar, too few
  generations).
- Industriousness was not tested in mixed worlds; whether it is selected in
  competition is unknown.
- Anything social. Agents ignore each other except by eating the same food.

**Surprised me:**
- "Curious" agents explore less, and that is what makes them win. The design
  said they would zigzag (`MILESTONE2_V2.md` section 3) but the name hides it.
- A 1.5% difference in food gathered was enough to decide which families
  survive in most worlds.
- Searching is short and almost always successful (94%), even though two
  thirds of deaths are starvation. Agents rarely starve because they cannot
  find food; they starve because there is not enough of it to go round.

## 5. Limitations

- One map size (60 x 40), one food setting, 3,000 ticks; 5 to 40 seeds.
- Mixed worlds use extreme values (10, 50, 90) and no mutation; real worlds
  have founders at 40-60 and mutation 5.
- The reason the zigzaggers gather more (staying near regrowing food) is a
  guess; it was not measured.
- `stage_compare.py` has no spread per variant; its small population
  differences are unproven.
- Measures 3, 4 and 8 of `MILESTONE2_V2.md` section 7 (situation split,
  explained split, clustering) were not computed.
- "Wandering" is recognised from the "why" text of a decision (the same rule
  as `starvation_study.py`); if that text changes, the scripts must too.
- Straightness counts only wander stretches of 10 moves or more, which are
  a minority (the mean stretch is 5 moves).

## Update after homes (Milestone 3 step 1)

Homes were built after this report. With homes on, the curiosity advantage
in mixed worlds mostly disappears (high beat low in 25 of 40 seeds instead of
34 of 40). Details: `docs/MILESTONE3.md`, "Results". Everything above
describes the Milestone 2 world (`home_radius = 0`), which the code still
reproduces exactly; `python3 experiments/curiosity_probe.py --homes-off`
regenerates these files.

## 6. Evidence for the next step

See `STATUS.md`, "Next step". Short version, from
`experiments/encounter_probe.py` (5 seeds x 3,000 ticks): with today's rules
an agent meets about 38 different agents in its life, but only 7% of pairs
meet again after 100 ticks apart, and only 6% of meetings are between family.
A prototype in which agents drift back toward their birthplace roughly
doubles family meetings and repeated meetings, with no change in survival.
