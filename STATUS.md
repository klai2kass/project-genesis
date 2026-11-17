# Project Genesis: status

Last checked: 2026-11-17, by running the commands in this file (not from memory).

**Milestones 1 and 2 are done. Milestone 3 steps 1 (a home) and 2
(encounter memory) are built, tested and measured** (`docs/MILESTONE3.md`).
Every agent stays near its birthplace and remembers up to 10 agents it met,
how often, when and where. Memory changes no behaviour yet. **Proposed next:
step 3, the first use of memory: share food with a starving agent you know**
(section 5); not started, it waits for your go. GitHub (`origin/main`) has
everything up to `e3e07c3`; this session's commits are local only.

Plain words: a **tick** is one step of time. A **seed** is the number a world
is built from (same seed = same world). A **fingerprint** is a short code that
is equal only when two worlds are exactly equal. **Headless** = no window.

## 1. What works today (checked this session)

- [x] World, food, agents that search (around water), gather, eat, rest,
      reproduce and die. Same seed = same world.
- [x] Rest need and traits (curiosity, industriousness), inherited +/-5.
- [x] **Homes**: `home` per agent (birth tile), `home_radius` 6 (0 = off).
- [x] **Encounter memory**: `memory` per agent, `memory_keep` 10 (0 = off);
      shown in the agent panel. A record only.
- [x] Every decision has a "why"; recent decisions are kept in saves.
- [x] Saves version 5; versions 1 to 4 load and keep their old rules.
- [x] Milestone 1, Milestone 2 and homes behaviour frozen and reproduced
      exactly: `tests/test_baseline.py`, `tests/test_home.py`,
      `tests/test_memory.py`, `experiments/baseline/make_baseline.py --check`.
