# Milestone 3: memory of places and individuals

Goal (from `VISION.md`): agents remember places and individuals, so that
relationships can later grow out of repeated contact, not out of a script.
Built one small step at a time, each measured before the next.

| Step | What | Status |
| --- | --- | --- |
| 1 | **Home**: every agent remembers where it was born and wanders near it | **Built** (this file) |
| 2 | **Encounter memory**: who did I meet, where, when, how often (record only) | **Built** (below) |
| 3 | First USE of that memory: share food with a starving agent you know | **Built** (below) |
| 4 | Look for groups in the memory network (measurement only) | Proposed (`STATUS.md`) |

## Step 1: home (built 2026-11-17)

### Why this step first

Measured before building (`experiments/encounter_probe.py`, details in
`docs/MILESTONE2_REPORT.md` section 6 and `STATUS.md`): with the Milestone 2
rules an agent drifts over an area about 11 tiles across and meets about 38
different agents in its life, mostly strangers. Only 7% of pairs ever meet
again after 100 ticks apart and only 6% of meetings are between family. A
memory of individuals would have almost nothing to recognise. A prototype
"home" doubled family meetings without changing survival, so it was built.

### The rule (whole numbers, no dice)

- Every agent has `home = [x, y]`: the tile where it was born. Founders: the
  tile where they were placed. It never changes.
- Setting `home_radius` (default **6**; `0` = homes off).
- Only when the agent **wanders** (no reachable food in sight, or its pack is
  full and it is not hungry), and only if it is more than `home_radius` steps
  from home (a step = one of 8 directions, so distance =
  `max(|dx|, |dy|)`), it takes the land step that brings it closest to home:
  smallest `max(|dx|, |dy|)`, then smallest `|dx| + |dy|`, then the first
  direction in the fixed order N, NE, E, SE, S, SW, W, NW.
- If no step gets it closer (water in the way), it wanders as before.
- Eating, reproducing, gathering, resting and walking to food it can see
  come first and are unchanged. Homes never override hunger.
- Heading home makes no dice draw (a normal wander step makes one), so the
  world's dice and everything after differ once anyone heads home. That is
  intended and is why the check below exists.
- The "why" says so: `... searching; I am 8 tiles from home (55, 6) and stay
  within 6, so heading home`.

Code: `genesis/agents.py` (`_home_distance`, `_step_home`, `_wander`),
`genesis/world.py` (`home` field, save version 4), `genesis/config.py` and
`genesis/overrides.py` (`home_radius`).

### Saves

Save format **4**. A version 3 (or older) save loads with `home_radius = 0`
and every living agent's home set to where it stands now (birthplaces were
never recorded before). So an old world continues exactly as before, and the
migration log says so. To try homes on an old world: `--set home_radius=6`.

### What guards the old behaviour (tests)

- `experiments/baseline/milestone2.json` (new, frozen before homes were
  written): counters, behaviour digest and event digest of seeds 42, 1, 2
  after 500 ticks, and a v3 save (`tests/fixtures/save_v3_seed42_t300.json`)
  continued 200 ticks. `tests/test_home.py` checks that `home_radius = 0`
  reproduces all of it exactly.
- The Milestone 1 baseline is unchanged (`MILESTONE1_RULES` now also sets
  `home_radius = 0`); `make_baseline.py --check` says ALL SAME.
- `tests/test_home.py` (12 tests): homes off = Milestone 2; homes on changes
  behaviour; v3 and v2 saves migrate; founders' and children's homes; home
  survives save and load; a far agent walks straight home, then stays within
  one step of the radius; homes off never mention home; food in sight,
  gathering, eating and resting all beat home; a wall of water falls back to
  wandering; same seed = same world.

### The page

Click an agent: its home is a gold square on the map, with a dashed box for
the area it wanders in, and the panel says where home is and how far away it
is ("homes are off in this world" for old saves).

### Results

All FACT, measured 2026-11-17 with the real code (no prototype). Re-run with
the commands in `STATUS.md`; raw output in `experiments/results/`.

**Did it work? Yes, on every success line set before building.**
(`encounter_probe.py`, 5 seeds x 3,000 ticks, counted after tick 500;
meeting = within 1 tile; family = parent/child or same parent.)

