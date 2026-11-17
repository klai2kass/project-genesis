# Review of the ChatGPT review of `docs/MILESTONE2.md`

Written 2026-11-17. Each point was checked against the real code and against
measurements. **FACT** = I ran it or read it (with file and line).
**PREDICTION** and **GUESS** are labelled. Nothing of Milestone 2 is built.
The reviewer saw an incomplete brief (no code, no data), so it is right more
often about design and weaker on specifics; both are noted below.

Plain words: a **fingerprint** is a short code that is equal only when two
worlds are exactly equal. A **digest** (new, see finding 6) is the same idea
but looks only at behaviour. A **stage** is one small, tested build step.

## Scoreboard

| # | Reviewer's point | Verdict |
| --- | --- | --- |
| 1 | Investigate starvation before adding needs | **Agree** (now done) |
| 2 | Rest and company need real consequences; positive incentives | **Partly agree** |
| 3 | Curiosity and boldness are undefined without memory | **Agree** |
| 4 | Scoring contradicts the old eating rule | **Agree** |
| 5 | Evolution needs measurable objectives | **Agree** (with a gap: nothing is tracked yet) |
| 6 | Do not keep two decision systems; keep a testable baseline | **Agree** (and the baseline needed a new tool) |
| 7 | Save format version 3 with a migration | **Partly agree** |

## 1. Investigate starvation first: AGREE

- **FACT:** the cause was unknown and is now measured: `docs/STARVATION.md`.
  Short version: food sets the head-count (91 agents against a ceiling of
  98); nothing limits births when the map is full; so the overflow starves.
  Slowing births (`repro_cooldown=400`) cut the starved share from 67.7% to
  45.5% with about the same population.
- **What it changes:** the reviewer feared we could not tell old problems from
  new ones. Now we can: every later stage is compared against the numbers in
  `docs/STARVATION.md` and `experiments/baseline/baseline.json`.
- **New consequence (not in the review):** anything that changes how many
  children are born (rest, company, scoring that delays reproduction) will
  move the starved share a lot, even if it never touches food. The plan
  must watch births, not only deaths.

## 2. Needs need consequences; use positive incentives: PARTLY AGREE

- **Agree (FACT):** with no effect on survival or reproduction, a trait
  cannot be selected for or against. Traits would only drift by chance. The
  current rules give energy exactly one use: 1 per tick (`sim.py:41`).
  Nothing else costs or saves energy.
- **Disagree in part:** "just add a positive incentive" is not neutral. This
  world is balanced on a knife edge: the population sits at 93% of the food
  ceiling. Any energy saving (for example cheaper resting) raises the
  ceiling, so the headcount rises and mortality shifts. (PREDICTION, based on
  the food_energy sweep: 15 -> 68 agents, 20 -> 89, 30 -> 119.)
- **Missed by the reviewer:** a free rest is an exploit. If resting costs 0
  energy, an agent that rests all day never starves until old age. Rest must
  cost something, for example half price (`age` even/odd rule), and must lose
  something real: while it rests it is not searching, and 46% of all
  decisions today are searching.
- **Missed:** company has no natural benefit here. Agents already crowd
  food (GUESS) and cannot see each other (no code reads other agents in
  `decide()`). A company need with no use would just be a number.
- **What it changes:** stage for rest has a measured pass/fail band for
  population and starved share (see `MILESTONE2_V2.md`). Company is postponed
  until there is a reason for agents to interact, as the reviewer suggested.

## 3. Curiosity and boldness are undefined without memory: AGREE

- **FACT:** an agent has no memory of places. Its fields are `id, x, y,
  energy, age, max_age, food, heading, cooldown, parent, generation, target,
  last_action, last_why` (checked on a live agent). `target` is only the one
  food tile it is walking to (`world.py:45`). `agents.py` never reads the
  history (grep for `history|visited|memory` in `genesis/agents.py`: no
  match). The history log is for humans, not for decisions.
- **Reviewer's preferred fix works:** redefine the traits with what the
  agent can see now (the 9 x 9 box: food counts, water, other agents; its own
  pack and energy). `docs/MILESTONE2_V2.md` does that, with whole numbers.
- **What it changes:** the proposal's "known food" and "unseen ground"
  wording is dropped. No memory in Milestone 2.

## 4. Scoring contradicts the old eating rule: AGREE

- **FACT:** old rule: eat if `pack > 0 and energy <= 80` and it is checked
  first (`agents.py:85` and `:131`). The proposal's floor is energy below 20
  (`MILESTONE2.md:67-69`), so an agent at energy 40 with food could explore
  instead of eating. The proposal contradicts itself: lines 79-81 say the old
  order is a special case, yet the floor differs from it.
- **FACT, why it matters:** food in the pack is eaten as soon as energy hits
  80, so no starving agent ever carries food, except the 6.2% who gather
  with 1 energy left (see `STARVATION.md`). Letting scoring delay eating
  would be a new way to starve.
- **What it changes:** the first scoring stage keeps `eat` as a fixed rule
  before scoring, with the same `eat_below=80`. Scoring only chooses between
  the actions that come after it (gather, reproduce, move kinds, rest).
  Changing the eating rule needs its own stage and its own data.

## 5. Evolution needs measurable objectives: AGREE, but nothing is tracked yet