- [x] Browser page, including the clicked agent's home and whom it knows
      (checked this session at http://127.0.0.1:8766, see 3).
- [x] Measurement scripts in `experiments/`, results in `experiments/results/`.
- [ ] `why.py --load` reads the stored history (it still replays instead).
- [ ] `--summary` does not report action mix or trait averages.

## 2. Tests (run this session)

`python3 -m unittest discover -s tests` -> `Ran 132 tests`, `OK` (about 55 s
on a quiet Mac). By file: baseline 5, controls 11, determinism 7, history 8,
home 12, memory 11, movement 7, overrides 11, rest 12, rest_design 14,
save_load 10, summary 5, trait_streams 5, traits 8, why_log 6.
Changed tests (on purpose): save-version checks now use `SAVE_VERSION`
instead of a fixed number; the curiosity turning test in `test_rest.py`
runs with `home_radius=0`.
`make_baseline.py --check` -> ALL SAME (Milestone 1 unchanged).
Reference run: `python3 run_headless.py --seed 42 --ticks 500 --every 0` ->
100 alive (homes on). Frozen references: `experiments/baseline/baseline.json`
(Milestone 1), `milestone2.json` (before homes), `milestone3_home.json`
(homes, before memory).

## 3. Browser check (this session)

Server started from the shell on port 8766 (Claude's sandbox blocks ports,
so it ran outside the sandbox), page opened in the app's browser.
- Milestone 2 check: map, Play/Pause, Step, 20x, stats (resting now, average
  traits), agent panel (rest bar, traits, options, earlier decisions), Save
  then Load (back to tick 392, paused, "Loaded ..." message). No errors.
- Homes check (fresh tab): clicking agent #45 shows a gold square at its
  home (55, 6), a dashed box for its 6-tile area, and the line "Home (55, 6),
  where it was born · 6 tiles away · wanders within 6 tiles of it"; its
  earlier decisions include "... I am 7 tiles from home (55, 6) and stay
  within 6, so heading home". Legend has the new entry. **No console errors.**
- Memory check (fresh tab): clicking an agent shows "Knows 10 agents
  (remembers up to 10). Met most:" and a list such as "#231 · met 3 times,
  last at tick 664 near (26, 27)", with "has died" where right. **No console
  errors.**
Small things noticed (not fixed): the population graph starts empty after a
load (not stored in saves); the rest bar shows the value after this tick's
rest while the decision text shows the value at decision time. The test save
`saves/claude_browsercheck.json` is still in `saves/` (ignored by git).

## 4. Measured results

**Encounter memory** (`docs/MILESTONE3.md`; `experiments/memory_probe.py`,
5 seeds x 3,000 ticks): an adult has met about 31 agents and remembers 10;
its most-met agent about 11 times; it keeps 76% of the agents it met 5+
times (the first cap rule kept only 50%, so it was replaced); 12% of what
it remembers is family. Behaviour identical with memory on or off. Cost:
about 6-13% slower depending on the timing, saves about 2.5% bigger.

**Could memory be used for something? (`experiments/sharing_opportunity.py`)**
One starvation death in three (33.7%) happened to an agent that, in its last
20 ticks, stood next to a well-fed agent carrying food; in one in five
(19.4%) that agent had met it before; family only 4.6%.

**Homes** (`docs/MILESTONE3.md`; `experiments/encounter_probe.py`, 5 seeds x
3,000 ticks; `stage_compare.py`):

| | homes off (Milestone 2) | homes, radius 6 (default) | radius 3 |
| --- | --- | --- | --- |
| meetings that are family | 6.0% | 13.0% | 20.0% |
| pairs that meet 5+ times | 8.5% | 21.1% | 26.6% |
| different agents met in a life | 38.3 | 25.0 | 19.4 |
| population after tick 500 | 93.0 | 93.1 | 93.4 |
| starved % of deaths | 66.5 | 65.4 | 66.1 |
| births | 946 | 931 | 947 |

Both success lines met (family share and 5+ meetings at least doubled), all
Milestone 2 bands hold, speed unchanged.

**Curiosity** (`docs/MILESTONE2_REPORT.md`, `docs/MILESTONE3.md`): it always
changes how agents walk. Without homes, high-curiosity families out-bred low
ones in 34 of 40 mixed worlds. **With homes that advantage mostly
disappears** (25 of 40, within luck), because homes keep every agent near
its patch, which was the zigzaggers' edge. In normal runs no trait is
selected beyond chance.

## 5. Next step: Milestone 3, step 3, share food with someone you know (recommended)

**What:** the first behaviour that uses memory. A well-fed agent (energy
above 80) carrying food, standing within 1 tile of a **starving** agent
(energy 20 or less, empty pack) that it has **met at least twice before**,
gives it 1 food. The receiver eats it next tick by its normal eat rule.

**Why (evidence, section 4):** 33.7% of starvation deaths had a fed giver
with food right next to them in their last 20 ticks; 19.4% had one that
knew them. That is a concrete situation the memory can act on, which
nothing else in the world handles. It is also the smallest step toward the
vision's relationships and exchange: who helps whom, and does help come
back, can then be measured.

**Alternatives considered:**
- *Family-only sharing* (uses the existing `parent` field, no memory):
  rejected as the first rule, it reaches only 4.6% of starvation deaths,
  a quarter of "someone I know".
- *Seeking company* (walk toward known agents): rejected, no measured payoff
  (the Milestone 2 gate still applies).
- *Do nothing social yet; give curiosity a job first* (decision 2): smaller,
  but does not move toward relationships.

**Prediction to test (not assumed):** `docs/STARVATION.md` showed that food
supply, not food finding, sets how many agents live. So sharing will
probably NOT lower the starved share much; it changes WHO starves (fewer
young, maybe more givers). That is still the interesting part: whether
gifts flow back (reciprocity) and whether giving families do better.

**Rule (proposed):**
- New action `give`, checked after eat and reproduce, before gather, rest
  and move. Fits when: not hungry (energy above `eat_below`), food in the
  pack, and some agent within 1 tile is starving with an empty pack and has
  `share_min_meetings` (2) or more meetings in the giver's memory.
- Several fit: the one met most often (ties: lower energy, then lower id).
  No dice.
- `share_min_meetings = 0` switches it off (old saves get 0 and keep their
  behaviour).
- Why text: "gave 1 food to #31 (we have met 6 times); it is starving
  (energy 14) and I am not hungry (energy 88)". The receiver's history gets
  a line too.

**Files:** `genesis/agents.py` (the give rule and its option line),
`genesis/sim.py` (move 1 food, event for both), `genesis/config.py`,
`overrides.py`, `save.py` (version 6: `share_min_meetings = 0` for old
saves), `server.py`/`web/` (gifts given/received in the panel, "gifts" in
the stats), README, `docs/MILESTONE3.md`. Optional small addition to memory
entries: gifts given and received per known agent, so reciprocity can be
read off directly.

**Tests:** frozen reference of today's behaviour first; `share_min_meetings
= 0` reproduces it exactly; a v5 save migrates and continues identically;
gives only when not hungry, only to a starving agent within 1 tile met 2+
times; never gives the last food when itself becomes hungry (energy rule
first); picks the most-met; same seed = same world.

**Measure and success:** gifts per 1,000 ticks; starved share, population,
births and age at death inside the Milestone 2 bands; starvation deaths by
age band before and after; reciprocity (share of gifts later returned by
the receiver, against a shuffled control); whether pairs that exchanged
gifts meet more often afterwards. Success = the bands hold AND gifts
happen often enough to measure (at least a few hundred per run); the other
numbers are reported, not targets.

**Risks:** changes behaviour (all comparisons need the new frozen
reference); givers may starve later (measure); with only 2 meetings needed,
"knowing" is weak (try 5 as well).

## 6. Next 5 tasks

1. **Your go for step 3 (sharing with someone you know)**, then build it as
   in section 5. Check: `python3 -m unittest discover -s tests`, then
   `python3 experiments/sharing_opportunity.py` and `stage_compare.py`.
2. **Decide what curiosity should mean now** (decision 2). If "roaming
   distance": files `genesis/agents.py`, `genesis/traits.py`, tests; measure
   with `python3 experiments/curiosity_probe.py`.
3. **Test industriousness in mixed worlds** (copy the mixed mode of
   `curiosity_probe.py`).
4. **`why.py --load` reads stored history.** Files: `why.py`,
   `genesis/history.py`, `tests/test_history.py`.
5. **Add action mix and trait averages to `--summary`.** Files:
   `genesis/summary.py`, `tests/test_summary.py`.

## 7. Decisions for you

1. **Go for sharing with someone you know (section 5)?** It is the first
   social rule, so it is your call. Default: wait for your yes.
2. **Curiosity after homes.** It now matters little. Options: (a) leave it;
   (b) let it also set each agent's roaming distance around home (curious =
   wanders further), which matches the word; (c) remove its effect.
   Default: (a) until you choose.
3. **`home_radius` = 6** (chosen as proposed). 3 doubles family contact
   again (20%) but agents meet fewer different agents (19 in a life) and
   reunite less after long gaps. Change anytime with `--set home_radius=3`.
4. History caps (20 decisions per agent, 50 dead agents) and
   `memory_keep` 10: kept.
5. The gather-then-eat flaw (6.2% of starvation deaths happen one tick after
   picking food up): still NOT fixed, so all comparisons stay valid.

## 8. Remaining limitations

- Results are for one map size (60 x 40), one food setting, 3,000 ticks.
- Mixed-world curiosity results use extreme values (10/50/90), no mutation.
- Homes never move. How often an agent is stuck on the far side of a lake
  from its home was not measured on real maps.
- `why.py` replays from the seed; it does not read stored history.
- The population graph on the page is not saved; it restarts after Load.
- Saves are about 1.1 MB at 2,000-3,000 ticks, mostly decision history.
- Memory costs about 6-13% speed (around the 10% aimed for).
- "Family" in panel and probes = parent, child, sibling while alive only.
- One test (`test_controls.py`) sleeps 0.7 s and could rarely fail on a very
  busy Mac. Python 3.9.
- Claude's sandbox blocks opening a port; the server check needed a run
  outside the sandbox (or `sandbox.network.allowLocalBinding: true`).

## 9. Copy-paste commands

```bash
cd ~/Desktop/"Project Genesis"
```

See the world in your browser (stop with Ctrl+C):

```bash
python3 server.py
```

All automatic checks (should end with `Ran 132 tests` and `OK`, about 55 s):

```bash
python3 -m unittest discover -s tests
```

Run without the page, with a report:

```bash
python3 run_headless.py --seed 42 --ticks 2000 --every 0 --summary
```

The same world without homes (Milestone 2 behaviour):

```bash
python3 run_headless.py --seed 42 --ticks 2000 --every 0 --summary --set home_radius=0
```

Why did agent 12 do that?

```bash
python3 why.py --seed 42 --ticks 300 --agent 12
```

Experiments (each only reads the world; results go to `experiments/results/`):

```bash
python3 experiments/encounter_probe.py
```

```bash
python3 experiments/memory_probe.py
```

```bash
python3 experiments/sharing_opportunity.py
```

```bash
python3 experiments/curiosity_probe.py
```

```bash
python3 experiments/curiosity_probe.py --mixed-extra
```

```bash
python3 experiments/stage_compare.py
```

```bash
python3 experiments/trait_drift.py
```

```bash
python3 experiments/starvation_study.py
```

```bash
python3 experiments/baseline/make_baseline.py --check
```

Add `--homes-off` to the two curiosity commands to regenerate the
Milestone 2 files (`curiosity_probe.txt`, `curiosity_mixed_extra.txt`);
without it they write the `_home` files. `stage_compare.py` prints both
(its homes-on output is saved as `stage_compare_home.txt`). Times on this Mac:
memory probe about 3 min (`--old-drop-rule` for the rejected first cap
rule), sharing count about 1.5 min, encounter probe about 3 min, curiosity probe about 4 min, mixed extra about
4 min, stage compare about 4 min, trait drift about 2 min, starvation study
about 25 s, baseline check about 1 min. `trait_drift.py` and
`starvation_study.py` now run with homes on; their saved results are from
before homes.

## Design choices (one line each)

- **Python standard library only, plus a thin web page.** Node.js is not installed.
- **The world is one plain dictionary.** A save is that dictionary as JSON text.
- **Our own dice (`rng.py`).** Its memory is one number, stored in the save;
  traits use their own per-agent dice so they never disturb the main dice.
- **Rules in a fixed order, first one that fits wins.** No scoring system:
  nothing measured so far needs one.
- **Personality as thresholds and rates**, neutral at 50, whole numbers only.
- **Old saves are repaired on every load** and keep their old rules, logged.
- **The server runs the world; the page only draws.**
- **Experiments only read the world.** Prototypes live in `experiments/`,
  clearly marked, never in `genesis/` and never in saves.
- **Mixed worlds as the selection test**, because forced worlds cannot show
  competition between traits.
- **Freeze before changing.** Each step that changes behaviour first freezes
  today's digests (`experiments/baseline/milestone2.json`), and "setting
  off" must reproduce them exactly.
- **Homes: greedy step, no path search.** The simpler choice; a lake in the
  way just means normal wandering (tested).

## Known risks

- Claude's sandbox blocks opening a port, so browser checks need a run
  outside the sandbox.
- Replays (`why.py`) match only if code and settings are unchanged.
- Big populations slow the page (over about 300 agents at 20x).
- The experiment scripts recognise wandering from the "why" text; if that
  wording changes, update `move_kind` in the scripts.

## Session log

Newest first. Older entries mention section numbers of earlier versions of
this file; see `git log -p STATUS.md` for those.

### Session 2026-11-17 (part 6: Milestone 3 step 2, encounter memory)
- **Your go** ("Yes, build memory").
- **Frozen first** (`1e51430`): `experiments/baseline/milestone3_home.json`,
  `tests/fixtures/save_v4_seed42_t300.json`.
- **Built** (`bac6685`): `genesis/memory.py`, `memory` field, `memory_keep`
  (10), save version 5. Page (`1f4a169`): "Knows N agents" list.
- **Changed on evidence** (`aabe3df`): the cap first forgot whoever was met
  longest ago; `experiments/memory_probe.py` showed it kept only half of
  each agent's 5+-meeting contacts, so it now forgets the least-met.
- **Speed** (`d132043`): faster meeting search tried; cost stays about
  6-13% (the work is the updates, not the search). Reported, not hidden.
- **Tests:** new `tests/test_memory.py` (11), 132 OK; Milestone 1 ALL SAME;
  memory on/off reproduce the frozen homes world exactly.
- **Evidence for step 3:** `experiments/sharing_opportunity.py` (section 4).
- **Not done:** step 3 (waits for your go).

### Session 2026-11-17 (part 5: Milestone 3 step 1, homes, built and measured)
- **Your go** ("Yes, build home") for the plan in the previous STATUS.
- **Frozen first** (`a603e88`): `experiments/baseline/milestone2.json` and
  `tests/fixtures/save_v3_seed42_t300.json`, made with the unchanged code.
- **Built** (`8aec7e8`): `home` field, `home_radius` setting (default 6,
  0 = off), rule in `_wander`, save version 4 with migration (old saves keep
  their rules), `MILESTONE1_RULES` also sets `home_radius = 0`. Fixed in
  passing: a newborn's `last_why` now equals its history record (a test
  caught the mismatch once homes changed which agent was born last).
- **Tests:** new `tests/test_home.py` (12); 3 tests updated for version 4 /
  homes off. 121 tests OK; Milestone 1 check ALL SAME; `home_radius=0`
  reproduces the frozen Milestone 2 digests and the v3 save exactly.
- **Page** (`9a900dc`): home square, dashed area, panel line, legend,
  plainer curiosity wording. Checked in the browser, no console errors.
- **Measured:** section 4 and `docs/MILESTONE3.md`. Success lines met; side
  effect: curiosity's competitive edge mostly gone with homes.
  `curiosity_probe.py --mixed-extra --homes-off` reproduced the Milestone 2
  file exactly.
- **Not done:** encounter memory (next, section 5).

### Session 2026-11-17 (part 4: Milestone 2 finished and measured; next step chosen)
- **Verified first:** git clean on `main` at `e3e07c3`; remote `origin`
  (github.com/klai2kass/project-genesis); 109 tests OK (38.7 s).
- **Curiosity probe built and run** (`experiments/curiosity_probe.py`,
  10 seeds, forced and mixed worlds, plus 30 extra mixed seeds). Result in
  section 4. Re-run from a clean copy of the commit (`git archive`): curiosity
  probe, mixed extra and stage compare give identical numbers (speed aside).
- **Final checks:** 109 tests OK (43.4 s); `make_baseline.py --check` ALL SAME.
- **Trait drift** (`experiments/trait_drift.py`): no selection in normal runs.
- **Report written:** `docs/MILESTONE2_REPORT.md`.
- **Docs brought up to date:** README (Milestone 2 rules, settings, files,
  test count), VISION (works today / not built / next), `docs/MILESTONE2_V2.md`
  ("As built" table: stage 6 scoring and stage 7 company not built,
  `trait_report.py` replaced by `trait_drift.py`), this file rewritten.
- **Browser checked** (section 3): works, no console errors.
- **Next step chosen with evidence** (`experiments/encounter_probe.py`,
  includes a throwaway home prototype): section 5.
- **No simulation code changed.** Baseline and determinism tests untouched.
- **Not done:** industriousness in mixed worlds; measures 3, 4, 8 of
  `MILESTONE2_V2.md` section 7.

### Session 2026-11-17 (part 3: Milestone 2 implementation, committed after your review)
- **Built (approved design, no scoring, no company):**
  - `genesis/traits.py` (new): curiosity and industriousness, 0-100. Each
    agent's own dice stream `Rng(seed_to_state("<seed>|traits|<id>"))`;
    founders 40-60, children parent +/-5 per trait, clamped. Main dice untouched.
  - `genesis/needs.py` (new): rest rule (only when energy > 80; start below 30,
    continue to 70; +3 per tick), half-rate energy drain with `drain_acc`,
    tiring per move with `tire_acc` (150/100/50 hundredths at industriousness
    0/50/100).
  - `genesis/agents.py`: rest rule after gather; curiosity sets the wandering
    turn chance (`rng.below(100) < p`, 5-25%, 15% at 50 = old behaviour).
  - `genesis/sim.py`, `world.py`: new agent fields (`needs`, `resting`,
    `drain_acc`, `tire_acc`, `traits`); die events carry traits and needs.
  - `genesis/config.py`, `overrides.py`: 13 new settings, all `--set`-able.
    No existing default changed.
  - `genesis/save.py`: save format 3. Version 1/2 saves are migrated so they
    KEEP THEIR OLD RULES (rest_below=0, traits 50, newborns 50), logged.
    Try new rules on an old save with `--set rest_below=30 --set trait_mutation=5`.
  - Browser: agent panel shows a rest bar, rest state, traits and what they do
    (turn %, rest lost per move); stats show resting now and average traits;
    resting agents have a violet ring on the map (legend updated).
  - `experiments/stage_compare.py` (new), `experiments/baseline/make_baseline.py`
    (check now runs the new code with Milestone 1 rules; baseline.json is
    untouched and can only be overwritten with `--rewrite-frozen`).
- **Frozen baseline preserved (FACT):** new code with `MILESTONE1_RULES`
  reproduces `baseline.json` exactly: same counters, behaviour digest and event
  digest for seeds 42/1/2, the v2 fixture continues identically, and the
  5-seed x 3,000-tick numbers are identical (pop 89.1, births 918, starved
  67.7%, age 295). Only the whole-world fingerprint differs (new fields):
  seed 42, 500 ticks: M1 rules -> 79 alive, `54cf2357346770e0`;
  defaults -> 92 alive, `63826e5a26ffdded`.
- **Tests (run this session):** `python3 -m unittest discover -s tests` ->
  `Ran 109 tests ... OK`. New: `tests/test_rest.py` (12, real sim: tiring
  1,2/0,1 patterns, first rest after 48/142 moves, 14-tick stints ending at
  70/71, shares 1/3, 1/4, 1/7, 7 energy per stint, never rests while hungry
  incl. 2 real seeds x 1,500 ticks, curiosity turn rates), `tests/test_traits.py`
  (8), migration test in `test_save_load.py`, baseline tests updated
  (compare digests, not fingerprint; new rules must differ).
  `test_trait_streams.py` now calls the real module (same golden numbers).
- **Measured, 5 seeds x 3,000 ticks** (`experiments/results/stage_compare.txt`):

  | run | pop | births | starved % | age | rest % of decisions | tiles/100 ticks | ticks/s |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | M1 rules | 89.1 | 918 | 67.7 | 295 | 0.0 | 66.6 | 585 |
  | M2 defaults | 93.0 | 946 | 66.5 | 300 | 8.7 | 63.5 | 545 |
  | all industrious 10 | 95.0 | 965 | 67.5 | 300 | 11.1 | 62.1 | 526 |
  | all industrious 90 | 92.1 | 938 | 66.3 | 300 | 5.9 | 64.7 | 566 |
  | all curiosity 10 | 93.3 | 949 | 66.9 | 299 | 8.6 | 65.1 | 577 |
  | all curiosity 90 | 93.3 | 934 | 65.8 | 303 | 8.5 | 61.6 | 578 |

  Plain reading: all stage 3 bands hold (pop 80-98, starved 62-73, births
  830-1010, age 265-325, nobody died out). Resting is 8.7% of decisions, not the
  25% of the never-hungry model, because agents are often hungry. Lazy agents
  rest about twice as often as industrious ones. Low curiosity covers about 6%
  more ground than high. Effects on survival are small so far; whether that
  matters is your call. Speed about 7% slower.
- **Browser:** the app's preview launcher could not read the Desktop folder
  (macOS "Operation not permitted"), so the server was started from the shell
  at http://localhost:8765 and checked: no console errors, agent panel and
  new stats display.
- **Not done:** curiosity probe with straightness and
  episode length, emergence report (stage 5) not written; README not updated
  for the new settings.


### Session 2026-11-17 (part 2: starvation + Milestone 2 review plan)
- **Step 0 verified by running (not trusted):** git clean on `main`;
  `python3 -m unittest discover -s tests` -> `Ran 64 tests ... OK` (21 s;
  `pytest` is not installed, unittest is the right command);
  `run_headless.py --seed 42 --ticks 500` -> alive 79, fingerprint
  `61e8b205b6228bc9` (matches STATUS section 7). This is the reference
  fingerprint for this session: it must stay the same.
- **Planned items, checked against the repo:**
  - `why.py --load`: option exists, but it only loads a save and then
    REPLAYS ticks; it does NOT read the stored `history`. NOT done.
  - Performance: speed and save size were measured (section 4), but no
    profiler run / hot-spot breakdown. Only partly done.
  - Mortality investigation: only the regrowth sweep exists (section 6);
    the reason for ~2/3 starvation was never tested. NOT done -> step 1.
  - `docs/MILESTONE2_DECISIONS.md`: does not exist. NOT done (the seven
    questions go into `docs/MILESTONE2_V2.md` in step 3 instead).
- **Step 1 done (starvation study).** New `experiments/starvation_study.py`
  (read-only; same end state as a normal run with `history_keep=0`, checked:
  seed 42, 500 ticks, fingerprint `8b33125c5a5addf9` both ways) and
  `docs/STARVATION.md` with all numbers (raw output in `experiments/results/`).
  Plain findings: the food supply sets how MANY agents live (about 91 of a
  98 ceiling); nothing limits births when the map is full, so the overflow
  starves. Slowing births (`repro_cooldown=400`) drops starved share
  67.7% -> 45.5% with about the same headcount. 26% of starvation deaths are
  agents younger than 80; 14.5% are newborns that never found food (die at
  age 50). 46% of all decisions are "search, nothing in sight". One small
  flaw: 6.2% starve one tick after picking up food (gather and eat are two
  separate ticks). Nothing in code changed; defaults untouched.
- **Step 2 done (review of the ChatGPT review).** `docs/MILESTONE2_REVIEW.md`:
  verdicts: 1 agree (now done), 2 partly, 3 agree, 4 agree, 5 agree (nothing
  tracked yet), 6 agree, 7 partly. Extra finds: new dice draws or new agent
  fields break fingerprints, so I added `genesis/digest.py` (behaviour
  digest that ignores new fields), `experiments/baseline/` (frozen results
  of today's rules), a real v2 save in `tests/fixtures/`, and
  `tests/test_baseline.py` (4 tests). Full suite: 68 tests OK (28 s).
  Fingerprint seed 42 / 500 ticks still `61e8b205b6228bc9`.
- **Step 3 done (staged plan).** `docs/MILESTONE2_V2.md`: 8 stages (0 done),
  definitions of needs and traits with exact whole-number rules (examples
  hand-checked and run), rest/company incentives with alternatives and
  predicted effect on deaths, 8 emergence measures, the 7 questions with
  options and recommendations, and an empty "Your answers" table. I differ
  from the reviewer in one place: personality as thresholds BEFORE any scoring
  system (reason in section 1 of the file). Nothing built.
- **Step 4 done (this log).** Final checks of the session: full suite
  `Ran 68 tests ... OK`; `run_headless.py --seed 42 --ticks 500` gives alive 79,
  fingerprint `61e8b205b6228bc9` (same as step 0). No code default changed,
  no feature of Milestone 2 built. Only code added: `genesis/digest.py`
  (read-only) and the study/baseline scripts.
- **In progress:** nothing. Next: "Next 5 tasks" (needs your answers first).

### Session 2026-11-17 (steps 0-9 plan)
- **Step 0 verified by running:** git clean, 8 commits. 25 tests pass (6.3 s).
  `run_headless.py --seed 42 --ticks 500` gives 49 alive, fingerprint
  `f8afe5e75d1209c4` (matches the claim below). `server.py` could NOT start
  here: the sandbox refuses the local port (`Operation not permitted`). Run it
  yourself: `cd ~/Desktop/"Project Genesis" && python3 server.py`.
- **Plan:** 1 VISION.md, 2 compatible saves, 3 `--set`, 4 water dithering,
  5 `--summary`, 6 browser load message, 7 history in saves, 8 regrow
  experiments, 9 Milestone 2 proposal (docs only).
- **Step 1 done:** `VISION.md` written (principles + works-today vs future).
- **Step 2 done:** saves are now format version 2. `genesis/save.py` migrates
  version 1 -> 2: fills missing config keys / stats / agent fields with
  defaults, logs every fill in `world["migration_log"]`, keeps unknown keys,
  rejects newer versions and saves missing essentials with plain messages.
  5 new tests (30 total, all pass). The real `saves/quicksave.json` (v1) loads.
- **Step 3 done:** `--set name=value` in `run_headless.py` and `why.py`
  (`genesis/overrides.py`: type + range rules per setting, plain errors listing
  valid names, last repeat wins, config files untouched, README documented).
  11 new tests (41 total, all pass).
- Note: steps 1 and 2 share one commit (my slip); every later step has its own.
- **Step 4 done (water dithering).**
  Cause in 3 lines: (1) agents picked the nearest food by straight-line
  distance, ignoring water, and re-picked every tick; (2) when the straight
  step was water they wandered at random, then re-targeted the same food;
  (3) so they bounced at lakes and chased food across water they could never
  reach. Fix: `_walk_to_food` in `genesis/agents.py`. It finds food by real
  walking distance with a small search limited to what the agent can see
  (at most 13x13 tiles, fixed order, no dice), ignores unreachable food, and
  keeps its chosen food (`target`) until eaten. A first try with only
  "step around the obstacle" looped around a long wall (the new wall test
  showed it), so the small search was needed.
  Before -> after, seeds 42,1,2,3,4 x 2000 ticks (totals): births 2099 -> 2083,
  starved 1442 -> 1414 (68.7% -> 67.9% of births), alive at end 283 -> 302.
  Back-and-forth moves (A->B->A) while heading for food: 9,828 -> 5,384.
  Seed 42 alone: starved 285 of 427 births -> 279 of 414.
  Cost: speed fell from ~1.1 s to ~1.9 s per 2,000 ticks (~1,050 ticks/s).
  7 new tests in `tests/test_movement.py` (48 total, all pass).
- **Step 5 done (`--summary`).** New `genesis/summary.py` (`RunRecorder`),
  `--summary` flag in `run_headless.py`, die events now carry `age` and
  `cause`. Checked: its counts equal the world's own counters and
  start + births - deaths = end (seed 42, 2000 ticks: 50 + 414 - 410 = 54).
  5 new tests (53 total). README documented.
- **Step 6 done (browser load message).** Server's load reply now reads
  "Loaded NAME: tick N, seed S (paused)". The page shows it as a pop-up
  (`#toast` in `web/`) that fades after ~3.5 s, ignores clicks
  (`pointer-events: none`) and turns red and stays ~6 s on failure. Damaged saves
  now give a plain "save file is damaged" error instead of a crash.
  2 new tests in `test_controls.py` (55 total, all pass).
  **How it was checked, honestly:** the sandbox blocks the server port, so
  the real page could not be loaded. In the built-in browser I opened the
  page as a static snapshot, injected the new CSS and `showToast` function,
  and saw: success text visible, opacity 1, `pointer-events: none`, then
  hidden with opacity 0 after ~4.6 s; error variant red. NOT checked: the
  full click on the real Load button. Please try once: run `python3 server.py`,
  Save, then Load, and look at the top of the page.
- **Step 7 done (history in saves).** New `genesis/history.py`; `sim.step`
  records every decision into `world["history"]` (per agent) and
  `world["history_dead"]`; the page's trail now reads from it (so it survives
  load). Settings `history_keep` (default 20 per agent) and
  `dead_history_keep` (default 50 dead agents). Old saves without history load
  (logged in `migration_log`) and start remembering from the load.
  **Measured, seed 42, 2,000 ticks:** save size 28 KB -> 605 KB (history off
  -> default); save 4 ms, load 4 ms; speed 993 -> 846 ticks/s (about 15%
  slower). Cap needed: yes. Without limits history grows forever; with
  keep=30 and 100 dead the save was 1.3 MB, and keeping 400 dead was 3.8 MB.
  Size is roughly (alive + dead kept) x 20 x ~290 bytes. A string table would
  roughly halve it; not done (adds complexity, files are still small).
  9 new tests (64 total, all pass), including history belongs to the right
  agent, dead agents kept, limits, old save, behaviour unchanged by history.
  Decision resolved: history IS now stored in saves (see Decisions).
