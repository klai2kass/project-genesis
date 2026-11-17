# Project Genesis: status

Last checked: 2026-11-17, by actually running the commands below (not from memory).

**Milestone 1 is complete.** Read "Next 5 tasks" to continue.

## Session log

Newest first. A fresh session should read this section first.

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
- **In progress:** step 9 (Milestone 2 proposal).

## What this project is

A small artificial world that runs on this Mac, offline and for free.
Simple creatures ("agents") live on a map: they look for food, eat, have
children and die. The world is built from a **seed** (any number or word):
the same seed always produces exactly the same world and the same story.
You can watch it on a map in your browser and ask **why** an agent did
something.

The long-term vision (agents with personalities, needs and memories) is
**not** in this folder as a document. See "Decisions you need to make".

## What exists

Everything is written in Python 3.9 (already on the Mac). The map page uses
a little HTML, CSS and JavaScript, only to draw. Nothing was installed.

| File or folder | What it is |
| --- | --- |
| `genesis/` | The simulation itself. Runs with no window ("headless") |
| `genesis/config.py` | All the numbers: map size, food, energy, lifespan |
| `genesis/world.py` | Builds a new world from a seed |
| `genesis/agents.py` | How an agent decides: its need, its options, its reason |
| `genesis/sim.py` | Moves time forward one step (a "tick") |
| `genesis/save.py` | Save, load, and a "fingerprint" (a short code that is equal only if two worlds are exactly equal) |
| `genesis/rng.py` | The dice. Their whole memory is one number, so a save can store it |
| `genesis/whylog.py` | Turns decision records into readable text |
| `genesis/__init__.py` | Lists what the folder offers to other files |
| `run_headless.py` | Runs the world in the Terminal, no page |
| `why.py` | Shows the last decisions of one agent |
| `server.py` | Runs the world and shows it on a local web page |
| `web/` | The page: `index.html`, `style.css`, `app.js` |
| `tests/` | Automatic checks (25 of them, in 4 files) |
| `saves/` | Your saved worlds. Not stored in git. Holds `quicksave.json`, a test save |
| `README.md` | Longer guide: controls, how agents think, things to try |
| `STATUS.md` | This file |
| `.gitignore` | Tells git which files to leave out (saves, logs, caches) |
| `.claude/` | Settings for the Claude app, not part of the project. Left out of git |

## How to run it

See the world on a map (your browser opens by itself):

```bash
cd ~/Desktop/"Project Genesis"
```

```bash
python3 server.py
```

Stop it with **Ctrl+C** in the Terminal. If it says the port is in use, it
is already running in another Terminal window. After any code change, stop
it and start it again to see the change.

Run the automatic checks (should end with `Ran 25 tests` and `OK`):

```bash
python3 -m unittest discover -s tests -v
```

Run in the Terminal with no page:

```bash
python3 run_headless.py --seed 42 --ticks 500
```

Ask why agent 12 did what it did:

```bash
python3 why.py --seed 42 --ticks 300 --agent 12
```

## What works

Checked on 2026-11-17:

- All 25 tests pass.
- `run_headless.py --seed 42 --ticks 500` ends with 49 agents alive and
  fingerprint `f8afe5e75d1209c4`, the same every time.
- The map page: pause/play, one step, speeds 1× 2× 5× 20×, new world from a
  seed, save, load. Click an agent to see its need, the options it weighed,
  its reason, and its earlier decisions.
- `why.py` prints the last decisions of any agent, alive or dead.
- Saves store the seed, the tick count and the position of the dice, so a
  loaded world continues exactly as the original would have.
- Speed: about 1,800 ticks per second with no page (2,000 ticks in 1.1 s).
  A save file is about 30 KB.

## What is broken or missing

Nothing is broken. Rough edges, none blocking:

- The world is harsh: about two thirds of all deaths are starvation.
- Water dithering fixed in step 4 (see Session log). Food farther than the 13x13 view is still unseen.
- Several agents can stand on the same tile.
- The page forgets an agent's earlier decisions when you load a save or
  restart the server. `why.py` does not have this limit.
- No automatic test clicks the real web page. It was checked by hand.

## Milestone 1 checklist

