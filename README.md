# Project Genesis

A small world that runs on your Mac. About 50 simple agents wander a map,
look for food, eat, have children and die. Nothing is installed and nothing
is paid for: it only needs the Python that is already on your Mac.

This is **Milestone 1**: no AI model (LLM) yet, just clear rules.

## Run it

Open the Terminal app, then:

```bash
cd ~/Desktop/"Project Genesis"
```

```bash
python3 server.py
```

Your browser opens at http://127.0.0.1:8765 and the world starts moving.
To stop it, click the Terminal window and press **Ctrl+C**.

Want a different world? `python3 server.py --seed banana`

## What you can do on the page

| Control | What it does |
| --- | --- |
| **Pause / Play** (or space bar) | Stop and start time |
| **Step** | Move forward exactly one tick |
| **1× 2× 5× 20×** | Speed (1× is 4 ticks per second) |
| **Seed + New world** | Build a fresh world. Same seed = same world, always |
| **Save** | Writes the world to `saves/<name>.json` |
| **Load** | Brings a saved world back (it loads paused) |
| **Click an agent** | See its energy, age, what it needs, the options it weighed, and *why* it chose |
| **Feed** | Births and deaths, or every single decision |

## Check that it works (tests)

```bash
python3 -m unittest discover -s tests -v
```

The tests prove the two promises this project is built on:

- **Same seed = same result.** Two runs with one seed end up identical,
  decision for decision.
- **Save → load = same state.** A loaded world is identical to the one that
  was saved, and it also *continues* identically.

## Run it without the page (headless)

```bash
python3 run_headless.py --seed 42 --ticks 1000
```

It prints the population over time and ends with a `fingerprint`. Run the
same command twice: the fingerprint is the same. Other options:

```bash
python3 run_headless.py --seed 42 --ticks 500 --save saves/day500.json
```

```bash
python3 run_headless.py --load saves/day500.json --ticks 500
```

```bash
python3 run_headless.py --seed 42 --ticks 200 --log decisions.jsonl
```

The last one writes every decision and its "why" to a file, one per line.

## Try settings without editing files (`--set`)

Both `run_headless.py` and `why.py` accept `--set name=value`. Repeat it for
several settings. It changes that one run only; no file is ever modified.
A `--set` value beats the default (and, with `--load`, beats the save's value).

```bash
python3 run_headless.py --seed 42 --ticks 500 --set regrow_per_tick=6
```

```bash
python3 run_headless.py --seed 42 --ticks 500 --set regrow_per_tick=6 --set vision=6 --set food_cap=0,3,10
```

```bash
python3 why.py --seed 42 --ticks 300 --agent 12 --set regrow_per_tick=6
```

Notes: `food_cap` takes three numbers (water, grass, forest). If you give the
same name twice, the last one wins. A wrong name or value stops with a plain
message that lists the valid names. With `--load`, map-building settings
(`width`, `height`, `water_share`, `forest_share`, `start_food_share`,
`start_agents`, `start_energy`) are refused because the world already exists.

## A report about a run (`--summary`)

```bash
python3 run_headless.py --seed 42 --ticks 2000 --every 0 --summary
```

Prints: seed, ticks, population (start, end, lowest, highest), births,
deaths by cause, the starved share, average age at death, how many died
before adulthood, the population at ten points in time, and how much food
lay on the map. It ends with a "Not tracked" list of things the simulation
does not record, so nothing is made up. With `--load`, the counts cover only
the ticks of that run. Combine with `--set` to compare settings.

## Ask why one agent did something

List who is alive after 300 ticks:

```bash
python3 why.py --seed 42 --ticks 300
```

Show the last 5 decisions of agent 12:

```bash
python3 why.py --seed 42 --ticks 300 --agent 12
```

Each decision shows the agent's **need**, every **option** it considered
(`no`, `could`, or `CHOSEN`) and the **why**. Add `--last 20` for more, or
use `--load saves/quicksave.json` to start from a save.

## How an agent thinks

Every tick, each agent loses 1 energy and gets 1 tick older. Then it picks
the first rule that fits:

1. **Eat** if it carries food and has room for the energy.
2. **Reproduce** if it is strong, grown up and rested.
3. **Gather** if there is food on its tile and room in its pack.
4. **Move** toward the nearest food it can see, or wander if it sees none.

It **dies** if its energy hits 0 (starved) or it reaches its lifespan (old age).

Every decision is recorded with three parts: the **need** ("food, energy 41
of 100"), the **options** it considered and whether each fitted, and the
**why**, for example `gather — 2 food on this tile and my pack has room (1/3)`.

## Where things live

| File | What it is |
| --- | --- |
| `genesis/config.py` | **All the numbers** (map size, food, energy, lifespan). Start here to experiment |
| `genesis/world.py` | Builds a new world from a seed |
| `genesis/agents.py` | The decision rules (`decide`) and their "why" text |
| `genesis/sim.py` | One tick of time (`step`) |
| `genesis/save.py` | Save, load, fingerprint |
| `genesis/rng.py` | The dice. One number, so saves can store it |
| `genesis/whylog.py` | Turns decision records into readable text |
| `run_headless.py` | Run with no page |
| `why.py` | Show the last decisions of one agent |
| `server.py` | Runs the world and serves the page |
| `web/` | The page. It only draws; no rules live there |
| `tests/` | The automatic checks |
| `STATUS.md` | What works right now, and what to do next |

The `genesis/` folder never touches the page or the server. That is what
lets the tests run it with no UI.

## Things to try

Open `genesis/config.py`, change one number, start a new world:

- `regrow_per_tick`: more food growing means a bigger population.
- `vision`: how far agents see food.
- `repro_cooldown`: lower it and watch a baby boom, then a famine.
