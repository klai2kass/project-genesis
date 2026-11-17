# Milestone 2, version 2: the staged plan, and what was built

**Status (checked 2026-11-17 against the code): BUILT.** Approved by the owner
on 2026-11-17 (`rest_resume = 70`); implemented in commit `e3e07c3`;
measured in `docs/MILESTONE2_REPORT.md`. The text below is the approved plan,
kept as the design record. Where the build differs, "As built" says so.

## As built (read this first)

| Stage | Plan | As built |
| --- | --- | --- |
| 0 baseline tools | digests, frozen baseline, v2 fixture | Done (`genesis/digest.py`, `experiments/baseline/`, `tests/test_baseline.py`) |
| 1 data, save v3 | new fields, migration | Done. v1/v2 saves migrate and keep their old rules (`MILESTONE1_RULES` in `genesis/save.py`) |
| 2 traits, no effect | `traits.py`, `trait_report.py` | `traits.py` done. `trait_report.py` was not written; `experiments/trait_drift.py` measures the same thing (real run against a control where traits do nothing) |
| 3 rest | `needs.py`, rest rule after gather, `stage_compare.py` | Done. All stage 3 bands hold (`experiments/results/stage_compare.txt`) |
| 4 trait effects + curiosity probe | formulas, opposite-trait tests, probe | Done. Probe: `experiments/curiosity_probe.py` (forced and mixed worlds, 10 seeds; no separate 50-vs-50 control, the seed-to-seed spread and per-seed paired differences play that role) |
| 5 emergence report | `emergence_report.py` | Written as `docs/MILESTONE2_REPORT.md` from `stage_compare.py`, `curiosity_probe.py`, `trait_drift.py`. Measures 3, 4 and 8 of section 7 were not computed |
| 6 scoring | conditional | Not built: the condition (a trade-off thresholds cannot express) was never shown |
| 7 company | gate | Not built (owner has not said "yes, add company"; no payoff exists) |
| 8 tidy | summary, docs | Docs done this session. `summary.py` does not yet report action mix or trait averages |

Stages 1 to 4 were committed together in `e3e07c3`, not one commit each.
Every number in the plan's formulas below matches the code
(`genesis/config.py`, `traits.py`, `needs.py`).

## Final proposed mechanics at a glance

- **Agent gets:** `needs.rest` (0 to 100, starts 100), `drain_acc` and `tire_acc` (small
  whole-number counters for half-rate energy drain and for tiring), and two traits:
  `curiosity` and `industriousness` (0 to 100). No sociability, no boldness,
  no company need, until each has a real use.
- **Founders:** each trait drawn independently with `between(40, 60)` from a
  separate seeded dice stream per agent, derived only from seed text and
  agent id (section 2a; main dice untouched, nothing extra to save).
  **Children:** parent's value plus an independent `between(-5, 5)` per trait,
  clamped to 0 to 100.
- **Eating, reproducing, gathering:** exactly as today, in the same order.
  Rest never overrides hunger: it is only possible when `energy > eat_below`
  (80), so it can never be chosen by a hungry or starving agent.
- **Rest:** a new rule after gather. Allowed when not hungry and
  `rest < 30` (the same for every agent), continuing until `rest >= 70`.
  Each resting tick gives `rest +3`; each moving tick takes off 0 to 2 rest
  points depending on industriousness (next line); nothing else changes it. Low rest costs nothing. Benefit: resting drains energy at half rate,
  using whole numbers and an accumulator (section 4).
- **Industriousness (option B, your decision):** how fast an agent tires
  while moving. Rest lost per 100 moving ticks = `100 - (industriousness -
  50)`: 150 for industriousness 0 (a lazy agent), 100 at 50 (exactly today's
  1 per move), 50 for 100 (a tireless agent). Integer accumulator, no
  decimals. The resting threshold is the same for everyone.
- **Curiosity:** changes how often a wandering agent turns, 5% to 25% per
  tick (15% at 50), see section 3 for exact behaviour and how we measure
  whether it matters.
- **Curiosity is judged by you from reported measurements**, not by a built-in pass/fail rule.
- **Measured against the frozen baseline** at stages 3 and 4: starvation,
  population, births, age at death, rest behaviour and speed (section 5).
- **Conditional, not planned:** scoring (stage 6, with explicit criteria) and
  company/sociability (stage 7, only with a payoff).

Written 2026-11-17. Replaces the build order in `docs/MILESTONE2.md` once you
answer the questions in section 6. It uses the checks in
`docs/MILESTONE2_REVIEW.md` and the numbers in `docs/STARVATION.md`.

Guiding principle (yours): **no rush toward complex AI. Simple rules whose
interactions produce behaviour we can measure and explain.** So this plan adds
the least machinery first: a few numbers per agent and thresholds in the
existing rule list. A scoring system and a "company" need are optional gates
at the end, not the start.

Labels: **FACT** (measured or read in code), **PREDICTION** (expected,
untested), **GUESS** (plausible, no evidence). Plain words: a **stage** is one
small build step with its own commit; a **digest** is a short code of
behaviour only (`genesis/digest.py`); a **band** is an allowed range.

## 1. Where I differ from the reviewer's order, and why

The reviewer's order was: investigate, data, rest, scoring, personality,
company, measure. I keep it except two changes:

