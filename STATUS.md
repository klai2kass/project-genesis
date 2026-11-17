# Project Genesis: status

Last checked: 2026-11-17, by running the commands in this file (not from memory).

**Milestone 1 is complete. Milestone 2 (rest, curiosity, industriousness) is
IMPLEMENTED and committed (not pushed).** Design:
`docs/MILESTONE2_V2.md`. Starvation background: `docs/STARVATION.md`. Read the
"Session log" first.

## Session log

Newest first. A fresh session should read this section first.

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

## 1. What was completed

All steps 0-9 of this session: verified state; `VISION.md`; backward-
compatible saves; `--set`; water dithering fix; `--summary`; load pop-up in
the browser; decisions stored in saves; regrowth experiment; Milestone 2
proposal. Every step except the first two has its own commit (steps 1 and 2
share one). Nothing was pushed (there is no remote).

Plain words: a **fingerprint** is a short code equal only when two worlds are
exactly equal. A **tick** is one step of time. **Headless** means running
with no window. A **migration** upgrades an old save file when loading.

## 2. What changed (file by file)

| File | Change |
| --- | --- |
| `VISION.md` (new) | Principles and roadmap, "works today" vs "future" |
| `genesis/save.py` | Save format 2; repairs missing/old fields on every load; `migration_log`; keeps unknown keys; plain errors |
| `genesis/overrides.py` (new) | Type and range checks for `--set` |
| `genesis/agents.py` | `_walk_to_food`: real walking distance, ignores unreachable food, keeps its target |
| `genesis/history.py` (new) | Per-agent decision history stored in the world |
| `genesis/summary.py` (new) | Report behind `--summary` |
| `genesis/sim.py` | Records history; die events carry `age` and `cause` |
| `genesis/world.py` | Save version 2; agents get `target`; world gets `history`, `history_dead` |
| `genesis/config.py` | New settings `history_keep` (20), `dead_history_keep` (50) |
| `run_headless.py`, `why.py` | `--set` (both), `--summary` (headless) |
| `server.py` | Trail now read from the world's history; load reply shows tick and seed |
| `web/app.js`, `index.html`, `style.css` | Fading load/error pop-up |
| `experiments/regrow_sweep.py` (new) | The regrowth comparison |
| `docs/MILESTONE2.md` (new) | The proposal |
| `tests/` | 4 new files; additions to `test_save_load.py`, `test_controls.py` |
| `README.md` | `--set`, `--summary`, new files |

## 3. Tests actually run (this session, final run)

`python3 -m unittest discover -s tests` printed `Ran 64 tests in 16.4s` and
`OK`. By file: controls 11, determinism 7, history 8, movement 7, overrides
11, save_load 9, summary 5, why_log 6. (Later the same day, with the new
`tests/test_baseline.py`: `Ran 68 tests in 28.5s`, `OK`.) Not covered by automatic tests: the
real web page in a browser (see Remaining limits), and starting the server.

## 4. Current performance (seed 42, 2,000 ticks, this Mac, measured)

| | Speed | Save size | Save / load time |
| --- | --- | --- | --- |
| History on (default 20 / 50) | about 850 ticks/s | 605 KB | 4 ms / 4 ms |
| History off (`--set history_keep=0`) | about 990 ticks/s | 28 KB | under 1 ms |
| Before this session (Milestone 1) | about 1,800 ticks/s (claimed earlier; the old code measured 1.1 s per 2,000 ticks) | about 30 KB | not measured |

Timings are noisy (a few runs varied by about 10%). The slowdown comes from
the new walking-distance search (step 4) and from history (step 7).

## 5. Remaining bugs and limitations

- The real server and page were NOT run in this sandbox (port blocked). The
  load pop-up was checked only as an injected snippet (see step 6 above).
- Food farther than the view (13 x 13 tiles) is still unseen. A long detour
  around a very large lake is not planned; the agent re-searches each tick.
- Several agents can still stand on one tile.
- Starvation is still about two thirds of all deaths at every regrowth
  setting tested (section 6).
- History makes saves about 20 times bigger (605 KB); fine on disk, grows
  with population (about 290 bytes per remembered decision).
- `why.py` still replays from the seed; it does not read stored history.
- Back-and-forth moves while heading to food fell from 9,828 to 5,384 over
  5 seeds x 2,000 ticks, not to zero (food gets eaten by others, so targets change).
- One test uses real time (0.7 s) and could rarely fail on a very busy Mac.
- Python 3.9 only; no remote backup (run `git push` yourself once a remote exists).

## 6. Regeneration experiment results

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

## 7. Recommended `regrow_per_tick`

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

## 8. Milestone 2 proposal, review and revised plan

Read in this order: `docs/STARVATION.md` (why 2/3 starve), then
`docs/MILESTONE2_REVIEW.md` (7 verdicts on the ChatGPT review), then
`docs/MILESTONE2_V2.md` (staged plan, 8 emergence measures, your 7 questions,
empty answers table). The original proposal follows; V2 replaces its build
order and some of its rules.

