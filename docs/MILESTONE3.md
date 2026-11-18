# Milestone 3: memory of places and individuals

Goal (from `VISION.md`): agents remember places and individuals, so that
relationships can later grow out of repeated contact, not out of a script.
Built one small step at a time, each measured before the next.

| Step | What | Status |
| --- | --- | --- |
| 1 | **Home**: every agent remembers where it was born and wanders near it | **Built** (this file) |
| 2 | **Encounter memory**: who did I meet, where, when, how often (record only) | **Built** (below) |
| 3 | First USE of that memory: share food with a starving agent you know | **Built** (below) |
| 4 | Look for groups in the memory network (measurement only) | **Done** (below) |
| 5 | Family home: a child takes its parent's home | **Built, OFF by default**: it did not make groups last longer |
| 6 | Why do groups end? (measurement only) | **Done** (below): the memory cap |
| 7 | Fading memory: forget friends you stop meeting | **Built, OFF by default**: no fade time gave groups that both last and stay local |
| 8 | Are there tight local cores inside the big groups? (measurement only) | **Done** (below): tight circles exist but never last |
| 9 | Rest at home: a tired agent walks home before resting | Proposed (`STATUS.md`) |

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

## Step 4: are there groups? (measured 2026-11-18, no rule changed)

### How

`experiments/community_probe.py` (read-only), 5 seeds x 3,000 ticks, default
world (homes, memory, sharing on) against the same world with homes off.
Every 250 ticks from tick 500 it builds a network from the agents' own
memories: a **tie** when two living agents BOTH remember K or more meetings
with each other, and a **group** = 3 or more agents connected by ties.

### Results (FACT, `experiments/results/community_probe.txt`)

With K = 5 (know each other well):

| | homes on (default) | homes off (control) |
| --- | --- | --- |
| living agents in a group | **58%** | 33% |
| groups per snapshot | 7.0 | 5.7 |
| group size, mean (biggest) | 7.7 (18) | 5.4 (11) |
| ties inside groups that are family | **19%** | 9% |
| how spread out members' homes are | **5.7 tiles** | 13.3 tiles |
| members still together 250 ticks later | 69% | 54% |
| how long a group can be traced | 225 ticks | 110 ticks |
| groups traced 1,000+ ticks (about 3 lifetimes) | **6.3%** | 0.4% |
| of those, every first member has died | 100% | |
| gifts made inside a group | 31% | 6% |
| pairs met 2+ times that lie inside a group | 51% | 24% |

(sd over seeds 0.2 to 2.6 on most lines; traced ticks 54 and 18.)

With K = 2 (met twice) almost everyone (94%) is one big connected network,
with or without homes: weak ties connect the whole world, so K = 2 says
nothing about groups.

### Plain reading

- **Groups exist.** More than half of all agents belong to a group of agents
  who know each other well. They are local (homes within about 6 tiles),
  about one tie in five is family, and they are twice as common with homes
  as without.
- **Most groups are short-lived.** A group can be followed for about 225
  ticks on average, less than one lifetime (about 310 ticks).
- **A few groups outlive everyone who started them** (6.3%, against 0.4%
  without homes): new members join while the first ones die. These are the
  first signs of something like a village. Rare, but clearly not chance.
- **Sharing does not stay inside groups.** Only 31% of gifts are between
  group members, although 51% of the pairs that could give are inside a
  group. Help goes more to agents at the edge of groups. GUESS: group
  members are the settled, well-fed agents; the starving ones are mostly
  newcomers and outsiders. Not measured.

### Why groups dissolve (`experiments/home_drift.py`)

A child's home is the tile where it was born, next to wherever the parent
happened to stand. So a family's home moves about 5.3 tiles every generation
(5.2 to 5.6 over 5 seeds) and after 10+ generations it is 14 to 19 tiles from
the founder's home. A group tied to one place cannot last when its families'
homes keep drifting apart. This is the evidence behind the proposed step 5.

### Limitations

- "Group" depends on the definition (mutual ties, K = 5, connected); other
  definitions (for example cliques) were not tried.
- With memory capped at 10, an agent cannot have more than 10 ties.
- The trace rule (follow the later group holding at least half of the
  surviving members) is one reasonable choice, not the only one.

## Step 5: the family home (built 2026-11-18, then switched off by default)

