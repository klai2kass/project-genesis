# Milestone 3: memory of places and individuals

Goal (from `VISION.md`): agents remember places and individuals, so that
relationships can later grow out of repeated contact, not out of a script.
Built one small step at a time, each measured before the next.

| Step | What | Status |
| --- | --- | --- |
| 1 | **Home**: every agent remembers where it was born and wanders near it | **Built** (this file) |
| 2 | **Encounter memory**: who did I meet, where, when, how often (record only) | Next, not started |
| later | Anything that USES that memory (recognition, preferring kin, ...) | Only with evidence |

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