| | homes off (Milestone 2) | **home_radius 6 (default)** | home_radius 3 | target for radius 6 |
| --- | --- | --- | --- | --- |
| meetings that are family | 6.0% | **13.0%** | 20.0% | 12%+ (double) |
| pairs that meet 5+ times | 8.5% | **21.1%** | 26.6% | 17%+ (double) |
| pairs that meet again after 100+ ticks apart | 7.3% | 13.5% | 11.7% | |
| different agents met in a life | 38.3 | 25.0 | 19.4 | |
| area an agent covers (radius, tiles) | 11.0 | 5.2 | 3.7 | |
| meetings per agent per 100 ticks | 29.7 | 27.8 | 26.2 | |
| population after tick 500 | 93.0 | 93.1 | 93.4 | 80-98 |
| starved % of deaths | 66.5 | 65.4 | 66.1 | 62-73 |
| births | 946 | 931 | 947 | 830-1,010 |

The real rule gives the same numbers as the prototype tested beforehand
(for example family 13.0% against 13.1%, 5+ meetings 21.1% against 21.5%).

**Milestone 2 bands** (`stage_compare.py`, 5 seeds, file
`stage_compare_home.txt`): with homes on, population 93.1, births 931,
starved 65.4%, age at death 304, nobody died out; all inside the bands.
Distinct tiles visited per 100 ticks fell from 63.5 to 44.4 (agents walk
over the same ground more). Resting 8.6% of decisions (8.7% before). Speed
unchanged (about 490 ticks per second in that run, both with homes on and off).

Plain reading: agents now live in neighbourhoods. An agent meets fewer
different agents, but the same ones again and again, and twice as many of
its meetings are with family. Nobody is worse fed for it.

**Side effect: curiosity's advantage mostly disappears.** In Milestone 2,
high-curiosity families out-bred low ones in mixed worlds (34 of 40 seeds,
`docs/MILESTONE2_REPORT.md`). With homes on (`curiosity_probe.py`, files
`curiosity_probe_home.txt` and `curiosity_mixed_extra_home.txt`):

| mixed worlds, alive at tick 3,000 | low (10) | neutral (50) | high (90) | high beat low |
| --- | --- | --- | --- | --- |
| seeds 42, 1-9 | 21.1 | 33.0 | 38.3 | 7 of 10 |
| seeds 10-39 | 29.2 | 29.2 | 35.2 | 18 of 30 |

Together 25 of 40, which luck alone produces about 15% of the time: no
longer a clear effect. Curiosity still changes how agents walk (direction
changes 21.9% / 27.3% / 32.8% in every seed) but no longer how far they get
(distance per 100 ticks 6.7 / 6.8 / 6.8), because the home holds everyone
near the same patch. This supports the Milestone 2 guess that zigzaggers won
by staying near their food patch: homes now give everyone that benefit.
(Forced worlds: as before, no difference in population or starvation.)

What this means for curiosity: as a turning rate it now does almost
nothing that matters. The natural fix is the one suggested in the
Milestone 2 report: let curiosity set how far from home an agent roams
(a per-agent radius around the default 6). That is a design choice for the
owner, listed in `STATUS.md`; nothing was changed.

**Limitations:** one map size, 3,000 ticks, 5 seeds for the encounter
numbers. "Family" counts only parent/child and siblings, not grandparents or
cousins. Agents behind a lake from their home wander normally at the lake
shore (tested in a small world; how often it happens in real maps was not
measured). Homes are fixed for life; an agent born in a poor spot stays
tied to it.

## Step 2: encounter memory (built 2026-11-17)

### Why

Homes made repeated contact common (21% of pairs meet 5+ times, 13% of
meetings are family; step 1 results). A memory now has something to keep.
It is a **record only**: nothing reads it yet, so behaviour cannot change.

### The rule (whole numbers, no dice; `genesis/memory.py`)

- A **meeting**: two living agents within 1 tile of each other (the 8 tiles
  around, or the same tile) at the end of a tick. While they stay that close
  it is one meeting; walking apart and coming back is a new one.
- Each agent keeps `memory`: entries `[id, first_tick, last_tick, meetings,
  x, y]` (x, y = where it stood when the latest meeting began).
- At most `memory_keep` entries (default **10**; 0 = off). When full it
  forgets the agent it met the **fewest** times (ties: met longest ago, then
  lower id), never one it is meeting right now unless all of them are.
