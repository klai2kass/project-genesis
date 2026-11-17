# Milestone 2, version 2: a staged plan (nothing here is built)

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
  existing rule list ("reproduce when energy is at least 90, minus a bit for
  bold agents"). That already makes two agents act differently in the same
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
- **Every stage:** all old tests stay green, a "why" sentence names any
  trait that changed the outcome, and `STATUS.md` is updated and committed.

## 3. Definitions: needs and traits (only what an agent can see now)

An agent can currently use: its energy, pack, age, cooldown, heading, its own
position, and the 9 x 9 box around it (food on each tile, water). It can
also be given the positions of other agents (not used today). It has **no
memory of places** (FACT, review finding 3), and this plan adds none.

### Needs

| Need | Range | Start | Changes (per tick) | Used by |
| --- | --- | --- | --- | --- |
| hunger | `energy` 0 to 100, exists | 50 to 60 | -1 | unchanged |
| rest (stage 3) | 0 to 100, 100 = rested | 100 | moving -1; resting +3; eating, gathering, reproducing 0 | rest rule below |
| company (stage 7 only) | 0 to 100 | 70 | another agent within 2 tiles: +5; else -1 | later |

Stage 1 adds only `rest`; `company` is added in the stage that uses it, so no
field sits unused.

### Traits (0 to 100, 50 = neutral, fixed for life)

| Trait | Plain meaning | Effect, stage 4 (all use the neutral-at-50 rule) | Only needs |
| --- | --- | --- | --- |
| industriousness | how long it keeps working before it needs rest | rest when `rest < 30 - ((industriousness - 50) * 30) // 100`, i.e. from 45 (lazy, 0) to 15 (tireless, 100) | rest, energy, pack |
| curiosity | how restless its wandering is | chance to turn while wandering = `15 + ((curiosity - 50) * 20) // 100` percent, i.e. 5 to 25 | heading (no map memory) |
| boldness | how little energy it needs before having a child | `repro_min_energy = 90 - ((boldness - 50) * 18) // 100`, i.e. 99 (timid, 0) to 81 (bold, 100) | energy |
| sociability | wish to be near others | **no effect until stage 7**; stored from stage 1 | other agents |

Rounding examples (so you can check by hand): industriousness 30 gives
`30 - (-20*30)//100 = 30 - (-6) = 36`. Curiosity 10 gives `15 + (-40*20)//100
= 15 + (-8) = 7`. Boldness 75 gives `90 - (25*18)//100 = 90 - 4 = 86`
(450 // 100 = 4, rounded down).

**Why curiosity and boldness no longer need memory** (review finding 3):
curiosity is restlessness of heading, boldness is a reproduction threshold.
Both use only energy and heading.

**Warning, FACT from `STARVATION.md`:** boldness changes births, and births
are the lever on starvation. Expect it to move the starved share. That is a
feature (a real trade-off: bold agents have more children and arrive weaker),
but the stage 4 check watches it.

Inheritance: child trait = `clamp(parent + rng_traits.between(-m, m), 0, 100)`
with `m = 10` (your question 3). Founders of a world get
`rng_traits.between(35, 65)` (narrow, so personalities start similar) or all
50 (question 3).

## 4. Rest and company: incentives, alternatives, predicted effect on deaths

Today only energy matters, at 1 per tick (`sim.py:41`). A need nobody can
profit from is just a number, and a trait with no effect on survival or
children cannot be selected (review finding 2).

### Rest (stage 3)

Rule: a voluntary `rest` action is allowed only if `energy > eat_below`
(never while hungry) and either `rest < rest_below` (30 at neutral) or the
agent rested last tick and `rest < 70` (so it does not flip between rest and
move). It is checked after eat, reproduce and gather, so it only replaces
walking (explore and stock-up). Resting is deliberately **not free**.

| Option | What it does | Effect on deaths | Label |
| --- | --- | --- | --- |
| **A. Half-price living while resting (proposed)** | on even ages the tick's 1 energy is refunded, so resting costs 1 per 2 ticks | explore is only 5.9% of all decisions (FACT), so saving half of that is about 3% of all energy. Population about +3%, starved share within plus or minus 2 points | PREDICTION |
| B. Rested agents see farther | vision +1 while `rest >= 80` | searching is 46% of decisions (FACT), so this could cut search time a lot: population up noticeably, starved share down. Also about 25% slower runs (box 11 x 11 instead of 9 x 9) | PREDICTION (size unknown); GUESS on the speed figure |
| C. Resting speeds up the child cooldown | cooldown -2 per resting tick | more births; `repro_cooldown=100` gave 78.4% starved against 67.7% (FACT), so expect starved share up | PREDICTION |
| D. Penalty only: tired agents skip every second move | no incentive, only a cost | tired agents die more; no reason to choose rest except to avoid the penalty | PREDICTION |

Proposed: A, because it is the smallest push on the food balance. Free rest
is excluded (an agent that rests forever never starves; review "missed" list).

### Company (stage 7, a gate, not a plan)

Company has no reason to exist today: agents cannot see each other and already
share tiles. Build it only if stage 5 shows traits matter and you want
sociability to do something.

| Option | What it does | Effect on deaths | Label |
| --- | --- | --- | --- |
| **A. Shared sight (proposed)** | an agent with nothing in view may follow the food target of an agent within 2 tiles | less searching, so more agents; clustering has a cost (they crowd the same food), a real trade-off for sociability to evolve against | PREDICTION; crowding cost is GUESS (not measured) |
| B. Food sharing | a neighbour with pack of 2 or more gives 1 food to an agent at energy 20 or less with an empty pack | directly removes some starvation (6.2% die one tick after gathering, FACT; sharing would not help those, but would help others); donors pay | PREDICTION |
| C. Shared lookout | vision +1 while another agent is within 2 tiles | like rest option B, plus favours clusters | PREDICTION |

Gate for stage 7: stages 3 to 5 done and you answer "yes, add company".

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
(`make_agent` adds `needs: {"rest": 100}` and four traits at 50;
`SAVE_VERSION = 3`), `genesis/save.py` (`_migrate_2_to_3`, defaults,
`migration_log`), `genesis/sim.py` (die events also carry traits and needs),
`tests/test_save_load.py` (v2 fixture migrates; a v3 save round-trips).
Check: unit tests, then `make_baseline.py --check`.
Must stay unchanged: event digest and behaviour digest for all 3 baseline
seeds, exactly; the save-fixture digest. **Expected change:** the full-world
`fingerprint` (new fields); `tests/test_baseline.py` then compares digests,
counters and `fingerprint` is kept as a second recorded value in the
baseline, replaced only in this commit. Proves: old saves migrate, nothing
behaves differently.

**Stage 2: trait creation and inheritance, still no effect.** Files:
`genesis/traits.py` (new: create, inherit, own dice stream), `world.py`,
`sim.py` (child gets inherited traits), `experiments/trait_report.py` (mean
and spread per generation). Check: unit tests and digests exactly equal to
stage 1, even though traits now vary. Proves: inheritance works and the main
dice are untouched. **Also gives the control:** with traits having no effect,
the report shows how far chance alone moves the averages (neutral drift).

**Stage 3: rest need and rest action (option A).** Files: new
`genesis/needs.py`, `agents.py` (one new rule after gather), `sim.py` (apply
rest, half-price refund), `whylog.py`, tests. Check: unit tests, then 5 seeds
x 3,000 ticks against the bands below. Changes behaviour on purpose; the
reference is re-recorded in `baseline.json` under `stage3`, in its own
commit. Proves: a need with a cost and a reward changes behaviour without
breaking the balance.
**Bands (all 5 seeds, vs the FACT baseline: mean pop 89.1, spread 88.6 to
89.6; starved share 67.7, spread 67.0 to 69.1; births 918; age at death 295):**
mean population after tick 500 within 80 to 98, starved share within 62 to 73,
births within 830 to 1,010, average age at death within 265 to 325, no run
dies out. Outside a band: stop and report, do not tune silently.

**Stage 4: trait effects as thresholds.** Files: `agents.py` (the three
formulas above, no new dice: curiosity uses `rng.below(100) < p` in place of
`rng.chance(0.15)`), `whylog.py`, tests. Check, in order: (1) with all traits
forced to 50 the event digest equals stage 3 exactly; (2) opposite-trait test
in a tiny world (curiosity 90 turns more often than 10; industriousness 10
rests earlier than 90; boldness 90 reproduces at a lower energy than 10);
(3) 5 seeds against the stage 3 bands, widened by 5 points for starved share.
Proves: personality alone makes same-situation choices differ, and every
difference is explained by a trait in the "why".

**Stage 5: emergence report.** Files: `experiments/emergence_report.py`
(measures in section 7, computed over 5 seeds, neutral control vs real).
Check: run it; the report is the check. Proves (or disproves) that traits
produce selection beyond chance. If it disproves, that is a result, not a
failure.

**Stage 6 (optional gate): scoring for a few actions.** Only if stage 5 shows
thresholds are too rigid. Eat stays a fixed rule before scoring with
`eat_below=80` (review finding 4). Scores are integers scaled by 100
(`150` means 1.50), products divided with `//`. Check: with all traits 50 and
no noise, event digest equals the stage 4 reference. Your questions 4 and 7
only matter here.

**Stage 7 (gate): company** (section 4), with a neighbour grid so cost stays
near one pass over agents per tick. Check: the bands again, plus a
clustering measure.

**Stage 8: tidy.** `summary.py` (action mix, trait averages), README, STATUS,
VISION.

## 6. The seven questions for you

I do not choose for you. "Recommend" is my suggestion; the default is what I
use if you leave a row empty (and it is always the more reversible option).

**Q1. Should low rest or low company ever cost energy or lifespan?**
- A. No, they only shape choices. Consequence: safest for the balance;
  traits can still be selected through the rest incentive. Reversible: yes.
- B. Yes, very low rest slows the agent (D above). Consequence: adds a
  punishment and a new way to die; harder to compare with the baseline.
  Reversible: yes, but baselines must be re-recorded.
- Recommend A. Default A.

**Q2. Which traits?**
- A. Four as proposed. B. Three that act now (curiosity, boldness,
  industriousness) and sociability stored but inactive until company.
  C. Two (boldness, curiosity) for the cleanest experiment.
- Consequence: fewer traits are easier to explain and to measure; an unused
  stored trait only wastes a field. Reversible: adding a trait later is a
  save migration; removing one is easy.
- Recommend B (it is what section 3 already assumes). Default B.

**Q3. Inheritance and mutation.**
- A. Child = parent +/- up to 10, founders all 50 (clean start, slow to
  diversify). B. Same mutation, founders random 35 to 65 (diversity from
  tick 0; harder to see what selection did). C. Larger mutation (+/- 20)
  (fast change, noisy).
- Consequence: with only about 16 generations in 3,000 ticks (FACT), small
  mutation may show little change; the neutral control tells us.
  Reversible: yes, a setting.
- Recommend B with +/- 10. Default A (founders 50) if you do not choose.

**Q4. Randomness in choices (only if stage 6 is built).**
- A. None: differences come from traits only (explainable, stable).
  B. Small integer noise (up to 10% of the top score) so equal agents can
  differ. C. A chance of a random action ("mistake").
- Consequence: noise adds draws, which change the dice order and make "why"
  harder to read; it also hides what traits do. Reversible: yes.
- Recommend A for now (the existing `wander` dice already give variety).
  Default A.

**Q5. May agents share a tile?**
- A. Yes, as now. B. One agent per tile (a blocked move waits or turns).
- Consequence: B changes movement for everyone, probably raises starvation
  where food is scarce (crowding), and costs speed (needs an occupancy map);
  not measured. Reversible: A is easy to return to; B changes baselines.
- Recommend A until company exists. Default A.

**Q6. The old rule order: switch or baseline? (updated from the reviewer's
point)**
- A. No switch. The old behaviour is kept only as frozen reference files and
  tests (`baseline.json`, digests), which already exist. Consequence: one
  decision system to maintain; we can still prove "nothing broke".
  B. Keep a temporary `--set decision=rules` until stage 5, then remove.
  Consequence: two systems for several stages; needs tests for both.
  C. A permanent switch. Consequence: permanent double maintenance.
- Recommend A. Default A. Reversible: yes (a switch could be added later).

**Q7. Where does a scoring table live (only if stage 6 is built)?**
- A. In code first, moved to settings once it settles. B. In `config.py` from
  the start, editable with `--set`. C. In its own JSON file.
- Consequence: B and C let you tune without code, but numbers in config are
  saved inside every world, so old saves keep old tables (good for
  reproducibility, noisy for experiments). Reversible: yes.
- Recommend A. Default A.

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

Fill one row each. Leave empty to accept the default shown in section 6.

| Question | Your answer | Notes |
| --- | --- | --- |
| Q1 low needs penalty | | |
| Q2 trait set | | |
| Q3 inheritance and mutation | | |
| Q4 randomness | | |
| Q5 tile sharing | | |
| Q6 rule-order switch | | |
| Q7 scoring table location | | |