- **Personality before scoring.** A trait can shift a threshold in the
  existing rule list or one simple rate ("tire 1.5 times as fast when lazy"). That already makes two agents act differently in the same
  situation, and the reason stays one readable sentence. A scoring system is
  only worth building if thresholds prove too rigid. (Your principle, and it
  avoids a second decision system.)
- **A measuring stage right after traits**, with a control run where traits
  do nothing, so we can tell selection from chance (review, finding 5).

## 2. The rules every stage must follow

- **Whole numbers only.** No decimals anywhere in agent state, needs,
  traits, scores or thresholds.
- **Neutral at 50.** A trait effect is
  `base + ((trait - 50) * span) // 100`
  where `//` is Python floor division (rounds toward minus infinity, also
  for negative numbers). At trait 50 the effect is exactly `base`, so an
  agent with all traits 50 behaves like the stage before.
- **Clamping.** Needs and traits are kept in 0 to 100 with
  `max(lo, min(hi, value))` after every change.
- **Percent chances** are drawn as `rng.below(100) < p` with `p` a whole
  number. (FACT: for p = 15 this equals today's `rng.chance(0.15)`; the
  baseline digest check proves it in stage 4.)
- **Dice.** New draws change all later behaviour. So: no new draws in the
  main dice stream until a stage says so. Trait dice come from their own
  stream, `Rng(seed_to_state("<seed>|traits|<agent id>"))`, one per agent,
  so they never disturb the main stream.
- **Ties** go to the earlier action in the fixed rule list. Agents act in id
  order, as today.
- **Settings.** Every tunable number (rest gain, thresholds, spans, mutation
  size) is a NEW key in `config.py`, changeable with `--set` and checked in
  `genesis/overrides.py`. Formulas stay in code. **No existing default
  changes** (not `repro_cooldown`, not `regrow_per_tick`, not
  `eat_below`). Changing any of them needs experimental evidence and your
  explicit yes first.
- **No survival penalty from needs.** A low rest or low company value never
  removes energy or lifespan by itself. Rest only gives a benefit when it is
  used.
- **Eating is untouched** in every stage up to and including scoring
  (`eat_below=80`, checked first).
- **The Milestone 1 baseline stays available** (`baseline.json`, digests,
  v2 fixture, `tests/test_baseline.py`). No runtime switch.
- **Every stage:** all old tests stay green, a "why" sentence names any
  trait that changed the outcome, and `STATUS.md` is updated and committed.

## 2a. Dice streams, exactly

**Two kinds of dice exist.**
1. **The main stream** (today's only one). One whole number, `world["rng"]`,
   saved in every save. Each tick `step()` builds `Rng(world["rng"])`, uses it
   (food regrowth, wandering, child placement, lifespans) and stores the new
   number back. Unchanged by this plan.
2. **Trait streams** (new). One per agent, used only to make that agent's
   trait values, and never stored.

**How a trait stream is derived (the whole rule):**

    stream = Rng(seed_to_state("<seed text>|traits|<agent id>"))

- `<seed text>` is `world["seed"]`, already saved as text (`world.py`: `str(seed)`,
  so `42` and `"42"` are the same seed).
- `<agent id>` is the agent's own id (founders 1 to 50, then `next_id`, which
  is saved and never reused).
- `seed_to_state` is the existing `zlib.crc32` of that text (`rng.py`), the same
  function that already turns seeds into the main stream's start number.
- Draw order is fixed: first curiosity, then industriousness. Founders:
  `between(40, 60)` for each. Child: `between(-5, 5)` for each, added to the
  parent's saved value, then clamped.
- The stream makes exactly those two draws and is thrown away. The results
  live in the agent's saved `traits`.

**Why it stays deterministic across save and load:** a stream depends only on
three saved facts (seed text, agent id, and for children the parent's saved
traits) and never on a running counter. There is no generator state to save
or restore. A world saved at any tick and loaded again would create the same
traits for the same next newborn, as an uninterrupted run would.

**Can unrelated random draws affect trait generation? No.** The trait stream
never reads or writes the main stream and no other code touches it, so adding,
removing or reordering any main-dice draw (wandering, regrowth, child
placement) cannot change a single trait value. The reverse also holds: making
traits draws nothing from the main stream, so every existing event stays the
same (the stage 2 digest check proves it).

**Known limits (FACT unless stated):**
- Two different (seed, id) texts could in principle map to the same 32-bit
  start number, and those two agents would get identical traits. Checked: no
  collision among ids 1 to 5,000 for each of the 5 baseline seeds. A world
  that creates more than about 5,000 agents has a small, growing chance
  (GUESS: well under 1% below 10,000 agents).
- The first draws of neighbouring ids look evenly spread: 3,000 first draws
  fell in ten equal buckets with counts 279 to 323 (expected 300).
- Changing the text rule changes every trait: it is part of the save
  format and must never be edited casually (golden tests below).