Written in full in [docs/MILESTONE2.md](docs/MILESTONE2.md): numerical needs
(hunger, rest, company), four personality traits, scored decisions with
"why" records, no LLM, file changes, save changes, determinism, tests,
performance risks, 8-step build order, 7 decisions for you. Not built.

## 9. Copy-paste commands

Run from the project folder:

```bash
cd ~/Desktop/"Project Genesis"
```

See the map in your browser (run this in your own Terminal; Claude's sandbox
blocks the port). Stop with Ctrl+C:

```bash
python3 server.py
```

All automatic checks (end should say `Ran 109 tests` and `OK`):

```bash
python3 -m unittest discover -s tests
```

Run with no page and a report:

```bash
python3 run_headless.py --seed 42 --ticks 2000 --every 0 --summary
```

Experiment with settings (repeat `--set` as needed; nothing is saved to files):

```bash
python3 run_headless.py --seed 42 --ticks 2000 --every 0 --summary --set regrow_per_tick=6 --set vision=6
```

Why did agent 12 do that?

```bash
python3 why.py --seed 42 --ticks 300 --agent 12
```

Compare regrowth values:

```bash
python3 experiments/regrow_sweep.py
```

Why do agents starve (about 25 s), and the settings sweep (about 4 min):

```bash
python3 experiments/starvation_study.py
python3 experiments/starvation_study.py --sweep
```

Check that behaviour still equals the frozen Milestone 1 reference (about 1 min):

```bash
python3 experiments/baseline/make_baseline.py --check
```

## 10. Next 5 tasks

1. **Curiosity probe and emergence report** (stage 4 probe, stage 5 of
   `docs/MILESTONE2_V2.md`), and README notes for the 13 new settings.
2. **Check the real page by hand.** Run `python3 server.py` in your own
   Terminal, press Save, then Load, and confirm the pop-up at the top fades;
   click an agent after loading and confirm earlier decisions are listed.
3. **Stage 1 of the V2 plan** (fields and save version 3, behaviour
   unchanged). Files: `genesis/world.py`, `genesis/save.py`, `genesis/sim.py`,
   `tests/test_save_load.py`. Check: `python3 -m unittest discover -s tests`
   and `python3 experiments/baseline/make_baseline.py --check` (digests equal).
4. **Let `why.py --load` read stored history** (still not done). Files:
   `why.py`, `genesis/history.py`, `tests/test_history.py`. Check: unit tests;
   `python3 run_headless.py --seed 42 --ticks 300 --save saves/t.json` then
   `python3 why.py --load saves/t.json --ticks 0 --agent 3` prints stored decisions.
5. **Measure the two starvation guesses** (cheap, read-only): food in view at
   birth against a random tile, and food taken by someone else before an agent
   arrived. Files: `experiments/starvation_study.py`. Check: new numbers in
   `docs/STARVATION.md` under "What is only a guess".

## Decisions you need to make

Safe defaults were used for all of them.

1. ~~`regrow_per_tick`~~ Decided: switched to 6 (section 7).
2. **History caps.** 20 decisions per agent, 50 dead agents (605 KB saves).
   Default: kept as is. Lower for smaller saves, higher for longer stories.
3. **Milestone 2 design approval.** All answers and the 3 open points are
   resolved in `docs/MILESTONE2_V2.md` (section "Final proposed mechanics at a
   glance" is the summary). Final review points handled: dice streams
   (section 2a, `tests/test_trait_streams.py`, 5 design tests), complete rest
   behaviour with test list, curiosity probe reports numbers and you decide.
   Decided: industriousness = how fast an agent tires while moving (option B,
   integer accumulator, 150 / 100 / 50 hundredths per move at trait 0 / 50 /
   100; `tests/test_rest_design.py`, 14 design tests: extremes and the complete rest cycle).
   APPROVED 2026-11-17 (`rest_resume = 70`). Next: stage 1 of the plan, only when you say go.
4. **The gather-then-eat flaw.** 6.2% of starvation deaths happen one tick
   after picking food up (gather and eat are two ticks). Fixing it changes
   behaviour and all baselines. Default: NOT fixed, so that Milestone 2 is
   compared against today's world.
4. **Is the harsh world right?** This session's data suggests food amount
   alone does not change the share of starvation deaths. If you want that
   share lower, task 3 looks for levers; this is your call.
5. **Dither fix is slower** (about 1.1 s to 1.9 s per 2,000 ticks). Acceptable?
   Default: yes.

## Design choices (one line each)

- **Python for everything, plus a thin web page.** Node.js is not installed.
- **The world is one plain dictionary.** A save is that dictionary as JSON text.
- **Our own dice (`rng.py`).** Its memory is one number, stored in the save.
- **Rules in a fixed order, first one that fits wins.** Scoring is proposed for Milestone 2.
- **Decisions ARE stored in saves** (capped), so the page survives load.
- **Old saves are repaired on every load** with documented defaults, never silently.
- **The server runs the world; the page only draws.**

## Known risks

- Claude's sandbox blocks writing to `.git` in some modes and opening a port;
  commits worked in this session, the server did not start.
- Replays (`why.py`) match only if code and settings are unchanged.
- Big populations slow the page (over about 300 agents at 20x).