- Updated once per tick in `sim.step`, after every agent has acted.
- Save format **5**; older saves start with empty memories (logged).

### Why "forget the least-met" (measured, not guessed)

The first version forgot whoever was met longest ago. Measuring it against
the same world with unlimited memory (memory never changes behaviour, so
the two runs are identical except for what is remembered;
`experiments/memory_probe.py`, 5 seeds x 3,000 ticks, adults = alive at the
end and 200+ ticks old):

| | forget met-longest-ago (first try) | **forget least-met (built)** |
| --- | --- | --- |
| agents met 5+ times that are still remembered | 49.8% | **76.0%** |
| adults remembering someone met 5+ times | 80.3% | **99.6%** |
| meetings with its most-met agent | 8.1 | **11.0** |
| living parent/siblings met, still remembered | 68.6% | **72.2%** |
| remembered agents that are family | 11.1% | 12.2% |

The first rule also reset a friend's count to 1 whenever it was forgotten
and met again, which is why its "most-met" numbers are lower. Re-run both:
`python3 experiments/memory_probe.py` and `... --old-drop-rule`.

### What an adult remembers (FACT, `memory_probe.txt`)

An adult has met about 31 different agents so far and remembers 10 (98% of
adults have a full memory). Its most-met agent: about 11 meetings. On
average it has met 7.4 agents 5+ times, and keeps 76% of them. About one
remembered agent in eight is family.

### Cost

Speed: 6% to 13% slower depending on how it is timed: 6% in
`memory_probe.py` (5 seeds x 3,000 ticks: 376 against 400 ticks per
second), 11-13% in a seed 42, 2,000-tick timing (best of 3 runs: 4.02 s
against 3.60 s). A faster meeting search did not change it; the cost is
updating about 80 meetings per tick. Around the 10% aimed for; acceptable
at this size. Save size: about +2.5% (1,128 KB against 1,101 KB at tick
3,000; the decision history is still most of a save).

### Tests (`tests/test_memory.py`, 11)

Memory on and off both reproduce the frozen homes world
(`experiments/baseline/milestone3_home.json`, seeds 42/1/2) exactly; a v4
save (`tests/fixtures/save_v4_seed42_t300.json`) migrates and continues
exactly; a meeting is counted once while it lasts and again after a gap;
same tile counts, 2 tiles apart does not; the cap keeps a friend over a
stranger; ties drop the one met longest ago, then the lower id; memory off
records nothing; strongest-first order; every count equals an independent
all-pairs count over 300 ticks (no cap); memory survives save and load and
the world continues identically.

### The page

Click an agent: "Knows 10 agents (remembers up to 10). Met most:" and the
top 5 with meetings, last tick, place, "(parent)", "(child)" or "(sibling)"
where the world still knows it, and "has died".

### Does memory have anything to do? (evidence for step 3)

`experiments/sharing_opportunity.py` (5 seeds x 3,000 ticks, after tick 500,
2,328 starvation deaths): a "giver" is an agent that is not hungry and
carries food, standing within 1 tile.

| | starving agent-ticks with a giver near | starvation deaths with a giver near in their last 20 ticks |
| --- | --- | --- |
| giver is anyone | 6.1% | **33.7%** |
| giver met it 2+ times before | 3.4% | **19.4%** |
| giver met it 5+ times | 1.3% | 8.0% |
| giver is family (parent, child, sibling) | 0.7% | 4.6% |

(Standing next to someone is itself a meeting, so "the giver remembers it
at all" is always true and is not a useful line; "2+ times" means at least
one earlier, separate meeting.)

Plain reading: one starvation death in three happens to an agent that, in
its last 20 ticks, stood next to a well-fed agent with food in its pack. In
one death in five, that agent had met it before. Family alone is much rarer
(under 5%), so a rule based on "someone I know" reaches about four times as
many cases as one based on family. This is the concrete reason behind the
proposed step 3 in `STATUS.md`.

### Limitations