- **Step 8 done (regrow experiments).** Default in code NOT changed (still 4).
  Script: `experiments/regrow_sweep.py` (calls `run_headless.py --summary --set`;
  history was switched off with `--set history_keep=0` for speed; this does not
  change behaviour, test-checked). 6 values x 5 seeds (42,1,2,3,4) x 3,000
  ticks. Results are averages over the 5 seeds; table and recommendation are
  in the final section below.
- **Step 9 done:** `docs/MILESTONE2.md` (proposal only, nothing built).
- **Later: default `regrow_per_tick` changed 4 -> 6 at your request.**
- **Final check (before that change):** 64 tests pass; `run_headless.py --seed 42 --ticks 500`
  gives 55 alive, fingerprint `2e91ef5c79b33484`, identical on two runs.
  Server port still blocked in this sandbox (see section 9).
- **In progress:** nothing. Next: "Next 5 tasks".

## Appendix: earlier results kept for reference

### Regeneration experiment results (earlier session)

`regrow_per_tick` changed with `--set`, code default was 4 when measured (changed to 6 afterwards, see section 7). 5 seeds
(42, 1, 2, 3, 4) x 3,000 ticks each, averages, via
`python3 experiments/regrow_sweep.py` (about 1 minute, reproduced twice).

| regrow | died out | agents at end | lowest pop | highest pop | starved % of deaths | avg age at death | avg food on map | pop at t300 / t1500 / t3000 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 0/5 | 28.8 | 20.4 | 81.2 | 75.6 | 275 | 53 | 31 / 29 / 29 |
| 3 | 0/5 | 45.0 | 34.2 | 92.8 | 71.9 | 287 | 33 | 51 / 47 / 45 |
| **4 (default)** | 0/5 | 60.8 | 48.0 | 107.0 | 68.9 | 295 | 37 | 78 / 58 / 61 |
| 6 | 0/5 | 93.8 | 50.0 | 142.2 | 67.7 | 295 | 46 | 134 / 92 / 94 |
| 8 | 0/5 | 123.8 | 50.0 | 192.4 | 66.5 | 297 | 59 | 184 / 121 / 124 |
| 12 | 0/5 | 173.4 | 50.0 | 287.4 | 67.6 | 288 | 111 | 211 / 178 / 173 |