What can be computed today from data the program already records, and what
cannot (traits do not exist yet, so every trait measure is "not tracked"):

| Measure | Today |
| --- | --- |
| Generations | **Tracked**: `generation` per agent (FACT: depth 16 at tick 3000, seed 42) |
| Survival and reproduction per agent | **Derivable** from die events (`age`, `cause`) and reproduce events; `experiments/starvation_study.py` already does it |
| Trait average and spread over time | **Not tracked** (needs traits; cheap once they exist: one pass over living agents every N ticks) |
| Trait diversity | **Not tracked** (same) |
| Survival by trait range | **Not tracked**: the die event must carry the traits (small addition) |
| Different seeds, different outcomes | **Runnable** with the existing multi-seed scripts once traits exist |

- **Missed by the reviewer (important):** the reviewer's worry "all survivors
  end with industriousness 100 and curiosity 0" cannot be judged without a
  control. Plan: run the same world with traits that have NO effect
  (neutral). Chance alone moves averages; only a trait effect that beats the
  neutral spread counts as selection. With 16 generations in 3,000 ticks the
  signal will be weak; the plan says so.

## 6. Do not maintain two decision systems: AGREE, and the baseline needed new tooling

- **Agree:** a permanent `decision=rules` switch (`MILESTONE2.md:199`) means
  two systems to test forever. Dropped. Question 6 is rewritten.
- **FACT, found while checking:** the existing `fingerprint()` hashes the
  whole world (`save.py:137-140`), so adding any new agent field changes it
  even when behaviour is identical. A "fingerprint unchanged" test therefore
  cannot guard the "data only" stage.
- **FACT, second trap:** world creation draws dice for every agent
  (`world.py:72-79`). Drawing traits there shifts the dice and changes every
  later event. So the data-only stage must give constant traits, or draw
  from a separate stream (see `MILESTONE2_V2.md`, stage 1).
- **Done now (small, tested, in scope):** `genesis/digest.py` (behaviour
  digest and event digest, ignore new fields and wording),
  `experiments/baseline/make_baseline.py` and `baseline.json` (frozen results
  of the current rules: 3 seeds x 500 ticks exact digests; 5 seeds x 3000
  ticks summaries), `tests/fixtures/save_v2_seed42_t300.json` (a real
  version-2 save) and `tests/test_baseline.py` (4 tests). Verified: a
  version-2 save loaded and run to tick 500 gives the same behaviour digest as
  an uninterrupted seed-42 run. Run `python3 experiments/baseline/make_baseline.py --check`
  to recompute everything (about 1 minute).
- **What it changes:** instead of a switch, each stage proves itself against
  `baseline.json`: exact match if it promises "unchanged", measured bands if
  it changes behaviour on purpose.

## 7. Save version 3 with an explicit migration: PARTLY AGREE

- **FACT, how it works today:** `_repair()` runs on every load and fills any
  missing agent field from `AGENT_DEFAULTS` (`save.py:32-35`, `:68-73`) and
  logs it. Version 1 -> 2 was exactly this: a bump plus an empty
  `_migrate_1_to_2` (`save.py:86-90`). `SAVE_VERSION = 2` is at `world.py:13`.
  A newer-than-known version is refused (`save.py:101-104`).
- **Where the reviewer is right:** if needs and traits are added and the
  version stays 2, an older copy of the program would load a Milestone 2
  save as if it were fine and silently ignore the new fields. A bump makes
  the old program refuse it. Also `MILESTONE2.md:121` ("stays 2") is
  inconsistent with its own rule at `:122-123`.
- **Where it is overstated:** "schema change even if old saves can be
  repaired" is true, but `_repair` must stay (it also covers hand-edited and
  partial saves). Version 3 adds the migration function, it does not replace
  repair.
- **What it changes:** the stage that first adds persistent fields bumps
  `SAVE_VERSION` to 3 and adds `_migrate_2_to_3`: add `needs` and `traits` to
  every agent at neutral values, add the new config keys, log it in
  `migration_log`, bump the version. Tests use the stored v2 fixture above.
  Both repair and migration stay.

## What the reviewer missed (found while checking)

1. **Dice order** (finding 6): new random draws shift all later behaviour.
2. **The fingerprint is too strict for "data only" stages** (finding 6).
3. **Births, not food, are the lever on starvation** (finding 1).
4. **Newborn clock:** a child starts with 50 energy and dies at age 50 if it
   finds nothing (430 deaths, 14.5% of starvation). A rest or scoring rule
   that slows a child's first steps hurts exactly the most fragile group.
5. **Gather and eat are two ticks:** 6.2% of starvation deaths happen one tick
   after picking food up. Scoring must not make this worse; fixing it is
   optional and would change behaviour (Decision for you).
6. **Speed:** a profile of 1,000 ticks (seed 42, `cProfile`) shows 40% of the
   time in `_steps_to`, 17% in `_food_in_box`, about 2% in the dice. So
   scoring costs are likely small next to the existing food search, but
   unmeasured until built (PREDICTION). Seven noise draws per agent per tick
   would be about 650 draws per tick (about 10x today's 70); cheap in time
   but each one changes the dice order.
7. **`why.py --load` does not use stored history** (it replays ticks). Not
   related to Milestone 2, but the page and `why.py` will both need to show
   scores; see "next tasks" in STATUS.
8. **Company has no use yet** (finding 2).