- "Family" on the page and in the probe is only parent, child and sibling
  while the relative is alive (the dead's parents are not kept).
- Memory is per agent; when an agent dies its memory goes with it.
- Speed cost is around the 10% I aimed for (6-13% depending on timing).

## Step 3: sharing food with someone you know (built 2026-11-18)

### Why

Evidence from step 2: one starvation death in three happened next to a
well-fed agent carrying food, and in one in five that agent had met the
starving one before. It is the first rule that READS memory.

### The rule (whole numbers, no dice; `genesis/agents.py`, `who_to_help`)

- New action **give**, checked after eat and reproduce, before gather, rest
  and move.
- Fits when the agent is not hungry (energy above 80), carries food, and an
  agent within 1 tile is **starving** (energy 20 or less, empty pack) and has
  `share_min_meetings` (default **2**) or more meetings in its memory.
- Several fit: the one met most often, then the lowest energy, then the
  lowest id. Never one that already died this tick.
- 1 food moves from pack to pack; the receiver eats it with its own eat rule
  (the same tick if it acts later, otherwise the next).
- Memory entries now also count food given and received
  (`[id, first, last, meetings, x, y, gave, got]`); `stats.gifts` counts all.
- The why: "gave 1 food to #60 (we have met 4 times); it is starving (energy
  20, empty pack) and I am not hungry (energy 93)".
- Save format **6**: older saves load with `share_min_meetings = 0`, so they
  keep their behaviour; old memory entries get gift counts 0.

### Tests (`tests/test_sharing.py`, 9)

`share_min_meetings = 0` reproduces the frozen memory world
(`experiments/baseline/milestone3_memory.json`) exactly; a v5 save
(`tests/fixtures/save_v5_seed42_t300.json`) migrates and continues exactly;
sharing on changes behaviour and gifts happen; one gift moves exactly 1 food
and both memories count it; gives only when not hungry, only to a starving
agent within 1 tile met enough times (each condition tested on its edge);
eat and reproduce come first; the choice order; never to an agent that died
this tick; same seed = same world and save/load continues identically.

### Results (FACT, `experiments/sharing_probe.py`, 5 seeds x 3,000 ticks)

| | no sharing | **met 2+ (default)** | met 5+ | Milestone 2 band |
| --- | --- | --- | --- | --- |
| population after tick 500 | 93.1 | 93.6 | 92.9 | 80-98 |
| births | 931 | 894 | 916 | 830-1,010 |
| starved % of deaths | 65.4 | **62.9** | 63.3 | 62-73 |
| age at death | 304 | **319** | 309 | 265-325 |
| gifts per run (3,000 ticks) | 0 | 187 | 83 | |
| different giver-receiver pairs | 0 | 170 | 77 | |
| gifts to family | | 16% | 23% | |
| receivers alive 20 ticks later | | 98% | 97% | |
| givers starved within 100 ticks | | 2.6% | 1.2% | |
| gifts ever returned (b gave back to a) | | **0%** | **0%** | |
| starvation deaths aged 0-79 | 25.5% | 23.7% | 26.0% | |

(sd over seeds: starved share 0.8 points, age at death 2-3 ticks, births
4-16, so the changes in those three lines are larger than luck.)

**Plain reading:**
- Sharing works as a rescue: 98% of receivers are still alive 20 ticks
  later, and givers almost never starve because of it.
- The world gets a little kinder but not bigger: the starved share drops
  by 2.5 points and agents live 15 ticks longer on average, while there are
  about 4% fewer births and the population stays the same. GUESS: giving
  away food keeps givers below the energy of 90 needed for a child a little
  more often; food, not finding food, still sets how many can live
  (`docs/STARVATION.md`).
- **No exchange emerged.** In about 935 gifts over 5 runs, not one went back
  the other way. Givers and receivers are mostly different agents (in seeds
  42 and 1, only 6 of 132 and 7 of 154 receivers ever gave food to anyone
  later).
  Help flows one way, from agents doing well to agents in trouble. The rule
  never looks at past gifts, so the only way help could come back is by the
  same two agents swapping roles, and that practically never happens.
- Fewer gifts than I hoped: 187 per run against "a few hundred" I set as a
  target. Still enough to measure.
- Both band lines sit near an edge (starved 62.9 against a floor of 62; age
  319 against a ceiling of 325). All bands still hold.

### Limitations

- 5 seeds, one map, 3,000 ticks.
- "Starving" is a fixed line (energy 20); no trait affects giving.
- Gifts are counted in memory only while both still remember each other.
- The family share uses parent/child/sibling only.

