# Project Genesis: status

Last checked: 2026-11-17, by running the commands in this file (not from memory).

**Milestone 1 is complete and Steps 0-9 of the second session are done.**
Milestone 2 is only a written proposal (`docs/MILESTONE2.md`). Read the
"Session log" first, then "Next 5 tasks" and "Decisions you need to make".

## Session log

Newest first. A fresh session should read this section first.

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
11, save_load 9, summary 5, why_log 6. Not covered by automatic tests: the
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

## 8. Milestone 2 proposal

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

All automatic checks (end should say `Ran 64 tests` and `OK`):

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

## 10. Next 5 tasks

1. **Check the real page by hand.** Files: none. Run `python3 server.py`,
   press Save, then Load, and confirm the pop-up at the top fades. Click an
   agent after loading and confirm earlier decisions are listed.
   Check: you see both. Tell me if not.
2. **Let `why.py --load` read stored history.** Files: `why.py`,
   `genesis/history.py`, new test in `tests/test_history.py`. When the save has
   history for the agent and `--ticks 0`, print it without replaying.
   Check: `python3 -m unittest discover -s tests` and
   `python3 run_headless.py --seed 42 --ticks 300 --save saves/t.json` then
   `python3 why.py --load saves/t.json --ticks 0 --agent 3`.
3. **Find what really changes the death rate.** Files: new
   `experiments/mortality_sweep.py` (copy of the regrow sweep), STATUS.md.
   Sweep `repro_cost`, `food_energy`, `repro_cooldown` (never the code defaults).
   Check: `python3 experiments/mortality_sweep.py`.
4. **Milestone 2, build step 1** (fields only, behaviour unchanged). Files:
   `genesis/world.py`, `genesis/save.py`, `web/app.js`, tests. Needs your
   answers first (below). Check: all tests pass, `saves/quicksave.json` loads.
5. **Optional: shrink saves with a string table.** Files: `genesis/save.py`,
   `tests/test_save_load.py`. Only if 600 KB saves bother you; estimated about
   half the size. Check: same tests plus a size print.

## Decisions you need to make

Safe defaults were used for all of them.

1. ~~`regrow_per_tick`~~ Decided: switched to 6 (section 7).
2. **History caps.** 20 decisions per agent, 50 dead agents (605 KB saves).
   Default: kept as is. Lower for smaller saves, higher for longer stories.
3. **Milestone 2.** Read the 7 questions at the end of `docs/MILESTONE2.md`;
   say "go with the defaults" or answer them. Nothing is started until then.
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
