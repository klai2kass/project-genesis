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
- **In progress:** step 1.

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
- Agents sometimes dither when water lies between them and food.
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
- **Decision records are not stored in the save.** They are rebuilt by
  replaying the seed (`why.py`). This keeps saves small and old saves loadable.
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
