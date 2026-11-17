# Milestone 2 proposal: needs, personality, scored decisions

Status: **proposal only. Nothing here is built.** Written 2026-11-17 against
the code as of that day (save format 2, 64 tests). Plain-language words in
**bold** are explained once where they first appear.

## 1. Goal in one paragraph

Today an agent has one need (energy) and decides by a fixed list of rules:
the first rule that fits wins, so two agents in the same situation always
act the same. Milestone 2 gives each agent (a) several needs that change over
time, (b) a personality that makes the same situation lead to different
choices, and (c) a decision step that **scores** every possible action and
picks one, writing down why one beat the others. No LLM. Nothing new needs
to be installed. This is the base that relationships, memory and culture can
later grow from (see `VISION.md`).

## 2. What an agent gets

All numbers are whole numbers 0 to 100 (not decimals), so saves and replays
are exactly the same on every machine.

**Needs** (they drift every tick, and acting on a need lowers it):

| Need | Meaning | Changes over time | Satisfied by |
| --- | --- | --- | --- |
| hunger | already exists as `energy`; it stays as is | -1 per tick | eating |
| rest | tiredness; 100 = fully rested | falls a little each tick of walking, falls less while still | the `rest` action (needs no food) |
| company | wish to be near others; 100 = content | falls each tick, faster when alone | being within a few tiles of other agents ("seek company" action, or just meeting them) |

Hunger keeps its meaning (energy at 0 = death). Whether low rest or low
company ever hurts survival is a decision for you (section 11). Safe default:
low rest slows nothing and low company has no penalty at first; they only
shape choices. That keeps the world's death rate unchanged while we learn
how the choices behave.

**Traits** (fixed for life, set at birth, 0 to 100, 50 = average):

| Trait | High value leans toward | Low value leans toward |
| --- | --- | --- |
| sociability | seeking and staying near others | staying alone |
| boldness | walking far, going to risky places, reproducing earlier | staying near known food, caution |
| curiosity | exploring unseen ground, trying new tiles | going back to known food |
| industriousness | gathering and stocking food beyond the immediate need | resting, doing the minimum |

Start-of-world agents get traits from the seeded dice. A child gets its
parent's traits plus a small random nudge (step 5 of the build order), so
personalities can run in families and slowly drift (this is the first place
anything resembling inheritance appears).

## 3. The decision system

`decide(world, agent, rng)` in `genesis/agents.py` keeps its signature and its
return shape (`action`, `need`, `options`, `why`), so `sim.py` and the page
keep working.

Candidate actions: `eat`, `gather`, `reproduce`, `rest`, `seek_food`
(walk to reachable food, the logic from step 4), `explore`, `seek_company`.
Each action gets a **score** (a whole number). Roughly:

    score(action) = urgency(need it serves)       how badly the agent needs it now
                  * trait_weight(action)          how much this personality likes it
                  * outcome(action)               what the agent expects to gain
                  - cost(action)                  walking distance, risk
                  + small_noise                   tiny, from the world dice

- **urgency** rises steeply as a need approaches empty. Hunger below 20
  must always win (survival floor, so personality never starves an agent
  that has food in its pack).
- **trait_weight** is a simple table: for example `explore` is multiplied
  by `0.5 + curiosity/100`, `seek_company` by `0.5 + sociability/100`.
- **outcome** uses only what the agent can see now (vision box, carried
  food, nearby agents). No planning, no memory yet.
