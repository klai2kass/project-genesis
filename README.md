# Project Genesis

A small world that runs on your Mac. About 50 simple agents wander a map,
look for food, eat, have children and die. Nothing is installed and nothing
is paid for: it only needs the Python that is already on your Mac.

Milestone 1 (food, children, death), **Milestone 2** (a rest need and two
personality traits, curiosity and industriousness) and three steps of
**Milestone 3** (every agent has a home it stays near, remembers whom it has
met, and shares food with a starving agent it knows) are built. No AI model
(LLM): every decision comes from a few clear rules, and every decision says
why. What the traits actually do, measured: `docs/MILESTONE2_REPORT.md`.

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
| **Click an agent** | See its energy, rest, traits, home (gold square on the map), whom it knows best (and food given or received), age, what it needs, the options it weighed, *why* it chose, and its earlier decisions |
| **Stats** | Alive, births, deaths by cause, resting now, average curiosity and industriousness, food shared, newest generation, population graph |
| **Feed** | Births and deaths, or every single decision |

## Check that it works (tests)

```bash
python3 -m unittest discover -s tests -v
```

It should end with `Ran 145 tests` and `OK` (about 1.5 minutes).

The tests prove the two promises this project is built on:

- **Same seed = same result.** Two runs with one seed end up identical,
  decision for decision.
- **Save → load = same state.** A loaded world is identical to the one that
  was saved, and it also *continues* identically. Saves from older versions
  (1 to 6) still load and keep their old rules.
- **Milestone 1 is frozen.** With `MILESTONE1_RULES` the new code repeats the
  old behaviour exactly (`tests/test_baseline.py`).

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

Milestone 2 settings (all whole numbers; see `genesis/config.py`):
`rest_below` (30), `rest_resume` (70), `rest_gain` (3), `rest_drain_units`
(1), `drain_units_per_energy` (2), `tire_base` (100), `tire_span` (100),
`tire_scale` (100), `turn_chance` (15), `turn_span` (20),
`trait_founder_min` (40), `trait_founder_max` (60), `trait_mutation` (5).
`--set rest_below=0` switches resting off.

Milestone 3 settings: `home_radius` (6). How far from home a wandering agent
may drift; `--set home_radius=0` switches homes off (Milestone 2 behaviour).
`home_inherit` (0): `1` gives a child its parent's home instead of the
tile where it was born (the "family home"; measured, off by default).
`memory_keep` (10): how many agents each agent remembers meeting; `0` = no
memory. `share_min_meetings` (2): how many meetings it takes before an agent
gives food to that agent when it is starving; `0` = no sharing.

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
3. **Give** 1 food if it is not hungry, carries food, and an agent it has met
   at least twice stands next to it starving (energy 20 or less, empty pack).
4. **Gather** if there is food on its tile and room in its pack.
5. **Rest** if it is not hungry (energy above 80) and tired (rest below 30);
   it keeps resting until rest reaches 70. Resting costs half the energy.
6. **Move** toward the nearest food it can *walk to* (around water), or
   wander if there is none. Food it cannot reach is ignored. A wandering
   agent more than 6 tiles from its **home** (where it was born) steps back
   toward home instead.

After everyone has acted, each agent notes whom it is standing next to (within
1 tile): its **memory** of up to 10 agents, with how many separate times it
met each one, when, and where. When the list is full it forgets the agent it
met least. Only the Give rule reads this memory.

Each agent has two **traits** (0 to 100, 50 = average), made at birth from
its own seeded dice and inherited by children (parent's value +/- 5):

- **Industriousness**: how fast it tires while moving (lazy agents rest
  about twice as often as hard-working ones).
- **Curiosity**: how often a wandering agent turns (7% of wandering ticks at
  10, 15% at 50, 23% at 90). High curiosity means zigzagging and searching
  the nearby patch thoroughly, not exploring further. Measured: when
  high- and low-curiosity families share a world, the high ones usually end
  up with more descendants (`docs/MILESTONE2_REPORT.md`).

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
| `genesis/needs.py` | The rest need: when to rest, resting, tiring |
| `genesis/traits.py` | Curiosity and industriousness: dice, inheritance, effects |
| `genesis/memory.py` | Encounter memory: who met whom, when, where, how often |
| `genesis/digest.py` | Behaviour-only codes used to prove Milestone 1 is unchanged |
| `genesis/sim.py` | One tick of time (`step`) |
| `genesis/save.py` | Save, load, fingerprint; repairs older saves |
| `genesis/history.py` | Each agent's recent decisions, stored in the world and saves |
| `genesis/overrides.py` | The checks behind `--set` |
| `genesis/summary.py` | The report behind `--summary` |
| `genesis/rng.py` | The dice. One number, so saves can store it |
| `genesis/whylog.py` | Turns decision records into readable text |
| `run_headless.py` | Run with no page |
| `why.py` | Show the last decisions of one agent |
| `server.py` | Runs the world and serves the page |
| `web/` | The page. It only draws; no rules live there |
| `tests/` | The automatic checks |
| `experiments/` | Measurement scripts (they only read the world); results in `experiments/results/`. `regrow_sweep.py`, `starvation_study.py`, `stage_compare.py`, `curiosity_probe.py`, `trait_drift.py`, `encounter_probe.py`, `memory_probe.py`, `sharing_opportunity.py`, `sharing_probe.py`, `community_probe.py` (add `--endings` for why groups end), `home_drift.py`; `baseline/` holds the frozen Milestone 1, Milestone 2 and homes references |
| `VISION.md` | The long-term idea and roadmap (read first) |
| `docs/MILESTONE3.md` | Milestone 3: homes, encounter memory, sharing (built), groups (measured), family home (built, off), with results |
| `docs/MILESTONE2_REPORT.md` | What Milestone 2 does, measured |
| `docs/MILESTONE2_V2.md` | The Milestone 2 design as built |
| `docs/STARVATION.md` | Why about two thirds of deaths are starvation |
| `docs/MILESTONE2.md`, `docs/MILESTONE2_REVIEW.md` | The first proposal and its review (history) |
| `STATUS.md` | What works right now, and what to do next |

The `genesis/` folder never touches the page or the server. That is what
lets the tests run it with no UI.

## Things to try

Open `genesis/config.py`, change one number, start a new world:

- `regrow_per_tick` (default 6): more food growing means a bigger population.
- `vision`: how far agents see food.
- `repro_cooldown`: lower it and watch a baby boom, then a famine.
- `--set tire_base=200`: everyone tires twice as fast and rests more.
- `--set rest_below=0`: nobody rests (Milestone 1 behaviour for rest).
- `--set home_radius=2`: agents cling to their birthplace; `0`: they roam freely.
- `--set share_min_meetings=0`: nobody shares; `5`: only with agents met 5+ times.
- `--set home_inherit=1`: families keep one home forever (tighter, more
  family-like groups; a little more starvation).
