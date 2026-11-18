# Milestone 2 report: what rest and personality actually do

Written 2026-11-17 from simulation runs made the same day. Every number below
comes from a saved result file; the command that makes it is listed with it.
Nothing is estimated from memory. Labels: **FACT** = measured, **GUESS** =
plausible but not tested.

> **Update 2026-11-18: curiosity was fixed.** Sections 1 to 6 describe the
> rule as it was (curious agents turned MORE). Since the fix, curious agents
> turn LESS and walk straighter (setting `curiosity_straight`, on by
> default; old saves keep the old rule). Section 7 has the before/after
> study. Where a sentence below talks about "curious" agents, it means the
> OLD rule.

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
- **The name was backwards** (fixed 2026-11-18, section 7). In the code a
  "curious" agent turned more often, so it explored *less*. It won because
  it stayed near the food patch it was on, not because it explored.
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

Flipping its direction (curious = straighter) was rejected here, because
the data said that would make "curious" the losing trait in mixed worlds
without homes. **Changed 2026-11-18 at the project owner's request** so the
word matches the behaviour; section 7 confirms the consequence exactly.

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

## 7. Curiosity fix (2026-11-18)

### The rule

`genesis/traits.py`, `turn_percent`. Chance that a wandering agent turns on
a tick, with `turn_chance` 15 and `turn_span` 20:

| curiosity | 0 | 10 | 49 | 50 | 51 | 90 | 100 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| old rule: `15 + ((c - 50) * 20) // 100` | 5% | 7% | 14% | 15% | 15% | 23% | 25% |
| new rule: `15 - ((c - 50) * 20) // 100` | 25% | 23% | 16% | 15% | 15% | 7% | 5% |

`//` rounds down, so the new rule gives 16% for 45 to 49 and 15% for 50 to
54 (tested). Curiosity 50 is 15% either way, so all-neutral worlds and the
frozen Milestone 1 baseline are byte-identical (`tests/test_curiosity.py`,
`tests/test_baseline.py`, `make_baseline.py --check`: ALL SAME). Setting
`curiosity_straight` (1 = new, the default; 0 = old). Save version 9: older
saves get 0 and continue exactly as before (tested with a frozen v8 save).

### The study (FACT, `experiments/curiosity_study.py`)

Every agent at one curiosity, industriousness 50, set from outside the
simulation code (all traits 50 through the public settings, then each
founder's curiosity written as data; children copy it). 30 seeds (1-30) x
1,500 ticks. Each agent is tracked for its first 300 ticks; "survivors" live
through them, "early-dying" do not, and both are reported. Values are
per-seed results, then mean, sd and min..max over the 30 seeds. Files:
`experiments/results/curiosity_before.*` (old rule, run before the fix) and
`curiosity_after.*` (new rule, same seeds and settings).
`curiosity_before_check.*` is the old rule run again AFTER the fix with
`--rule old`: identical to `curiosity_before` (checked with diff).

Survivors, homes off (the clean world for this question; homes pull every
agent back within about 6 tiles):

| | old 10 | old 90 | new 10 | new 90 |
| --- | --- | --- | --- | --- |
| tiles per 1,000 wander ticks (MAIN) | 825 (sd 8) | 792 (sd 8) | 792 (sd 8) | **825** (sd 8) |
| distance from start at end (tiles) | 22.4 | 20.9 | 20.9 | **22.4** |
| turns per free wander tick | 16.1% | 28.3% | 28.3% | 16.1% |
| water ahead (forced turn) | 10.6% | 10.6% | 10.6% | 10.6% |
| ticks to first food | 10.4 | 10.8 | 10.8 | 10.4 |
| food eaten per 100 ticks | 5.8 | 5.8 | 5.8 | 5.8 |
| resting | 10.3% | 10.2% | 10.2% | 10.3% |
| starved (all tracked agents) | 48.6% | 48.3% | 48.3% | 48.6% |
| 90 explores more than 10 (per seed) | 0 of 30 | | 30 of 30 | |

Early-dying agents show the same pattern (new rule: 812 vs 842 tiles,
16.9 vs 18.7 tiles from start, 30 of 30 seeds). With homes on (today's
default world) curiosity makes almost no difference to exploring: 579 vs
583 tiles per 1,000 wander ticks, 5.5 vs 5.6 tiles from start; 90 beats 10
in 19 of 30 seeds (about luck). Wander share is about 46% (survivors) and
57% (early-dying) at every level.

**The new numbers are the old ones with 10 and 90 swapped, exactly.** That
is expected: the new rule at curiosity c is the old rule at 100 - c, and
turning is the only thing curiosity changes. Checked directly: a mixed world
(founders at 10/50/90, homes off) under the old rule and the same world with
every curiosity replaced by 100 - c under the new rule give identical events
for 1,500 ticks (seeds 42 and 7). So the fix adds no new behaviour; it gives
the existing behaviour the right name.

### Risks checked

- **More obstacle hits?** No: water is ahead on about 10.6% (homes off) and
  9.5% (homes on) of free wander ticks at every level.
- **Slower reaction to food nearby?** No: ticks to first food and food
  eaten are the same at every level. From the code: food in sight always
  wins over wandering (`_walk_to_food`), and curiosity is only read while
  wandering.
- **Travelling far without finding more?** Yes, mildly: curious agents end
  about 1.5 tiles (7%) further from their start without homes, and gather no
  more food.
- **Competition (from the mirror above, not re-run):** in mixed worlds
  without homes, the Milestone 2 result now belongs to the LOW-curiosity
  families: they out-breed the curious ones in 34 of 40 seeds. With homes on
  (the default) it was 25 of 40, about luck.
- **Whole world** (`experiments/results/stage_compare_curiosity_fix.txt`, 5
  seeds x 3,000 ticks, default world): new rule pop 93.4, starved 62.7%,
  births 899, age 317; old rule 93.6, 62.9%, 894, 319. All Milestone 2 bands
  hold.

### Acceptance check (FACT, `tests/test_curiosity.py`, Acceptance)

Two otherwise identical agents (same world dice, same start, open grass, no
food, no home), curiosity 10 and 90, 500 ticks, 20 pairs: the curious one
changes direction about 31 times against 101, in all 20 pairs; it ends
further from its start in 18 of 20 (mean 125 against 51 tiles) and visits
more different tiles in 17 of 20 (452 against 423).

**In plain words:** a curious agent keeps walking the way it is going and
only turns now and then, so it gets far and keeps seeing new ground. An
incurious agent changes direction about every fourth step, so it zigzags
around the same spot. In the real world the difference is small, because
agents only wander when no food is in sight, a "turn" picks a random
direction that can be the same as before, water forces turns anyway, and
homes keep everyone within about 6 tiles.