| Item | State |
| --- | --- |
| Small seeded world | done |
| About 50 agents that eat, move, gather, reproduce, die | done |
| Simple map view | done |
| Pause and speed controls | done, tested in `tests/test_controls.py` |
| Save / load | done |
| Simulation runs with no UI | done |
| Test: same seed gives same world and same result after N steps | done, `tests/test_determinism.py` |
| Test: save then load gives identical state | done, `tests/test_save_load.py` |
| "Why" log: need, options considered, reason | done, `tests/test_why_log.py` |
| Command and view for one agent's last decisions | done: `why.py` and the page's Agent panel |

## Design choices (one line each)

- **Python for everything, plus a thin web page.** Node.js is not installed;
  Python is, so nothing needs installing.
- **The world is one plain dictionary.** That makes a save file just that
  dictionary written as text (JSON).
- **Our own small dice (`rng.py`).** Its memory is one number, and it gives
  the same results on every Python version.
- **Rules in a fixed order, first one that fits wins.** Simplest thing that
  explains itself. Scoring by needs can replace it in a later milestone.
- **Recent decisions ARE stored in the save** (last 20 per agent, last 50
  dead agents). `why.py` still replays from the seed.
- **The server runs the world; the page only draws.** So the rules exist in
  one place and stay testable.

## Next 5 tasks

Each is small. After each one: run the tests, commit, update this file.
Changing a rule changes every fingerprint. That is expected; the tests
compare two runs with each other, not against a stored code.

1. **Make old saves survive new settings.**
   Files: `genesis/save.py`, `tests/test_save_load.py`.
   When loading, fill any setting missing from the save's `config` with the
   value from `DEFAULT_CONFIG`. Add a test that deletes one key from a save
   and loads it.
   Check: `python3 -m unittest discover -s tests -v`

2. **Try settings without editing files.**
   Files: `run_headless.py`, `why.py`.
   Add `--set name=value` (repeatable) and pass it to `create_world(seed, config)`.
   Check: `python3 run_headless.py --seed 42 --ticks 500 --set regrow_per_tick=6`
   (should end with more agents alive than 49).

3. **Stop agents dithering at water.**
   Files: `genesis/agents.py` (`_choose_move`), new `tests/test_movement.py`.
   When the straight step is blocked, try the two directions next to it
   before wandering. Test with a tiny hand-made world with a strip of water.
   Check: `python3 run_headless.py --seed 42 --ticks 2000` (today: 285
   starved out of 427 births; it should not get worse).

4. **A summary of how lives went.**
   Files: `run_headless.py`, `genesis/whylog.py`, `tests/test_why_log.py`.
   Add `--summary`: deaths by cause, average age at death, share of children
   that died before adulthood.
   Check: `python3 run_headless.py --seed 42 --ticks 2000 --summary`

5. **Keep an agent's story on the page after loading a save.**
   Files: `server.py` (`Game._use_world`), `tests/test_controls.py`.
   Simplest way: after a load, show a note in the Agent panel that earlier
   decisions are available through `why.py`. Do not store history in saves
   without asking (see decisions).
   Check: `python3 -m unittest discover -s tests -v`, then load a save on the page.

## Known risks

- **Python 3.9 only.** Do not use newer Python features (`match`, `int | str`).
- **Replays only match if code and settings are unchanged.** `why.py` on an
  old save shows today's rules, not the rules from when it was saved.
- **One test uses real time** (`test_pause_stops_time_and_play_restarts_it`
  waits 0.7 s). On a very busy Mac it could fail once; run it again.
- **Claude's sandbox blocks two things**: writing to `.git` (commits need
  approval) and opening a local port (so `server.py` must be started
  outside the sandbox, or by you in the Terminal). Your own Terminal is not
  affected.
- **Big populations slow the page.** At 20× speed with over ~300 agents,
  Python may not keep up. Not a problem at today's ~50-100.
- **Only a local git history, no backup.** Run `git push` yourself when you
  have a remote set up.

## Decisions you need to make

1. **Add the vision document.** Copy it into this folder as `VISION.md` so
   later sessions can read it. It was never in the repo.
2. **Is the harsh world what you want?** Most children starve. One number
   changes it: `regrow_per_tick` in `genesis/config.py` (higher = gentler).
3. **What is Milestone 2?** Suggestion: needs as numbers (hunger, rest,
   company) and personality traits that change the rule order, still with
   no LLM. Nothing for it has been started.
4. **Should saves also keep each agent's recent decisions?** Today they do
   not (smaller files, simpler). Say so if you want the history inside saves.
