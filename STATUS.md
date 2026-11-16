# Project Genesis: status

Last checked: 2026-11-17, by actually running the commands below (not from memory).

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
| `genesis/agents.py` | How an agent decides what to do, and its "why" text |
| `genesis/sim.py` | Moves time forward one step (a "tick") |
| `genesis/save.py` | Save, load, and a "fingerprint" (a short code that is equal only if two worlds are exactly equal) |
| `genesis/rng.py` | The dice. Their whole memory is one number, so a save can store it |
| `genesis/__init__.py` | Lists what the folder offers to other files |
| `run_headless.py` | Runs the world in the Terminal, no page |
| `server.py` | Runs the world and shows it on a local web page |
| `web/` | The page: `index.html`, `style.css`, `app.js` |
| `tests/` | Automatic checks (11 of them) |
| `saves/` | Your saved worlds. Not stored in git. Holds `quicksave.json`, a test save |
| `README.md` | Longer guide: controls, how agents think, things to try |
| `STATUS.md` | This file |
| `.gitignore` | Tells git which files to leave out (saves, logs, caches) |
| `.claude/` | Settings for the Claude app, not part of the project. Left out of git |

Git history: 3 commits, all from 2026-11-17. Nothing uncommitted.

## How to run it

See the world on a map (your browser opens by itself):

```bash
cd ~/Desktop/"Project Genesis"
```

```bash
python3 server.py
```

Stop it with **Ctrl+C** in the Terminal. If it says the port is in use, it
is already running in another Terminal window.

Run the automatic checks:

```bash
python3 -m unittest discover -s tests -v
```

Run in the Terminal with no page:

```bash
python3 run_headless.py --seed 42 --ticks 500
```

## What works

Checked today:

- All 11 tests pass.
- `run_headless.py --seed 42 --ticks 500` ends with 49 agents alive and
  fingerprint `f8afe5e75d1209c4`, the same every time.
- The map page: pause/play, one step, speeds 1× 2× 5× 20×, new world from a
  seed, save, load, click an agent to see its last 12 decisions.
- `saves/quicksave.json` loads (seed 42, tick 39, 55 agents).
- Saves store the seed, the tick count and the position of the dice, so a
  loaded world continues exactly as the original would have.

## What is broken or missing

Nothing is broken. What is missing for Milestone 1:

- The "why" is one sentence. It does not yet record the **need**, the
  **options considered** and the reason, as separate parts.
- You can see one agent's last decisions only on the page, and only for the
  time the page has been running. There is no Terminal command for it.
- Pause, speed, save and load are not covered by automatic tests (they were
  checked by hand in the browser).

Known rough edges (not blocking):

- The world is harsh: about two thirds of all deaths are starvation.
- Agents sometimes dither when water lies between them and food.
- Several agents can stand on the same tile.

## Milestone 1 checklist

| Item | State |
| --- | --- |
| Small seeded world | done |
| About 50 agents that eat, move, gather, reproduce, die | done |
| Simple map view | done |
| Pause and speed controls | done (no automatic test yet) |
| Save / load | done |
| Simulation runs with no UI | done |
| Test: same seed gives same world and same result after N steps | done |
| Test: save then load gives identical state | done |
| "Why" log for every decision | partly: one sentence, not need + options + reason |
| Command or view for one agent's last decisions | partly: page only |

## Decisions you need to make

- **The vision document is not in this folder.** If you have it, copy it in
  as `VISION.md` so later sessions can read it.