### The rule

Setting `home_inherit`: 1 = a newborn's home is a copy of its parent's
home, so every descendant keeps its founder's home; 0 = the home is the
tile where it was born (the step 1 rule). No dice. Save format **7**: older
saves load with 0. Code: `genesis/sim.py` (reproduce), `genesis/config.py`.

### What it was meant to do

Step 4 found that a family's home drifts about 5 tiles per generation, and
guessed that this pulls groups apart. Success line, set before building:
groups traced 1,000+ ticks clearly above 6.3%, and the Milestone 2 bands
hold.

### Results (FACT, `experiments/community_probe.py` and `home_drift.py`,
5 seeds x 3,000 ticks)

| | family home (`home_inherit=1`) | birth-tile home (`0`) | homes off |
| --- | --- | --- | --- |
| a family's home after 10+ generations, from the founder's | **0 tiles** | 14-19 tiles | |
| agents in a group (K = 5) | 57.5% | 58.1% | 32.7% |
| groups per snapshot (size) | 7.9 (6.7) | 7.0 (7.7) | 5.7 (5.4) |
| family ties inside groups | **24.0%** | 18.6% | 8.8% |
| members' homes spread | **3.3 tiles** | 5.7 tiles | 13.3 tiles |
| members still together 250 ticks later | 72.7% | 69.0% | 54.4% |
| how long a group can be traced | 248 +/- 76 ticks | 225 +/- 54 | 110 +/- 18 |
| **groups traced 1,000+ ticks** | **6.1% +/- 4.8** | **6.3% +/- 1.5** | 0.4% |
| starved % of deaths | 65.0 | 62.9 | 63.5 |
| age at death | 311 | 319 | 311 |
| population / births | 93.1 / 905 | 93.6 / 894 | 93.0 / 913 |
| gifts of food per run | 226 | 187 | 167 |

The birth-tile column is the same world as step 4 and gives exactly the
same numbers (a reproducibility check).

### Plain reading

- It does what it says: family homes no longer move.
- Groups become tighter and more family-like (homes 3.3 tiles apart, a
  quarter of ties are family), and more food is shared (226 gifts).
- **But groups do not last longer.** Groups traced 1,000+ ticks: 6.1%
  against 6.3%, well inside the luck range. The step 4 guess (drift is what
  ends groups) was wrong, or at least not the main reason.
- Life gets a little harder: starved share 65.0% against 62.9%, age at
  death 311 against 319 (families crowd one spot). Bands still hold.

### Decision

The success line was not met, so the family home stays in the code as a
setting but is **off by default** (`home_inherit = 0`): the normal world is
the step 3 world, unchanged. Try it with `--set home_inherit=1`. Owner can
switch the default (STATUS, decisions).

### Tests (`tests/test_home.py`, +4: 16 in that file)

`home_inherit = 0` reproduces the frozen sharing world
(`experiments/baseline/milestone3_share.json`) exactly; a v6 save
(`tests/fixtures/save_v6_seed42_t300.json`) migrates and continues
exactly; with 1, behaviour changes, every child's home equals its parent's
and every agent's home equals its founder's (600 ticks, generation 2+
checked); with 0, children's homes are their birth tiles.

## Step 6: why do groups end? (measured 2026-11-18, no rule changed)

### How

`python3 experiments/community_probe.py --endings` (5 seeds x 3,000 ticks,
K = 5). Every group that starts at least 1,000 ticks before the end is
followed (step 4 trace) until it ends, and the ending is classified:
- **members died**: fewer than 2 of its members are alive at the next
  snapshot;
- **split**: most survivors are still in groups, but no single group holds
  half of them;
- **dissolved**: most survivors are in no group any more (a tie between two
  living agents only breaks when one forgets the other, or when the members
  linking them die);