**Tests (written now, they use only today's `Rng`):**
`tests/test_trait_streams.py`, 5 tests: golden numbers (for example seed 42,
agent 1 gets curiosity 60, industriousness 53; agent 2 gets 42 and 49; seed 1,
agent 1 gets 54 and 44); depends only on seed and id; real worlds run with the
main dice cannot change the derived values; the seed text and ids survive
save and load; no start-number collisions for 5 seeds x 5,000 ids and an even
spread. Stage 2 must make `genesis/traits.py` reproduce these golden numbers
and the tests switch to calling it. Stage 2 adds more: founders in 40 to 60,
child within 5 of its parent and inside 0 to 100, clamping at 0 and 100,
neighbouring children independent, and the event digest equal to stage 1.

## 3. Definitions: needs and traits (only what an agent can see now)

An agent can currently use: its energy, pack, age, cooldown, heading, its own
position, and the 9 x 9 box around it (food on each tile, water). It can
also be given the positions of other agents (not used today). It has **no
memory of places** (FACT, review finding 3), and this plan adds none.

### Needs

| Need | Range | Start | Changes (per tick) | Used by |
| --- | --- | --- | --- | --- |
| hunger | `energy` 0 to 100, exists | 50 to 60 | -1 | unchanged |
| rest (stage 3) | 0 to 100, 100 = rested | 100 | moving -1; resting +3; eating, gathering, reproducing 0; clamped | rest rule below |
| company (stage 7 only) | 0 to 100 | 70 | another agent within 2 tiles: +5; else -1 | later |

Stage 1 adds `rest` and the two counters `drain_acc` and `tire_acc` (whole
numbers, 0 at start); `company` is added in the stage that uses it, so no field sits unused.

### Traits (0 to 100, 50 = neutral, fixed for life)

| Trait | Plain meaning | Effect, stage 4 (all use the neutral-at-50 rule) | Only needs |
| --- | --- | --- | --- |
| industriousness | how slowly it tires while moving | rest lost per moving tick, in hundredths: `tire_rate = tire_base - ((industriousness - 50) * tire_span) // 100`; with `tire_base` 100 and `tire_span` 100 this is 150 (lazy, 0) down to 50 (tireless, 100); exact formula in section 4 | rest only |
| curiosity | how restless its wandering is (exact behaviour below) | chance of a voluntary turn on each wandering tick = `turn_chance + ((curiosity - 50) * turn_span) // 100` percent; with 15 and 20 that is 5 to 25 | its own heading only. It does NOT mean seeking unseen or unvisited places: agents remember no places |
| *(boldness)* | *deferred until the simulation has real risk mechanics (your Q2)* | *no field, no effect* | |
| *(sociability, boldness)* | *not stored, not defined* | *added with a migration when a meaningful social or risk behaviour exists (stage 7 or later)* | |

Rounding examples (so you can check by hand): industriousness 30 gives
`100 - (-20*100)//100 = 100 + 20 = 120` hundredths per move (the 100s cancel,
so this formula never needs rounding). Industriousness 75 gives
`100 - (25*100)//100 = 75`. Curiosity 10 gives `15 + (-40*20)//100 = 15 +
(-8) = 7` (the only trait formula that rounds; -800 // 100 is exactly -8).

**Exactly how curiosity works** (read from `agents.py:48-61`, `_wander`). An
agent wanders (a) when no reachable food is in sight (the "search" action,
45.8% of all decisions, FACT) and (b) when its pack is full and it is not
hungry ("explore", 5.9%). Each wandering tick:
1. One dice draw. If `rng.below(100) < p` (p = the curiosity formula; today
   `rng.chance(0.15)`, FACT-checked equal over 2 million draws) the agent
   wants to turn. It also must turn if the tile ahead is water.
2. A turn picks one of the land directions around it (up to 8, including its
   current one) at random, so the real change-of-direction rate is a bit
   below p. A turn is the only thing curiosity changes. Eating, gathering,
   walking to seen food and reproducing are untouched.
3. Otherwise it keeps walking the same way.
So a low-curiosity agent walks long straight lines; a high-curiosity agent
zigzags and stays closer to where it began. **Whether either helps is not
known** (GUESS: straight lines cover more new ground and find food faster in
open country, zigzags search one patch more thoroughly). That is exactly
what we measure, and curiosity is judged "meaningful" or "not" by the
numbers in stage 4, not by assumption.

**Why neither active trait needs memory** (review finding 3): curiosity is
turning frequency, industriousness is a tiring rate. Both use only the
agent's own heading, energy and rest.

**No trait changes births directly** (boldness, which did, is deferred).
FACT from `STARVATION.md`: births are the lever on starvation, so keeping
them untouched keeps the starved share comparable with the baseline. Traits
can still affect births indirectly (a better-fed agent reaches energy 90
more often).

Inheritance and founders (your decisions): every trait value is drawn
separately and independently, in the order curiosity, then industriousness,
from the agent's own trait dice stream (section 2).
- Founder: `between(40, 60)` for each trait.
- Child: `clamp(parent + between(-5, 5), 0, 100)` for each trait; the size 5
  is config key `trait_mutation`, founders' range is `trait_founder_min` 40
  and `trait_founder_max` 60.
Only about 16 generations fit in 3,000 ticks (FACT), so expect small drift.

## 4. Rest and company: incentives, alternatives, predicted effect on deaths

Today only energy matters, at 1 per tick (`sim.py:41`). A need nobody can
profit from is just a number, and a trait with no effect on survival or
children cannot be selected (review finding 2).

### Rest (stage 3)

Rule: a voluntary `rest` action is allowed only if `energy > eat_below`
(never while hungry) and either `rest < rest_below` (30, same for all) or the
agent rested last tick and `rest < 70` (so it does not flip between rest and
move). It is checked after eat, reproduce and gather, so it only replaces
walking (explore and stock-up). Resting is deliberately **not free**.

| Option | What it does | Effect on deaths | Label |
| --- | --- | --- | --- |
| **A. Half-price living while resting (your choice)** | resting drains energy at half rate, done with an integer accumulator (below) | explore is only 5.9% of all decisions (FACT), so saving half of that is about 3% of all energy. Population about +3%, starved share within plus or minus 2 points | PREDICTION |
| B. Rested agents see farther | vision +1 while `rest >= 80` | searching is 46% of decisions (FACT), so this could cut search time a lot: population up noticeably, starved share down. Also about 25% slower runs (box 11 x 11 instead of 9 x 9) | PREDICTION (size unknown); GUESS on the speed figure |
| C. Resting speeds up the child cooldown | cooldown -2 per resting tick | more births; `repro_cooldown=100` gave 78.4% starved against 67.7% (FACT), so expect starved share up | PREDICTION |
| D. Penalty only: tired agents skip every second move | no incentive, only a cost | tired agents die more; no reason to choose rest except to avoid the penalty | PREDICTION |

Rest recovers by +3 per resting tick (config `rest_gain`), so resting really
fills the need. Low rest never costs energy or lifespan (your Q1). **Rest
never overrides hunger:** the rest rule contains `energy > eat_below`, and
the eat rule is checked first, so an agent at 80 or less never rests (a test
checks this over a whole run, not just one case). Option A was chosen
because it is the smallest push on the food balance.

**Half-rate drain, exact integer rule** (no decimals anywhere). Today
`sim.py:41` takes 1 energy at the start of every agent's turn. Config:
`drain_units_per_energy = 2`, `rest_drain_units = 1`. On a tick where the
agent's chosen action is `rest`, after the normal 1-energy drain:
1. `energy += 1` (undo the normal drain; never above where it was before).
2. `drain_acc += rest_drain_units` (1).
3. If `drain_acc >= drain_units_per_energy` (2): `drain_acc -= 2` and
   `energy -= 1`.
Result: two resting ticks cost exactly 1 energy, in a fixed pattern (the
first resting tick is free, the second pays), and `drain_acc` is 0 or 1 and
is kept between rests. No dice, no age parity, no floats. Because rest needs
`energy > 80`, the refund can never rescue a dying agent. Free rest stays
impossible (an agent that rests forever never starves; review "missed" list).

### Complete rest behaviour, with industriousness (option B)

Settings (new config keys): `rest_below` 30, `rest_resume` 70, `rest_gain`
3, `tire_base` 100, `tire_span` 100, `tire_scale` 100. There is no
per-trait threshold any more. Only moving ticks tire an agent; eating,
gathering, reproducing and resting do not; rest is clamped to 0 to 100.

**Tiring rule (whole numbers).** On a moving tick, per agent:

    tire_acc += tire_rate(industriousness)       # tire_rate = 100 - (ind - 50)
    loss      = tire_acc // 100                  # whole rest points lost now
    tire_acc  = tire_acc - loss * 100            # always 0 to 99, kept in the save
    rest      = max(0, rest - loss)

| industriousness | tire_rate | rest lost on consecutive moves (first 12) | long-run average per move |
| --- | --- | --- | --- |
| 0 (lazy) | 150 | 1,2,1,2,... | 1.5 |
| 25 | 125 | 1,1,1,2 repeating | 1.25 |
| 50 | 100 | 1,1,1,1,... | 1.0 (today's rate) |
| 75 | 75 | 0,1,1,1 repeating | 0.75 |
| 100 (tireless) | 50 | 0,1,0,1,... | 0.5 |

Over any 100 moving ticks the total loss equals `tire_rate` exactly, for all
101 trait values (checked by test), so nothing is lost to rounding. Range:
50 to 150, never below 0.5 or above 1.5 rest per move.

**Decision, checked every tick in this order** (first that fits wins,
exactly like today): eat, reproduce, gather, **rest**, then move. `rest` fits
only when ALL of these hold:
1. `energy > eat_below` (80). Hunger always wins: eat is checked before, and
   a hungry agent without a pack goes to move/search instead.
2. EITHER `rest < 30` (starting a rest), OR the agent rested on its previous
   tick and `rest < 70` (continuing, so it does not flip every tick).

**What this means in practice**
- **Does an agent eventually rest?** Yes, whenever it is not hungry and has
  nothing to eat, reproduce or gather. Rest only falls on moving ticks. From
  full (100), the first time it drops below 30 takes 48 moves for
  industriousness 0, 71 for 50 and 142 for 100. If it is hungry the whole time
  it never rests; its rest value falls to 0 and stays there with no penalty
  (your Q1). The moment it eats back above 80 and is idle it rests.
- **Stints (exact).** A stint **starts** on the first tick where `rest < 30`
  (so rest is 28 or 29: a move loses at most 2) and **ends** on the first tick
  where, after resting, `rest >= 70` (70 or 71). It does NOT run to 100: the
  stop value is `rest_resume` = 70. Calculation of the length: starting at 29,
  after 13 resting ticks rest is `29 + 3*13 = 68`, still below 70; after 14 it
  is `29 + 3*14 = 71`, which is at least 70, so the stint is **14 ticks**.
  Starting at 28 the 14th tick gives exactly 70, again 14 ticks. So every
  stint is 14 ticks for every industriousness value (tested for all 101).
  (If it rested from 29 up to 100 it would take `ceil(71 / 3) = 24` ticks;
  that is the alternative shown below, not the proposal.) What differs between
  agents is how long they work between stints.
- **A stint is interrupted, not forced:** it stops at once if energy drops to
  80 or less (hunger wins), or if the agent gathers, reproduces or eats on a
  later tick. After an interruption the "continue" clause no longer applies,
  so rest resumes only when `rest < 30` again. A tired agent whose rest sits
  between 30 and 70 after an interruption keeps walking: deliberate and simple.
- **Rest replaces walking toward food** while the agent is not hungry
  (including stocking up). A tired, well-fed agent with an empty pack rests
  rather than fetches. That is the cost of resting: it is not finding food
  (46% of decisions today are searching, FACT).
- **Energy interaction:** needs `energy > 80`, so rest never rescues a dying
  agent. Energy during a stint falls by 1 every second tick (half-rate drain,
  `drain_acc`), so a 14-tick stint costs 7 energy. A well-fed agent at 100
  can rest about 40 ticks before reaching 80, after which hunger takes over,
  even mid-stint.
- **Rest value and energy are independent** except through that gate: low
  rest never drains energy (Q1), and high energy never raises rest.

**Why the resting share does not depend on where the stint ends.** Over one
whole cycle rest ends up where it began, so what is lost while moving equals
what is gained while resting: `moves * (rate/100) = rest_ticks * 3`. Therefore

    share of time resting = rest_ticks / (rest_ticks + moves) = rate / (rate + 300)

(up to one tick of edge effect at each end). With rate 150, 100, 50 that is
33.3%, 25.0% and 14.3%. The stop value 70 only changes the length of each
stint and the work period, not the share.

**Cycle table, steady state (FACT: run as a stand-alone model of the rules,
agent never hungry, nothing to gather; the first descent from rest 100 is
excluded; real agents are interrupted, so real shares will be lower and are
not measured yet).** Start and end values are what the model produced.

| industriousness | tire rate (per 100 moves) | stint starts at rest | stint ends at rest | rest ticks per stint | moves between stints | share of time resting | energy per cycle |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 150 | 28 | 70 | 14 | 28 | 33.3% | 28 + 7 = 35 |
| 25 | 125 | 28 or 29 | 70 or 71 | 14 | 33.6 on average | 29.4% | moves + 7 |
| 50 | 100 | 29 | 71 | 14 | 42 | 25.0% | 42 + 7 = 49 |
| 75 | 75 | 29 | 71 | 14 | 56 | 20.0% | 56 + 7 = 63 |
| 100 | 50 | 29 | 71 | 14 | 84 | 14.3% | 84 + 7 = 91 |

Correction: the earlier table (33.1, 28.9, 24.7, 19.6, 14.0%) was measured over
3,000 ticks that started with one long first descent from rest 100, which
slightly lowered every share. The steady-state numbers above are the right
ones. The 14-tick length itself was already right.

**Alternative, not proposed: rest until 100.** Starting at 29 it takes 24 ticks
(`29 + 3*24 = 101`, capped at 100). Shares from the model: 33.3%, 25.3% and
14.5% for industriousness 0, 50, 100, with 48, 71 and 142 moves between stints.
Longer stints, almost the same share, but a rested agent would spend a longer
time unable to fetch food and the energy saving per stint would be 12 instead
of 7. Decided: keep 70.

**Expected behavioural differences (PREDICTION unless noted; none measured in
the real world yet).**
- A lazy agent spends a third of its idle-and-fed time resting instead of
  walking, so it searches and fetches less (searching is how food is found, 46%
  of decisions, FACT) but pays half price for those rest ticks. An industrious
  agent walks three times as long between stints (84 moves against 28) and rests 14%
  of the time, so it covers more ground and finds more food but pays full drain.
- Which wins is genuinely open (GUESS). If food is scarce and far, walking more
  should help the industrious agent; if food is plentiful near spawn, the lazy
  agent's saved energy may win. That is the real trade-off the trait was
  meant to carry, and what stage 5 selection tests will show.
- Since rest is gated by `energy > 80` and idle-ness, real rest shares will be
  lower than the table; the difference between traits should shrink in
  proportion, not vanish. Measured in stage 3 and 4.
- The time spent resting depends on the trait, so the share of decisions that
  are `rest`, the mean rest value, and the distance walked per 100 ticks all
  become trait-dependent measures for `stage_compare.py` and the emergence
  report.

**Mathematical checks of the extremes (done now, run `python3 -m unittest
tests.test_rest_design`):** rate is exactly 150, 100 and 50 at 0, 50 and 100;
it never increases with industriousness; the accumulator stays below 100; total
loss over 100 moves equals the rate for every value 0 to 100; the loss
patterns at 0, 50 and 100 are as in the table; first tiredness at 48, 71, 142
moves; ten resting ticks cost exactly 5 energy. **Complete cycle
(`CompleteRestCycle`, 7 more tests):** every stint starts at rest 28 or 29
(below 30), ends at 70 or 71 (at least 70, never at 100) and lasts exactly 14
ticks for all 101 trait values, with the hand calculation 29+3*13=68,
29+3*14=71; steady shares 33.3%, 29.4%, 25.0%, 20.0%, 14.3% match
`rate/(rate+300)`; the rest-to-100 alternative gives 24-tick stints and shares
within 0.2 points; every complete cycle costs exactly `moves + 7` energy with
`drain_acc` back at 0; rest never leaves 0 to 100.

**Tests for the real code (specified now; need stage 3 and 4 code, not
written yet):**
1. Lazy (industriousness 0), never hungry, nothing to find: rest falls 1, 2,
   1, 2, ... per move from 100 until it first drops below 30 after 48 moves;
   then it rests: +3 per tick up to 70 or more.
2. Tireless (100): same world; first rest begins after 142 moves, with losses
   0, 1, 0, 1, ...
3. Never while hungry: for every tick of 5 seeds x 2,000 ticks, no `rest`
   decision when pre-decision energy is 80 or less (count must be 0).
4. Hunger interrupts: an agent mid-stint whose energy reaches 80 stops resting
   the next tick and does not rest again until energy is above 80.
5. Interruption by gather: after a gather during a stint, the next tick follows
   the "rest < 30" rule again, not the continue rule.
6. Drain: two resting ticks cost exactly 1 energy; ten cost 5; `drain_acc`
   stays 0 or 1; a non-resting tick leaves `drain_acc` unchanged.
7. Tiring: `tire_acc` is always 0 to 99; only moving ticks change it and
   `rest`; a clamped rest at 0 stays at 0.
8. Neutral: with industriousness forced to 50, tiring is exactly 1 per move,
   so the stage 3 and stage 4 event digests are equal.
9. Hungry forever: an agent kept at energy 80 or less never rests; its rest
   ends at 0 with no energy or lifespan change attributable to it.
10. Real-world check: over 5 seeds, mean resting share of decisions is lower for
    industriousness 0 than 100 in the forced-trait experiment, same seeds.

### Company (stage 7, a gate, not a plan)

Company has no reason to exist today: agents cannot see each other and already
share tiles. Build it only if stage 5 shows traits matter and you want
sociability to do something.

| Option | What it does | Effect on deaths | Label |
| --- | --- | --- | --- |
| **A. Shared sight (proposed)** | an agent with nothing in view may follow the food target of an agent within 2 tiles | less searching, so more agents; clustering has a cost (they crowd the same food), a real trade-off for sociability to evolve against | PREDICTION; crowding cost is GUESS (not measured) |
| B. Food sharing | a neighbour with pack of 2 or more gives 1 food to an agent at energy 20 or less with an empty pack | directly removes some starvation (6.2% die one tick after gathering, FACT; sharing would not help those, but would help others); donors pay | PREDICTION |
| C. Shared lookout | vision +1 while another agent is within 2 tiles | like rest option B, plus favours clusters | PREDICTION |

Gate for stage 7: stages 3 to 5 done, you answer "yes, add company", AND a
payoff from the table above is built in the same stage. **No `seek_company`
action and no company need are added on their own**: an action that only
moves agents closer together, with no use, is not allowed (your constraint).
Until then sociability does not exist; it is added, with a save migration, only when this payoff exists.

## 5. The build sequence

Each stage = one commit, tests green, STATUS updated. "Unchanged" checks use
`genesis/digest.py` and `experiments/baseline/baseline.json` (built this
session; stage 0 is already done).

**Stage 0 (done): baseline tools.** Files: `genesis/digest.py`,
`experiments/baseline/make_baseline.py`, `baseline.json`,
`tests/fixtures/save_v2_seed42_t300.json`, `tests/test_baseline.py`.
Check: `python3 -m unittest tests.test_baseline` (4 tests) and
`python3 experiments/baseline/make_baseline.py --check`.
Proves: today's behaviour is frozen and a v2 save loads and continues
exactly.

**Stage 1: data only, save version 3.** Files: `genesis/world.py`
(`make_agent` adds `needs: {"rest": 100}`, `drain_acc: 0`, `tire_acc: 0` and two traits at 50 (curiosity, industriousness; no sociability);
`SAVE_VERSION = 3`), `genesis/save.py` (`_migrate_2_to_3`, defaults,
`migration_log`), `genesis/sim.py` (die events also carry traits and needs), `genesis/config.py`
and `genesis/overrides.py` (new keys only: `rest_gain`, `rest_below`,
`rest_resume`, `tire_base`, `tire_span`, `tire_scale`, `rest_drain_units`, `drain_units_per_energy`,
`turn_chance`, `turn_span`, `trait_mutation`, `trait_founder_min`,
`trait_founder_max`; no
existing default touched),
`tests/test_save_load.py` (v2 fixture migrates; a v3 save round-trips).
Check: unit tests, then `make_baseline.py --check`.
Must stay unchanged: event digest and behaviour digest for all 3 baseline
seeds, exactly; the save-fixture digest. **Expected change:** the full-world
`fingerprint` (new fields); `tests/test_baseline.py` then compares digests,
counters and `fingerprint` is kept as a second recorded value in the
baseline, replaced only in this commit. Proves: old saves migrate, nothing
behaves differently.

**Stage 2: trait creation (founders 40 to 60) and inheritance (+/- 5), still no effect.** Files:
`genesis/traits.py` (new: create, inherit, own dice stream), `world.py`,
`sim.py` (child gets inherited traits), `experiments/trait_report.py` (mean
and spread per generation). Check: unit tests and digests exactly equal to
stage 1, even though traits now vary (a test checks founders lie in 40 to 60, children differ from the parent by at most 5, values stay in 0 to 100). Proves: inheritance works and the main
dice are untouched. **Also gives the control:** with traits having no effect,
the report shows how far chance alone moves the averages (neutral drift).

**Stage 3: rest need and rest action (option A).** Files: new
`genesis/needs.py`, `agents.py` (one new rule after gather), `sim.py` (apply
rest, accumulator drain), `whylog.py`, tests (including: no rest at energy
80 or less, ever; two resting ticks cost exactly 1 energy; rest need
recovers +3 and is clamped). Check: unit tests, then 5 seeds x 3,000 ticks
with `experiments/stage_compare.py` (new in this stage) against
`baseline.json` and the bands below. It prints, side by side with the
baseline: population, starved share, births, age at death, **rest behaviour**
(share of all decisions that are rest, mean rest need, mean energy saved per
resting tick, count of rest decisions at energy 80 or less which must be 0)
and **speed**. Changes behaviour on purpose; the
reference is re-recorded in `baseline.json` under `stage3`, in its own
commit. Proves: a need with a cost and a reward changes behaviour without
breaking the balance.
**Bands (all 5 seeds, vs the FACT baseline: mean pop 89.1, spread 88.6 to
89.6; starved share 67.7, spread 67.0 to 69.1; births 918; age at death 295):**
mean population after tick 500 within 80 to 98, starved share within 62 to 73,
births within 830 to 1,010, average age at death within 265 to 325, no run
dies out. Outside a band: stop and report, do not tune silently.
**Speed (FACT, measured today, seed 42, 2,000 ticks, 3 runs):** with history
on 631, 610, 593 ticks/s; history off 703, 713, 686 ticks/s. Timings vary by
about 10% between runs and by machine load (an earlier session measured about
850), so speed is compared in the same session: unpack the baseline code
with `git archive c48e64c | tar -x -C <empty folder>` (that commit's
`decide`, `sim` and `world` are the Milestone 1 rules) and time both. Limit:
no more than 25% slower in stage 3 and no more than 2x slower at the end.

**Stage 4: trait effects as thresholds.** Files: `agents.py` (the two
formulas above, no new dice: curiosity uses `rng.below(100) < p` in place of
`rng.chance(0.15)`), `whylog.py`, tests. Check, in order: (1) with all traits
forced to 50 the event digest equals stage 3 exactly; (2) opposite-trait test
in a tiny world (curiosity 90 turns more often than 10; industriousness 10
loses rest faster per move than 90 (150 against 50 per 100 moves); neither trait ever changes the eat rule);
(3) 5 seeds against the stage 3 bands, widened by 5 points for starved share,
with `stage_compare.py` repeated. `stage_compare.py` also reports, per
industriousness range, resting share, distance walked per 100 ticks,
food gathered per 100 ticks and survival.
Proves: personality alone makes same-situation choices differ, and every
difference is explained by a trait in the "why".

**Curiosity probe (part of stage 4, `experiments/curiosity_probe.py`).**
Clean experiment: same seeds, all agents curiosity 10, then 50, then 90
(`trait_mutation=0` and a forced start value, so only curiosity differs).
For each, from the position of every wandering agent (events carry x, y):
- **Straightness:** net distance moved over a whole search episode divided by
  steps walked (1.00 = a straight line). Integers: percent.
- **New ground:** distinct tiles visited per 50 wandering ticks.
- **Time to food:** length of search episodes (ticks from "nothing in sight" to
  the next gather).
- **Outcome:** starved share and mean population.
**No automatic verdict.** The script prints the actual measurements for
curiosity 10, 50 and 90, per seed and averaged, with the seed-to-seed spread,
and also a control (curiosity 50 against 50 on a different set of seeds) so
you can see how much the numbers move by chance alone. Rule-of-thumb
indicators, **reading aids only, not proof that curiosity is useful or
useless**: a straightness or new-ground difference between 10 and 90 clearly
larger than the control's spread suggests the trait changes exploration;
differences inside the spread suggest it does not at this map size.
(The earlier 15% and 10% marks are dropped as a decision rule.) The report
lists the numbers and what they might mean; **you decide** whether the effect
is worth keeping, reworking or removing. All five measures are "not tracked"
today and are computed by the script from events, so no simulation change is
needed.

**Stage 5: emergence report.** Files: `experiments/emergence_report.py`
(measures in section 7, computed over 5 seeds, neutral control vs real).
Check: run it; the report is the check. Proves (or disproves) that traits
produce selection beyond chance. If it disproves, that is a result, not a
failure.

**Stage 6 (conditional, not planned): scoring for a few actions.** Build it
only if experiments show that threshold-based decisions cannot express a
desired trade-off. Concrete test, decided in advance: at least two
behaviours we want (for example "rest vs finish stocking up" for an agent that
is both tired and low on food in its pack) cannot be produced by moving one
threshold per trait without also causing a worse result elsewhere, shown by
the stage 4 and 5 numbers. If that is not shown, stage 6 stays unbuilt.
If built: eat stays a fixed rule before scoring with `eat_below=80` (review
finding 4); scores are integers scaled by 100 (`150` means 1.50), products
divided with `//`; formulas in code, tunable numbers in `config.py`; no
noise; with all traits 50 the event digest must equal the stage 4 reference.

**Stage 7 (gate): company** (section 4), with a neighbour grid so cost stays
near one pass over agents per tick. Check: the bands again, plus a
clustering measure.

**Stage 8: tidy.** `summary.py` (action mix, trait averages), README, STATUS,
VISION.

## 6. The seven questions: your decisions and what they mean

Options and consequences are kept so you can revisit. **Chosen** = your answer.

**Q1. Should low rest or low company cost energy or lifespan?**
**Chosen: No.** (Option A.) Alternative B, a punishment for very low rest,
was rejected. Effect on the plan: rest has only a benefit (half-price living
while resting, only when not hungry); traits are selected through that
benefit. Reversible: yes.

**Q2. Which traits?** **Chosen: curiosity and industriousness now.**
Boldness deferred until real risk mechanics exist; sociability removed from
stored data (your later correction) and added, with a save migration, only
when a meaningful social behaviour is built. Effect: both traits act; no trait
changes the reproduction threshold, so births stay comparable with the
baseline. Reversible: adding a trait later is a save migration.

**Q3. Inheritance and mutation.** **Chosen: founders get independent seeded
values from 40 to 60 for each trait; a child gets the parent's value plus an
independent integer from -5 to +5 per trait, clamped to 0 to 100.** Effect:
founders already differ a little (so the first generations have material for
selection); drift is slow. FACT: only about 16 generations fit in 3,000 ticks;
the neutral control (stage 2) tells us what chance alone does. Reversible:
config keys.

**Q4. Randomness in choices.** **Chosen: none initially.** Variation comes
from traits and from the world (food, position). The existing wander dice
stay. Effect: no new draws, so the digest checks stay exact. Revisit only
after experiments.

**Q5. May agents share a tile?** **Chosen: yes, as now.** No collision
system. Effect: movement and baselines unchanged.

**Q6. The old rule order.** **Chosen: no runtime switch.** The Milestone 1
baseline is the frozen reference (`baseline.json`, digests, v2 fixture,
`tests/test_baseline.py`). Effect: one decision system.

**Q7. Where scoring lives.** **Chosen: formulas in code, tunable numbers in
`config.py`, no separate file.** Effect: numbers are saved inside each world
(old saves keep old numbers, good for reproducibility) and changeable with
`--set`; new keys need override rules and a `_repair` default.

## 7. How we will measure emergence

"Emergence" here means: behaviour nobody wrote as a rule that we can
measure and explain from the simple rules. Eight cheap measures:

| # | Measure | Meaning | Data today | Needs |
| --- | --- | --- | --- | --- |
| 1 | Action mix over time | share of eat, gather, search, walk-to-food, explore, rest | **Computable now** (`starvation_study.py` does it; today 5.4/5.5/45.8/37.0/5.9% for eat/gather/search/to_food/explore, rest 0) | rest action in stage 3 |
| 2 | Population balance | mean population, lowest and highest after tick 500, births and starved share per 100 ticks | **Computable now** (baseline: pop 89.1, starved 67.7%, births 918 per 3,000 ticks) | nothing |
| 3 | Situation split rate | of agents in the same situation (energy band, pack, food in view), the share that chose differently | **Computable now** from a snapshot per tick (script only); baseline is not computed yet | nothing for baseline; traits to explain it |
| 4 | Explained split | how much of measure 3 disappears once agents are grouped by trait range | not tracked | traits (stage 2+) |
| 5 | Trait averages and spread per generation | do traits drift, and how much is just chance (neutral control) | not tracked | traits (stage 2) |
| 6 | Selection test | children and lifespan by trait range, real run vs neutral control | not tracked (children and lifespan are derivable now) | die events carry traits (stage 1) |
| 7 | Different seeds, different outcomes | final trait averages per seed; do they spread more than the control | not tracked | traits, 5 seeds |
| 8 | Clustering | average number of other agents within 3 tiles, against random placement | **Computable now** from agent positions; baseline not computed | nothing; needed for stage 7 |

Pass rule for "interesting": traits explain a visible part of measure 3 (4)
AND measure 6 or 7 differs from the neutral control by more than the control
varies between seeds. Otherwise the honest result is "no emergent selection
at this scale".

## 8. Your answers

Recorded from your messages of 2026-11-17. The whole design was approved
the same day.

| Question | Your answer | Notes |
| --- | --- | --- |
| Q1 low needs penalty | No direct cost in energy or lifespan | Rest recovers +3 per tick; rest never overrides hunger; benefit is half-rate drain via integer accumulator |
| Q2 trait set | Curiosity and industriousness; boldness deferred; sociability removed from stored data for now | Add sociability with a migration when a social behaviour exists |
| Q3 inheritance and mutation | Founders: independent seeded 40..60 per trait. Children: parent plus independent -5..+5, clamped 0..100 | |
| Q4 randomness | No decision noise initially | Revisit after experiments |
| Q5 tile sharing | Agents may share tiles | No collision system |
| Q6 rule-order switch | No runtime switch | Frozen baseline plus regression tests |
| Q7 scoring table location | Formulas in code, tunable numbers in config | No separate settings file |

Resolved open points: founders 40 to 60; scoring stays conditional (stage 6
has an explicit test); rest benefit is half-rate energy drain with an integer
accumulator.