What the numbers say: population grows about in proportion to regrowth, and
nobody died out at any value. The starved share barely moves (76% down to
about 67%), so more food gives more agents, not a gentler world. Every run
shows a boom then a drop (for example 78 at tick 300 down to 58 at tick 1500
at the default), then a steady level. Only 5 seeds, one map size, one length.
The reason the starved share stays put is a guess (agents multiply until food
is short again); it was not tested.

### Recommended `regrow_per_tick` (decided: 6)

**Decision made: 6.** The code default is now 6 (was 4). After the change: 64 tests pass; seed 42, 500 ticks gives 79 alive, fingerprint `61e8b205b6228bc9`. Older fingerprints in this file are from default 4.
- It keeps the world as deadly as before (starved share 67.7% against 68.9%,
  average age at death unchanged at 295), which matches "no peaceful world".
- It gives a steady population of about 94 instead of 61 (lowest 50 instead of
  48), so there are more agents near each other for later social features,
  and it is less fragile (at 2 or 3 the population sits at 29 to 45).
- It costs speed: roughly 50% more agents means roughly 50% more work per tick.
- If you prefer fewer agents or faster runs, keep 4: it is also stable.
- Values of 8 or more mainly add agents (123 to 173) without more scarcity.
To try it: `python3 run_headless.py --seed 42 --ticks 2000 --every 0 --summary --set regrow_per_tick=6`