- **still going** when the run ends.
Also: at what age agents first appear in a group (checked every 50 ticks),
and how often a full memory forgets an agent met 5+ times (counted inside
the memory's own forgetting step, without changing it). Four worlds: the
default, the family home, and the default with `memory_keep` 20 and 1000.

### Results (FACT, `experiments/results/community_endings.txt` and `.json`)

| | default (memory 10) | family home | memory 20 | memory 1000 |
| --- | --- | --- | --- | --- |
| 5+-meeting friends forgotten per 1,000 ticks | **211** | 288 | **2** | 0 |
| groups traced 1,000+ ticks | **6.3%** | 6.1% | **54%** | 71% |
| how long a group can be traced | 225 ticks | 248 | 997 | 1,317 |
| ended: members died | 55% | 61% | 21% | 21% |
| ended: split | 28% | 19% | 46% | 17% |
| ended: dissolved | 15% | 19% | 0% | 1% |
| still going at the end of the run | 1% | 1% | 32% | 61% |
| agents in a group | 58% | 58% | 72% | 72% |
| groups per snapshot | 7.0 | 7.9 | 3.1 | 2.5 |
| group size (biggest) | 7.7 (18) | 6.7 (15) | 21.9 (50) | 27.1 (55) |
| members' homes spread | 5.7 tiles | 3.3 | 9.0 | 10.3 |
| family ties inside groups | 19% | 24% | 16% | 16% |
| adults that ever join a group | 96% | 97% | 99.6% | 99.5% |
| age when first in a group | 148 | 146 | 124 | 122 |
| starved % / age at death | 62.9 / 319 | 65.0 / 311 | 62.5 / 321 | 62.5 / 318 |
| gifts of food per run | 187 | 226 | 217 | 233 |

(sd over seeds is large for the ending shares, 10 to 38 points, because each
seed has only a few dozen groups; the forgetting and lasting lines differ
between worlds far more than their spread, which is at most 47 for
forgetting and 16 for lasting.)

### Plain reading

- **The memory cap is the main reason groups do not last.** With room for
  10, an agent keeps forgetting friends: about 210 friendships of 5+
  meetings are forgotten every 1,000 ticks across the world. With room for
  20, almost none are (2), and groups last: 54% run for 1,000+ ticks
  instead of 6%.
- **But lasting groups become very large.** With memory 20 there are only
  about 3 groups, the biggest holding about half the world, with homes 9
  tiles apart. Once nothing is forgotten, everyone who ever met someone
  five times stays linked forever, so groups merge into regions. That is
  not a village either.
- So the small groups of the default world are small partly BECAUSE agents
  forget, and the big groups of the memory-20 world last only because they
  never forget. Neither is "a local group of agents who keep meeting".
- The family home makes no difference to any of this (as in step 5).
- All Milestone 2 bands hold in every world (age at death 321 with memory
  20 is close to the 325 ceiling).

### What this points to

Memory today forgets by **space** (a full list drops the least-met), never
by **time**. A friend met 30 times long ago stays "close" forever, unless
the list overflows. Real ties fade when people stop meeting. The proposed
step 7 (`STATUS.md`) tests exactly that: forget an agent not met for a
while, with room for 20.

### Limitations

- Ending shares vary a lot between seeds (few groups per seed).
- "Group" is still one definition (mutual 5+ ties, connected).
- The memory 20 and 1000 worlds also change sharing a little (more agents
  are "known"), so they are not memory-only comparisons.

## Step 7: fading memory (built 2026-11-18, then left OFF by default)

### The rule (whole numbers, no dice; `genesis/memory.py`, `_fade`)

Setting `memory_fade` (0 = off). Every tick, after meetings are noted and
before a full list is trimmed, every living agent forgets each agent it has
not been within 1 tile of for MORE than `memory_fade` ticks
(`tick - last_tick > memory_fade`). A full list still drops the least-met.
Save version 8: an older save gets `memory_fade` 0 and, if it has none,
`memory_keep` 10, so it keeps its old rules (logged).

### What it was meant to do (section "What this points to" of step 6)

Keep ties to agents you keep meeting, drop the others, so that groups last
(as with room for 20) but stay local (as with room for 10).
Success line, written before measuring: groups traced 1,000+ ticks 25% or
more, AND home spread at most about 6 tiles, AND the biggest group well
under half the world (about 47), AND the Milestone 2 bands hold.

### Results (FACT, `experiments/results/community_fading.txt` and `.json`)

`python3 experiments/community_probe.py --fading`, 5 seeds x 3,000 ticks,
K = 5. All worlds use today's other defaults. Fade 75 was added after a
quick 2-seed run showed that 300 and 600 change little (agents live about
310 ticks, so they die before a friend fades).

| | memory 10, no fade (default) | memory 20, no fade | 20, fade 75 | 20, fade 150 | 20, fade 300 | 20, fade 600 |
| --- | --- | --- | --- | --- | --- | --- |
| groups traced 1,000+ ticks | 6.3% | 54% | 11% | 44% (sd 28) | 60% | 54% |
| home spread in a group | 5.7 tiles | 9.0 | **5.0** | 7.7 | 8.5 | 9.0 |
| biggest group (of about 93) | 18 | 50 | **15** | 38 | 48 | 50 |
| groups per snapshot | 7.0 | 3.1 | 8.2 | 4.5 | 3.4 | 3.1 |
| living close friends faded / 1,000 ticks | 0 | 0 | 516 | 154 | 10 | 0 |
| close friends dropped by a full list / 1,000 ticks | 211 | 2 | 0 | 0.1 | 0.5 | 2 |
| starved % / age at death | 62.9 / 319 | 62.5 / 321 | 62.7 / 320 | 63.8 / 316 | 63.1 / 320 | 62.5 / 321 |
| gifts of food per run | 187 | 217 | 205 | 221 | 214 | 217 |

Fade 600 gives exactly the memory-20 world (nobody lives long enough to
fade). All bands hold everywhere. Speed: 3.29 s per 1,500 ticks with fade
150 and room for 20, against 2.93 s today (+12%).

### Plain reading

- **No fade time meets the success line.** Short fading (75) keeps groups
  small and local, but they do not last (11%). Longer fading (150 and up)
  lets them last, but they grow into regional groups again.
- Fading and the memory size move the world along **the same line**:
  every setting so far that makes groups last also makes them big. A tie
  is broken either by forgetting or not at all; there is no setting where
  neighbours keep their ties and far-away groups stay apart.
- Likely reason (reasoned from the code, not yet measured): a group is any
  chain of ties (a friend of a friend of a friend ...). Agents spread over
  the whole land, homes sit next to each other and neighbours really do
  keep meeting, so one chain of real ties can link neighbourhood to
  neighbourhood. Big groups may then be many local cores joined by a few
  links, and "lasting" may partly mean "big enough to survive deaths".

### Decision

Same as the family home: **built, tested, left OFF** (`memory_fade` 0,
`memory_keep` 10), so today's default world is unchanged (it still
reproduces `experiments/baseline/milestone3_family.json`). Try it with
`--set memory_fade=150 --set memory_keep=20`. Whether to switch it on is in
`STATUS.md`, decisions.