- **noise** is a small number from `Rng` (the project's seeded dice), so
  two agents with identical needs and traits can still differ a little, but
  the same seed still gives the same world.
- The highest score wins; a tie goes to the action earlier in a fixed list.

Important: the old rule order becomes a special case (very high urgency for
eating and a fixed floor), which lets us test that nothing broke by setting
all traits to 50 and noise to 0 and comparing to Milestone 1 behaviour.

## 4. "Why" records

Each option records `action`, `score`, and its parts, for example:

    explore      score 41 = urgency 30 x curiosity 1.4 x outcome 1.0 - cost 1 + noise 2
    seek_company score 38 = ...

and the decision stores the winner, the runner-up and the margin, so the
text can say: "explored (41) instead of seeking company (38): curious
(78) but only a little lonely (company 61)". The record shape in
`genesis/history.py` gains an optional score list; old records still read.
`why.py`, the page's Agent panel and `format_decision` show the scores and
the margin. A test checks that the printed winner is the real maximum.

## 5. File and module changes

| File | Change |
| --- | --- |
| `genesis/config.py` | decay rates, trait defaults, noise size, survival floor, company radius |
| `genesis/traits.py` (new) | create traits from dice, inherit with a nudge, names and descriptions |
| `genesis/needs.py` (new) | per-tick change of rest and company; effect of actions on needs |
| `genesis/scoring.py` (new) | urgency, trait weights, outcome, the scoring table |
| `genesis/agents.py` | `decide()` builds candidates and calls scoring; `_walk_to_food` stays |
| `genesis/world.py` | `make_agent` adds `needs` and `traits`; world creation draws traits |
| `genesis/sim.py` | apply new actions (`rest`, `seek_company`, `explore`); decay needs |
| `genesis/history.py`, `whylog.py` | score list in the record and in the text |
| `genesis/save.py` | defaults for old saves (below) |
| `genesis/overrides.py` | rules for the new settings |
| `genesis/summary.py` | action mix, average trait values of the living (only after they exist) |
| `server.py`, `web/` | show needs and traits in the Agent panel; score bars |
| `tests/` | new `test_needs.py`, `test_traits.py`, `test_decisions.py` |

## 6. Data and save-format changes

Agent record gains `"needs": {"rest": 80, "company": 70}` and
`"traits": {"sociability": 50, "boldness": 50, "curiosity": 50,
"industriousness": 50}`. Save format stays 2 because loading already fills
missing agent fields with defaults (`_repair`): old agents get all needs at
70 and all traits at 50, logged in `migration_log`. A world that is saved,
loaded and continued keeps working. If we later change the meaning of an
existing field, that is when version 3 and a migration function are needed.
Old history records without scores stay valid.

## 7. Determinism

- All dice come from the one `Rng`, always drawn in the same order: agents in
  id order, and inside `decide` the noise values drawn once per candidate in
  the fixed candidate order. Adding or removing a draw changes every future
  fingerprint; that is expected, but it is never random between runs.
- Whole numbers only (no decimals) and integer division, so results do not
  depend on the machine.
- Dictionaries are read in a fixed order (sorted or fixed lists), never in
  "whatever order a set gives".
- Tests compare two runs with each other, never against a stored code.

## 8. Test plan

1. Needs drift: after N ticks of standing still, rest and company have the
   documented values; acting resets them.
2. Traits: range 0-100, inherited with nudge within bounds, same seed gives
   the same traits.
3. Decisions with hand-made tiny worlds (same helper as `test_movement.py`):
   - identical needs, opposite traits (curiosity 90 vs 10, sociability 90 vs
     10) choose differently often enough, over many ticks;
   - survival floor: a starving agent with food in its pack eats whatever its
     traits are;
   - the recorded winner has the highest score; margin is right;
   - noise 0 and all traits 50 gives Milestone 1 behaviour in the hungry cases.
4. Determinism: same seed twice gives equal worlds; save/load/continue equals
   an uninterrupted run (existing tests must stay green).
5. Old saves: a save without needs/traits loads and runs.
6. Measure, do not guess: population and starvation share on 5 seeds before
   vs after, with the sweep script; ticks per second before vs after.

## 9. Performance risks

- Scoring 7 candidates per agent per tick, on top of the reachability search
  (which already slowed 2,000 ticks from about 1.1 s to 1.9 s, measured in step 4). Budget: no more than 2x slower
  (about 400 ticks/s with ~100 agents).
- "Company" needs the nearby agents. A naive scan is agents x agents (10,000
  checks at 100 agents, 1,000,000 at 1,000). Plan: one pass per tick that
  buckets agents into a coarse grid, then each agent looks only at its own and
  neighbouring cells.
- History records get larger (scores). Save size: not measured, expect noticeably larger (guess, to be measured in step 4 of the build order). Lower
  `history_keep` or add a string table if it matters.
- The page sends the selected agent's trail every poll; scores add a little.

## 10. Build order (each step small, tested, committed)

1. Add `needs` and `traits` fields with defaults and save repair; show them
   in the Agent panel. Behaviour unchanged. Check: all tests, old save loads.
2. Needs drift per tick and `rest` action (no survival effect). Check: new
   needs tests; sweep shows survival unchanged.
3. Scoring module that reproduces the old rule order exactly (traits 50, no
   noise). Check: same decisions as before on seed 42 for 500 ticks.
4. Record scores in "why" (history, `why.py`, page).
5. Traits: creation, inheritance with nudge, effect on `explore` and
   `gather` weights. Check: opposite-trait tests.
6. Company need and the neighbour grid; `seek_company` action.
7. Noise from the dice; tune urgency curves with the sweep script.
8. Update `summary.py` (action mix, trait averages), README, STATUS, VISION.

## 11. Decisions I need from you

Each has a safe default that I will use if you do not answer.

1. Should low rest or low company ever cost energy or lifespan?
   Default: **no** (they only shape choices) until step 7 data is in.
2. Are four traits right, or should I add/remove any? Default: these four.
3. How much inheritance and mutation? Default: child trait = parent +/- up
   to 10, kept within 0-100.
4. How much randomness in choices? Default: noise up to 10% of the highest
   score.
5. Should agents be able to share a tile (as now), or should the new
   `seek_company` make them stand next to each other, one per tile?
   Default: still allowed to share.
6. Is a rule-order mode worth keeping as a switch (`--set decision=rules`)
   for comparing with Milestone 1? Default: yes, kept until Milestone 3.
7. Keep the whole scoring table inside code, or in a settings file you can
   edit? Default: in code first, in config once it settles.