### Tests (`tests/test_fading.py`, 10)

Fade off + memory 10 reproduces the frozen step 6 world (events, behaviour
and every memory, 3 seeds); a v7 save migrates with the old rules and
continues exactly; a v4 save gets memory 10 and no fading; an entry is kept
at exactly `memory_fade` ticks and forgotten one tick later (both sides);
meeting again in time keeps and counts it; fade 0 never forgets; a full
list still drops the least-met; the setting is accepted by `--set` and
negative values are refused; in a real world nobody remembers anyone older
than the fade; same seed = same world.

### Limitations

- One group definition again (mutual 5+ ties, chained). Step 8 checks
  whether a stricter one shows lasting local cores.
- The sd of "lasting" for fade 150 and 300 is large (23 to 28 points).
- Fading also changes who is "known" for sharing; gifts change by up to 34
  per run, starvation by at most 1 point.

## Step 8: tight circles inside the big groups (measured 2026-11-18, no rule changed)

### How

`python3 experiments/community_probe.py --cores` (snapshots every 250
ticks, as in steps 4 to 7) and `--cores --every 50` (every 50 ticks), 5
seeds x 3,000 ticks. Same tie as before (both agents remember 5+ meetings
with each other), but stricter ways to form a group:

- **K5 core3**: keep only agents with 3+ ties to other kept agents. (This
  was the plan. Reasoned from the definition, it cannot cut a lone tie
  between two dense neighbourhoods, so it can still chain; kept for
  comparison.)
- **K5 shared1 / shared2 / shared3** (added): keep a tie only if the two
  agents ALSO have 1 / 2 / 3+ friends in common (repeat until nothing
  changes). A lone bridge between neighbourhoods has no common friend and is
  cut. **shared2 = a "tight circle"** is the main view below.
- **K10**: the old chained group with a stricter tie (10+ meetings).

Five worlds: memory 10 (default); memory 20 with fade 150; memory 20 without
fading; and, added after a 2-seed trial found almost no tight circles, the
family home with memory 10 and with memory 20 + fade 150 (a family sharing
one home area should meet each other most).
The 50-tick run was added after the 250-tick run, because 250 ticks is
almost a lifetime (310): a circle whose members all change within 250 ticks
could not be followed at that gap.

### Results (FACT, `experiments/results/community_cores.txt` and
`community_cores_every50.txt`, `.json` beside them)

Tight circles (shared2), checked every 50 ticks:

| | memory 10 (default) | 20, fade 150 | 20, no fade | family home, 10 | family home, 20, fade 150 |
| --- | --- | --- | --- | --- | --- |
| living agents in a tight circle | 2.6% | 14% | 16% | 2.8% | **23%** |
| biggest circle (mean) | 2.1 | 5.9 | 6.2 | 2.1 | 7.1 |
| members' homes spread | 3.4 tiles | 4.1 | 4.0 | 1.0 | **1.7** |
| how long a circle can be followed | 34 ticks | 56 | 73 | 38 | 90 |
| circles followed 1,000+ ticks | **0%** | **0%** | **0%** | **0%** | **0%** |
| ended: broke apart / members died | 96 / 4% | 99 / 1% | 98 / 2% | 92 / 8% | 98 / 2% |
| members of a big chained group (20+) that are in a tight circle | 6% | 20% | 23% | 5% | 31% |

The looser views agree: shared1 groups (one common friend) last 109 to 368
ticks on average and 0 to 8% reach 1,000 ticks; core3 and K10 groups never
do (at most 0.3%). At the 250-tick gap tight circles end mostly with "members
died" (71 to 77% in the memory-20 worlds), which only says that almost
all their members are gone 250 ticks later.

How often you look changes the old "lasting" line too (chained K5 groups,
traced 1,000+ ticks):

| | memory 10 | 20, fade 150 | 20, no fade | family home, 10 | family home, 20, fade 150 |
| --- | --- | --- | --- | --- | --- |
| checked every 250 ticks (steps 4 to 7) | 6.3% | 44% | 54% | 6.1% | 36% |
| checked every 50 ticks | 6.6% | **2.0%** | 25% | 11% | 25% |

All Milestone 2 bands hold in all five worlds (same world numbers as steps 5
to 7; this step only looks).

### Plain reading

- **The big groups are not made of lasting local communities.** Inside them
  only 6 to 31% of the members are in a tight circle, and every tight circle
  breaks up within about 35 to 90 ticks (a third of a lifetime or less).
  None, in any world, lasts 1,000 ticks.
- **Tight circles are real and very local**: 4 to 7 agents whose homes lie
  1 to 4 tiles apart. The family home with room for 20 makes the most of
  them (23% of agents, homes under 2 tiles apart).
- **They break apart; they do not just die out.** Reasoned from the code
  (not measured): a circle needs every pair to have met 5+ times, so when
  one member dies or drifts away, the others lose a common friend, and a
  circle of 4 to 7 falls below the rule. A newcomer needs 5 separate
  meetings with several members before it counts, and agents meet only by
  chance while wandering near home, so replacements come too slowly.
- **The "lasting" numbers of steps 4 to 7 depend on how often groups are
  checked.** Every 250 ticks hides short breaks; every 50 ticks catches
  them. The big drop for fade 150 (44% to 2%) means its groups split and
  re-form all the time. Memory 20 without fading and the family home with
  room for 20 are the steadiest (25% either way).

### What this points to

Nothing in the rules makes the SAME few agents meet again and again: they
meet only by chance near their homes. A small, non-social rule that would do
it: **rest at home**. A tired agent (rest below `rest_below`, not hungry)
walks home before resting. Agents with homes close together (a family, most
of all with the family home) would then rest beside each other, over and
over. Proposed as step 9 in `STATUS.md`.

### Limitations

- "Tight circle" is still one definition (shared2); shared1 and shared3 are
  reported beside it and point the same way.
- Tracing at 50 ticks is strict: a single 50-tick break ends the trace.
- The reason circles break is reasoned from the code, not measured
  directly.

