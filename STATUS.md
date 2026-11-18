# Project Genesis: status

Last checked: 2026-11-18, by running the commands in this file (not from memory).

**Milestones 1 and 2 are done. Milestone 3: steps 1 (home), 2 (memory) and
3 (sharing) are built and on; step 4 (groups) is measured; step 5 (family
home) is built but OFF by default, because it did not reach its goal**
(`docs/MILESTONE3.md`). **Step 6 (why groups end) is measured: the memory
cap.** **Step 7 (fading memory) is built but OFF by default: no fade time
gave groups that both last and stay local** (short fading: local but
short-lived; longer fading: lasting but regional, like room for 20).
Today's default world is unchanged. **Step 8 (tight circles) is measured:
small, very local circles of friends exist, but every one breaks up within
about 35 to 90 ticks; none lasts 1,000 ticks in any world.** Proposed next:
**step 9, rest at home** (a tired agent walks home before resting), section
5. GitHub (`origin/main`) has everything up to `af88e8a`; later
commits are local only.

Plain words: a **tick** is one step of time. A **seed** is the number a world
is built from (same seed = same world). A **fingerprint** is a short code that
is equal only when two worlds are exactly equal. **Headless** = no window.

## 1. What works today (checked this session)

- [x] World, food, agents that search (around water), gather, eat, rest,
      reproduce and die. Same seed = same world.
- [x] Rest need and traits (curiosity, industriousness), inherited +/-5.
- [x] **Homes**: `home` per agent (birth tile), `home_radius` 6 (0 = off).
- [x] **Encounter memory**: `memory` per agent, `memory_keep` 10 (0 = off);
      shown in the agent panel.
- [x] **Sharing**: action `give`, `share_min_meetings` 2 (0 = off); gifts
      shown in the panel and in the stats ("Food shared").
- [x] **Family home** (optional): `home_inherit` 0 by default, 1 = a child
      takes its parent's home. The panel says where a home comes from.
- [x] **Fading memory** (optional): `memory_fade` 0 by default (never
      fade); e.g. `--set memory_fade=150 --set memory_keep=20`. The panel
      says "forgets anyone not met for N ticks" when it is on.
- [x] Every decision has a "why"; recent decisions are kept in saves.
- [x] Saves version 8; versions 1 to 7 load and keep their old rules.
- [x] Milestone 1, Milestone 2, homes and memory behaviour frozen and
      reproduced exactly: `tests/test_baseline.py`, `tests/test_home.py`,
      `tests/test_memory.py`, `tests/test_sharing.py`, `tests/test_fading.py`,
      `experiments/baseline/make_baseline.py --check`.
- [x] Browser page, including the clicked agent's home and whom it knows
      (checked this session at http://127.0.0.1:8766, see 3).
- [x] Measurement scripts in `experiments/`, results in `experiments/results/`.
- [ ] `why.py --load` reads the stored history (it still replays instead).
- [ ] `--summary` does not report action mix or trait averages.

## 2. Tests (run this session)

`python3 -m unittest discover -s tests` -> `Ran 155 tests`, `OK` (about 1.6
minutes). By file: baseline 5, controls 11, determinism 7, fading 10,
history 8, home 16, memory 11, movement 7, overrides 11, rest 12, rest_design 14, save_load 10,
sharing 9, summary 5, trait_streams 5, traits 8, why_log 6.
Changed tests (on purpose): save-version checks now use `SAVE_VERSION`
instead of a fixed number; the curiosity turning test in `test_rest.py`
runs with `home_radius=0`; the memory tests switch sharing off to compare
with the frozen memory world; `test_why_log.py` knows the action "give".
`make_baseline.py --check` -> ALL SAME (Milestone 1 unchanged).
Reference run: `python3 run_headless.py --seed 42 --ticks 500 --every 0` ->
100 alive (homes on). Frozen references: `experiments/baseline/baseline.json`
(Milestone 1), `milestone2.json` (before homes), `milestone3_home.json`
(homes, before memory), `milestone3_memory.json` (memory, before sharing),
`milestone3_share.json` (sharing, before the family home),
`milestone3_family.json` (step 6 world, before fading memory, now also with
a code for every agent's memory; today's default world reproduces it
exactly).

## 3. Browser check (this session)

Server started from the shell on port 8766 (Claude's sandbox blocks ports,
so it ran outside the sandbox), page opened in the app's browser.
- Milestone 2 check: map, Play/Pause, Step, 20x, stats (resting now, average
  traits), agent panel (rest bar, traits, options, earlier decisions), Save
  then Load (back to tick 392, paused, "Loaded ..." message). No errors.
- Homes check (fresh tab): clicking agent #45 shows a gold square at its
  home (55, 6), a dashed box for its 6-tile area, and the line "Home (55, 6),
  where it was born · 6 tiles away · wanders within 6 tiles of it"; its
  earlier decisions include "... I am 7 tiles from home (55, 6) and stay
  within 6, so heading home". Legend has the new entry. **No console errors.**
- Memory check (fresh tab): clicking an agent shows "Knows 10 agents
  (remembers up to 10). Met most:" and a list such as "#231 · met 3 times,
  last at tick 664 near (26, 27)", with "has died" where right. **No console
  errors.**
- Fading check (step 7, fresh tab, default world): the panel still reads
  "Knows 10 agents (remembers up to 10). Met most:" (fading off); fed a
  fade of 150 it reads "... (remembers up to 20, forgets anyone not met for
  150 ticks)". Step works. (A first scripted try sent malformed requests
  and got 400 errors; after a reload, real clicks gave no errors.)
- Sharing check (fresh tab, tick 821): stats show "Food shared 71" and
  "Newest generation 7"; agent #111's list shows "met 15 times ... it gave
  me 1 food" and "met 10 times ... I gave it 1 food". **No console errors.**
Small things noticed (not fixed): the population graph starts empty after a
load (not stored in saves); the rest bar shows the value after this tick's
rest while the decision text shows the value at decision time. The test save
`saves/claude_browsercheck.json` is still in `saves/` (ignored by git).

## 4. Measured results

**Tight circles** (step 8, `experiments/community_probe.py --cores --every
50`; a tight circle = friends where every pair also has 2+ friends in
common, checked every 50 ticks):

| | memory 10 (default) | 20, fade 150 | 20, no fade | family home, 10 | family home, 20, fade 150 |
| --- | --- | --- | --- | --- | --- |
| agents in a tight circle | 2.6% | 14% | 16% | 2.8% | 23% |
| members' homes spread | 3.4 tiles | 4.1 | 4.0 | 1.0 | 1.7 |
| how long a circle lasts | 34 ticks | 56 | 73 | 38 | 90 |
| circles lasting 1,000+ ticks | 0% | 0% | 0% | 0% | 0% |
| ended by breaking apart | 96% | 99% | 98% | 92% | 98% |

The big groups are loose chains, not lasting local communities. Also: the
old "lasting" line depends on how often groups are checked (fade 150: 44%
when checked every 250 ticks, 2% every 50). Details:
`docs/MILESTONE3.md`, step 8.

**Fading memory** (step 7, `experiments/community_probe.py --fading`, 5
seeds x 3,000 ticks; success line: lasting 25%+ AND home spread about 6
tiles or less AND biggest group well under half the world):

| | memory 10 (default) | 20, no fade | 20, fade 75 | 20, fade 150 | 20, fade 300 | 20, fade 600 |
| --- | --- | --- | --- | --- | --- | --- |
| groups lasting 1,000+ ticks | 6.3% | 54% | 11% | 44% | 60% | 54% |
| home spread in a group | 5.7 tiles | 9.0 | 5.0 | 7.7 | 8.5 | 9.0 |
| biggest group (of about 93) | 18 | 50 | 15 | 38 | 48 | 50 |
| starved % | 62.9 | 62.5 | 62.7 | 63.8 | 63.1 | 62.5 |

No setting meets all three: whatever makes groups last also makes them
big. Fade 600 = no fading (agents die first). Bands hold everywhere. Kept
OFF; details in `docs/MILESTONE3.md`, step 7.

**Why groups end** (`experiments/community_probe.py --endings`, 5 seeds x
3,000 ticks):

| | memory 10 (default) | memory 20 | memory 1000 |
| --- | --- | --- | --- |
| close friends (5+ meetings) forgotten per 1,000 ticks | 211 | 2 | 0 |
| groups lasting 1,000+ ticks | 6.3% | 54% | 71% |
| groups per snapshot (biggest) | 7.0 (18) | 3.1 (50) | 2.5 (55) |
| members' homes spread | 5.7 tiles | 9.0 | 10.3 |
| ended by death / split / dissolved | 55 / 28 / 15% | 21 / 46 / 0% | 21 / 17 / 1% |

The cap of 10 makes agents forget friends all the time, so groups stay
small and short. Without forgetting, groups last but grow into a few huge
regional blobs. Bands hold everywhere.

**Family home** (`experiments/community_probe.py`, `home_drift.py`, 5 seeds
x 3,000 ticks): family homes stop drifting (0 tiles against 14-19 after 10
generations); groups get tighter (homes 3.3 against 5.7 tiles apart) and
more family-like (24% against 19% family ties); 226 gifts against 187; but
groups lasting 1,000+ ticks stay at 6.1% +/- 4.8 against 6.3% +/- 1.5, and
the starved share rises to 65.0% from 62.9% (bands hold). Goal not met, so
off by default.

**Groups** (`experiments/community_probe.py`, 5 seeds x 3,000 ticks; tie =
both remember 5+ meetings; group = 3+ agents connected by ties):

| | homes on | homes off |
| --- | --- | --- |
| agents in a group | 58% | 33% |
| group size (biggest) | 7.7 (18) | 5.4 (11) |
| family ties inside groups | 19% | 9% |
| members' homes spread | 5.7 tiles | 13.3 tiles |
| group can be traced | 225 ticks | 110 ticks |
| groups lasting 1,000+ ticks (all founders dead) | 6.3% | 0.4% |
| gifts inside a group (vs pairs that could) | 31% (51%) | 6% (24%) |

**Home drift** (`experiments/home_drift.py`): a child's home is 5.2-5.6
tiles from its parent's; after 10+ generations a family's home is 14-19
tiles from the founder's.

**Sharing** (`docs/MILESTONE3.md`; `experiments/sharing_probe.py`, 5 seeds x
3,000 ticks):

| | no sharing | sharing, met 2+ (default) |
| --- | --- | --- |
| starved % of deaths | 65.4 | 62.9 |
| age at death | 304 | 319 |
| births | 931 | 894 |
| population after tick 500 | 93.1 | 93.6 |
| gifts per run | 0 | 187 (170 different pairs) |
| receivers alive 20 ticks later | | 98% |
| gifts ever returned | | 0% |

All Milestone 2 bands hold (starved and age close to an edge). Sharing
rescues individuals and makes life a bit longer, with slightly fewer births;
the population stays the same. **No exchange emerged:** of about 935 gifts
none went back the other way; givers and receivers are mostly different
agents. Fewer gifts than the "few hundred" I hoped for.

**Encounter memory** (`docs/MILESTONE3.md`; `experiments/memory_probe.py`,
5 seeds x 3,000 ticks): an adult has met about 31 agents and remembers 10;
its most-met agent about 11 times; it keeps 76% of the agents it met 5+
times (the first cap rule kept only 50%, so it was replaced); 12% of what
it remembers is family. Behaviour identical with memory on or off. Cost:
about 6-13% slower depending on the timing, saves about 2.5% bigger.

**Could memory be used for something? (`experiments/sharing_opportunity.py`)**
One starvation death in three (33.7%) happened to an agent that, in its last
20 ticks, stood next to a well-fed agent carrying food; in one in five
(19.4%) that agent had met it before; family only 4.6%.

**Homes** (`docs/MILESTONE3.md`; `experiments/encounter_probe.py`, 5 seeds x
3,000 ticks; `stage_compare.py`):

| | homes off (Milestone 2) | homes, radius 6 (default) | radius 3 |
| --- | --- | --- | --- |
| meetings that are family | 6.0% | 13.0% | 20.0% |
| pairs that meet 5+ times | 8.5% | 21.1% | 26.6% |
| different agents met in a life | 38.3 | 25.0 | 19.4 |
| population after tick 500 | 93.0 | 93.1 | 93.4 |
| starved % of deaths | 66.5 | 65.4 | 66.1 |
| births | 946 | 931 | 947 |

Both success lines met (family share and 5+ meetings at least doubled), all
Milestone 2 bands hold, speed unchanged.

**Curiosity** (`docs/MILESTONE2_REPORT.md`, `docs/MILESTONE3.md`): it always
changes how agents walk. Without homes, high-curiosity families out-bred low
ones in 34 of 40 mixed worlds. **With homes that advantage mostly
disappears** (25 of 40, within luck), because homes keep every agent near
its patch, which was the zigzaggers' edge. In normal runs no trait is
selected beyond chance.

## 5. Next step: Milestone 3, step 9, rest at home (recommended)

**What:** a tired agent that is not hungry (rest below `rest_below`, the
moment it would start resting) first walks home and rests when it is within
`rest_home_within` tiles of home (proposed 1). If water blocks the way, or
its rest falls very low (proposed: below 10), it rests where it is, as
today. New setting `rest_home` (1 = on, 0 = today's rule; old saves get 0).
No social rule: it is about a PLACE, not about other agents.

**Why (evidence, section 4 and `docs/MILESTONE3.md` step 8):** tight
circles of friends exist and are very local (homes 1 to 4 tiles apart),
but each breaks up within about 35 to 90 ticks: agents meet only by chance
while wandering, so the same few agents do not meet again often enough to
keep or renew a circle. Resting is a long stay (about 13 ticks, several
times a life). If everyone rests at home, neighbours and family (most of
all with the family home) meet again and again in the same spot.

**Alternatives considered:**
- *A newborn starts knowing its parent's close friends*: faster renewal, but
  it writes meetings that never happened into memory; rejected unless rest
  at home fails.
- *Switch on fading or the family home anyway*: measured; neither gives
  circles that last (section 4).
- *Pause Milestone 3 for the tidy-up tasks* (section 6, tasks 2 to 5): a
  fair choice if you prefer; nothing is broken.

**Files:** `genesis/agents.py` (the rest decision), `genesis/config.py`,
`overrides.py`, `save.py` (version 9), new `tests/test_rest_home.py`,
README, `docs/MILESTONE3.md`. Frozen reference of today's world first.

**Tests:** `rest_home = 0` reproduces today exactly; a v8 save migrates and
continues exactly; a tired agent far from home walks home and then rests;
one within reach rests at once; water in the way or very low rest = rests
where it is; hunger still comes first; same seed = same world.

**Measure and success:** `community_probe.py --cores --every 50` with rest
at home on and off, with and without the family home. Success = tight
circles last clearly longer (mean well above 90 ticks, and some reach
1,000) AND the Milestone 2 bands hold (walking home costs energy; watch
starvation). Report every world, including any that fail.

**Risks:** walking home while tired may cost energy and raise starvation;
home might be far after a long food chase (home radius keeps it within
about 7 tiles).

## 6. Next 5 tasks

1. **Your go for step 9 (rest at home)**, then build it as in section 5.
   Check: `python3 -m unittest discover -s tests`, then
   `python3 experiments/community_probe.py --cores --every 50`.
2. **Decide what curiosity should mean now** (decision 2). If "roaming
   distance": files `genesis/agents.py`, `genesis/traits.py`, tests; measure
   with `python3 experiments/curiosity_probe.py`.
3. **Test industriousness in mixed worlds** (copy the mixed mode of
   `curiosity_probe.py`).
4. **`why.py --load` reads stored history.** Files: `why.py`,
   `genesis/history.py`, `tests/test_history.py`.
5. **Add action mix and trait averages to `--summary`.** Files:
   `genesis/summary.py`, `tests/test_summary.py`.

## 7. Decisions for you

1. **Go for step 9, rest at home (section 5)?** It changes where agents
   rest, so it changes the world. Default: wait for your yes.
2. **Fading memory default.** OFF (`memory_fade` 0, `memory_keep` 10)
   because it missed its goal. If you prefer groups that last over groups
   that stay small, `memory_fade` 150 with `memory_keep` 20 gives 44%
   lasting groups (biggest about 38 of 93), bands hold, about 12% slower.
3. **Family home default.** I switched it OFF after it missed its goal
   (groups did not last longer; a bit more starvation). If you like the
   tighter family groups anyway, set the default to 1 in `genesis/config.py`.
4. **Curiosity after homes.** It now matters little. Options: (a) leave it;
   (b) let it also set each agent's roaming distance around home (curious =
   wanders further), which matches the word; (c) remove its effect.
   Default: (a) until you choose.
5. **`home_radius` = 6** (chosen as proposed). 3 doubles family contact
   again (20%) but agents meet fewer different agents (19 in a life) and
   reunite less after long gaps. Change anytime with `--set home_radius=3`.
6. History caps (20 decisions per agent, 50 dead agents) and
   `memory_keep` 10: kept.
7. The gather-then-eat flaw (6.2% of starvation deaths happen one tick after
   picking food up): still NOT fixed, so all comparisons stay valid.

## 8. Remaining limitations

- Results are for one map size (60 x 40), one food setting, 3,000 ticks.
- Mixed-world curiosity results use extreme values (10/50/90), no mutation.
- Homes never move. How often an agent is stuck on the far side of a lake
  from its home was not measured on real maps.
- `why.py` replays from the seed; it does not read stored history.
- The population graph on the page is not saved; it restarts after Load.
- Saves are about 1.1 MB at 2,000-3,000 ticks, mostly decision history.
- Memory costs about 6-13% speed (around the 10% aimed for).
- Sharing: fewer gifts than hoped (187 per run); no gift ever returned.
- Groups: the chained definition (mutual 5+ ties, connected) and, since
  step 8, stricter "tight circle" views. How long a group "lasts" depends on
  how often it is checked (250 vs 50 ticks); compare only like with like.
- Fading memory is built but off (no fade time met its goal).
- The family home is built but off; with it on, starvation rises a little.
- "Family" in panel and probes = parent, child, sibling while alive only.
- One test (`test_controls.py`) sleeps 0.7 s and could rarely fail on a very
  busy Mac. Python 3.9.
- Claude's sandbox blocks opening a port; the server check needed a run
  outside the sandbox (or `sandbox.network.allowLocalBinding: true`).

## 9. Copy-paste commands

```bash
cd ~/Desktop/"Project Genesis"
```

See the world in your browser (stop with Ctrl+C):

```bash
python3 server.py
```

All automatic checks (should end with `Ran 132 tests` and `OK`, about 55 s):

```bash
python3 -m unittest discover -s tests
```

Run without the page, with a report:

```bash
python3 run_headless.py --seed 42 --ticks 2000 --every 0 --summary
```

The same world without homes (Milestone 2 behaviour):

```bash
python3 run_headless.py --seed 42 --ticks 2000 --every 0 --summary --set home_radius=0
```

Why did agent 12 do that?

```bash
python3 why.py --seed 42 --ticks 300 --agent 12
```

Experiments (each only reads the world; results go to `experiments/results/`):

```bash
python3 experiments/encounter_probe.py
```

```bash
python3 experiments/memory_probe.py
```

```bash
python3 experiments/sharing_opportunity.py
```

```bash
python3 experiments/sharing_probe.py
```

```bash
python3 experiments/community_probe.py
```

```bash
python3 experiments/community_probe.py --endings
python3 experiments/community_probe.py --fading
python3 experiments/community_probe.py --cores --every 50
```

```bash
python3 experiments/home_drift.py
```

The world without sharing:

```bash
python3 run_headless.py --seed 42 --ticks 2000 --every 0 --summary --set share_min_meetings=0
```

```bash
python3 experiments/curiosity_probe.py
```

```bash
python3 experiments/curiosity_probe.py --mixed-extra
```

```bash
python3 experiments/stage_compare.py
```

```bash
python3 experiments/trait_drift.py
```

```bash
python3 experiments/starvation_study.py
```

```bash
python3 experiments/baseline/make_baseline.py --check
```

Add `--homes-off` to the two curiosity commands to regenerate the
Milestone 2 files (`curiosity_probe.txt`, `curiosity_mixed_extra.txt`);
without it they write the `_home` files. `stage_compare.py` prints both
(its homes-on output is saved as `stage_compare_home.txt`). Times on this Mac:
memory probe about 3 min (`--old-drop-rule` for the rejected first cap
rule), sharing count about 1.5 min, sharing probe about 5 min, community
probe about 6 min (`--endings` about 8 min, `--fading` about 15 min, `--cores` about 20 min, `--cores --every 50`
about 25 min), home drift about 1 min, encounter probe about 3 min, curiosity probe about 4 min, mixed extra about
4 min, stage compare about 4 min, trait drift about 2 min, starvation study
about 25 s, baseline check about 1 min. `trait_drift.py` and
`starvation_study.py` now run with homes on; their saved results are from
before homes.

## Design choices (one line each)

- **Python standard library only, plus a thin web page.** Node.js is not installed.
- **The world is one plain dictionary.** A save is that dictionary as JSON text.
- **Our own dice (`rng.py`).** Its memory is one number, stored in the save;
  traits use their own per-agent dice so they never disturb the main dice.
- **Rules in a fixed order, first one that fits wins.** No scoring system:
  nothing measured so far needs one.
- **Personality as thresholds and rates**, neutral at 50, whole numbers only.
- **Old saves are repaired on every load** and keep their old rules, logged.
- **The server runs the world; the page only draws.**
- **Experiments only read the world.** Prototypes live in `experiments/`,
  clearly marked, never in `genesis/` and never in saves.
- **Mixed worlds as the selection test**, because forced worlds cannot show
  competition between traits.
- **Freeze before changing.** Each step that changes behaviour first freezes
  today's digests (`experiments/baseline/milestone2.json`), and "setting
  off" must reproduce them exactly.
- **Homes: greedy step, no path search.** The simpler choice; a lake in the
  way just means normal wandering (tested).

## Known risks

- Claude's sandbox blocks opening a port, so browser checks need a run
  outside the sandbox.
- Replays (`why.py`) match only if code and settings are unchanged.
- Big populations slow the page (over about 300 agents at 20x).
- The experiment scripts recognise wandering from the "why" text; if that
  wording changes, update `move_kind` in the scripts.

## Session log

Newest first. Older entries mention section numbers of earlier versions of
this file; see `git log -p STATUS.md` for those.

### Session 2026-11-18 (part 12: Milestone 3 step 8, tight circles)
- **Your go** ("Yes, step 8"). Measurement only; nothing in `genesis/`.
- **New:** `community_probe.py --cores` (stricter groups: core3, shared1/2/3,
  K10), `--every N` (snapshot gap), `--reprint` (print a saved result).
- **Assumptions / changes to the plan:** added the "shared friends" views
  because a 3-core cannot cut a lone bridge; added two family-home worlds
  after a quick trial; added the 50-tick run because 250 ticks is almost a
  lifetime. The first printout had one overlapping column; it was printed
  again from the saved .json with `--reprint` (checked identical).
- **Found:** section 4: tight circles exist, are local, never last; the
  old "lasting" line depends on the snapshot gap.
- **Not done:** step 9 (waits for your go).

### Session 2026-11-18 (part 11: Milestone 3 step 7, fading memory)
- **Your go** ("Yes, fading memory").
- **Frozen first** (`ce05be0`): `experiments/baseline/milestone3_family.json`
  (now with a code for every agent's memory), `tests/fixtures/save_v7_seed42_t300.json`.
- **Built:** `memory_fade` (`genesis/memory.py` `_fade`), save version 8
  (older saves: fade 0 and memory 10), `tests/test_fading.py` (10), panel
  text, `community_probe.py --fading`.
- **Assumption:** added fade 75 to the planned 150/300/600 after a quick
  2-seed run showed 300 and 600 change little (agents live about 310 ticks).
- **Found:** section 4. No fade time met the success line; kept OFF, so the
  default world is unchanged (reproduces the frozen step 6 world exactly).
- **Tests:** 155 OK. Browser: section 3.
- **Not done:** step 8 (waits for your go).

### Session 2026-11-18 (part 10: Milestone 3 step 6, why do groups end?)
- **Your go** ("Yes, step 6"). Measurement only; nothing in `genesis/`.
- **New:** `community_probe.py --endings` (how each group ends, when agents
  join, how often full memories forget close friends), worlds: default,
  family home, memory 20, memory 1000.
- **Found:** section 4. The memory cap of 10 is the main reason groups do
  not last; without forgetting, groups last but become regional blobs.
- **Not done:** step 7 (waits for your go).

### Session 2026-11-18 (part 9: Milestone 3 step 5, the family home)
- **Your go** ("Yes, family home").
- **Frozen first** (`8d8381b`): `experiments/baseline/milestone3_share.json`,
  `tests/fixtures/save_v6_seed42_t300.json`.
- **Built** (`6c90028`): `home_inherit`, save version 7 (old saves: 0).
  Page (`0057584`): "its family's home, from #58".
- **A scare that was not a bug:** the full test suite ran for many minutes
  once; each file alone ran in normal time. Cause: several test suites and
  experiments running at the same time on this Mac. Final suite alone: 145
  OK in about 1.5 minutes.
- **Measured:** section 4 and `docs/MILESTONE3.md`. Goal NOT met (groups
  lasting 1,000+ ticks 6.1% vs 6.3%). **Decision (mine, reversible):**
  default switched to `home_inherit = 0`, so today's default world is the
  step 3 world, exactly (tested). Listed under decisions.
- **Not done:** step 6 (waits for your go).

### Session 2026-11-18 (part 8: Milestone 3 step 4, are there groups?)
- **Your go** ("Yes, measure groups"). Measurement only; nothing in
  `genesis/` changed.
- **New:** `experiments/community_probe.py` (groups from mutual memory
  ties, traced over time, homes on vs off) and `experiments/home_drift.py`.
- **Found:** section 4. Groups exist (58% of agents), most last less than a
  lifetime, 6.3% outlive all their founders; gifts go more to agents outside
  groups; family homes drift about 5 tiles per generation.
- **Fixed during the work:** the first version measured "together 500
  ticks later", which is empty because agents live about 310 ticks; replaced
  by tracing groups whose members change.
- **Not done:** step 5 (waits for your go).

### Session 2026-11-18 (part 7: Milestone 3 step 3, sharing)
- **Your go** ("Yes, build sharing"), after pushing everything (GitHub at
  `af88e8a`).
- **Frozen first** (`0a1d3e9`): `experiments/baseline/milestone3_memory.json`,
  `tests/fixtures/save_v5_seed42_t300.json`.
- **Built** (`e8794c2`): action `give`, `share_min_meetings` (2), gift counts
  in memory, `stats.gifts`, save version 6 (old saves: sharing off).
  Page (`531f33b`): "Food shared", "Newest generation", gifts per known agent.
- **Tests:** new `tests/test_sharing.py` (9); 141 OK; Milestone 1 ALL SAME;
  `share_min_meetings=0` reproduces the frozen memory world exactly.
- **Measured** (`experiments/sharing_probe.py`): section 4. Starved share
  65.4 -> 62.9, age at death 304 -> 319, births 931 -> 894, population same;
  no gift returned.
- **Not done:** step 4 (waits for your go).

### Session 2026-11-17 (part 6: Milestone 3 step 2, encounter memory)
- **Your go** ("Yes, build memory").
- **Frozen first** (`1e51430`): `experiments/baseline/milestone3_home.json`,
  `tests/fixtures/save_v4_seed42_t300.json`.
- **Built** (`bac6685`): `genesis/memory.py`, `memory` field, `memory_keep`
  (10), save version 5. Page (`1f4a169`): "Knows N agents" list.
- **Changed on evidence** (`aabe3df`): the cap first forgot whoever was met
  longest ago; `experiments/memory_probe.py` showed it kept only half of
  each agent's 5+-meeting contacts, so it now forgets the least-met.
- **Speed** (`d132043`): faster meeting search tried; cost stays about
  6-13% (the work is the updates, not the search). Reported, not hidden.
- **Tests:** new `tests/test_memory.py` (11), 132 OK; Milestone 1 ALL SAME;
  memory on/off reproduce the frozen homes world exactly.
- **Evidence for step 3:** `experiments/sharing_opportunity.py` (section 4).
- **Not done:** step 3 (waits for your go).

### Session 2026-11-17 (part 5: Milestone 3 step 1, homes, built and measured)
- **Your go** ("Yes, build home") for the plan in the previous STATUS.
- **Frozen first** (`a603e88`): `experiments/baseline/milestone2.json` and
  `tests/fixtures/save_v3_seed42_t300.json`, made with the unchanged code.
- **Built** (`8aec7e8`): `home` field, `home_radius` setting (default 6,
  0 = off), rule in `_wander`, save version 4 with migration (old saves keep
  their rules), `MILESTONE1_RULES` also sets `home_radius = 0`. Fixed in
  passing: a newborn's `last_why` now equals its history record (a test
  caught the mismatch once homes changed which agent was born last).
- **Tests:** new `tests/test_home.py` (12); 3 tests updated for version 4 /
  homes off. 121 tests OK; Milestone 1 check ALL SAME; `home_radius=0`
  reproduces the frozen Milestone 2 digests and the v3 save exactly.
- **Page** (`9a900dc`): home square, dashed area, panel line, legend,
  plainer curiosity wording. Checked in the browser, no console errors.
- **Measured:** section 4 and `docs/MILESTONE3.md`. Success lines met; side
  effect: curiosity's competitive edge mostly gone with homes.
  `curiosity_probe.py --mixed-extra --homes-off` reproduced the Milestone 2
  file exactly.
- **Not done:** encounter memory (next, section 5).

### Session 2026-11-17 (part 4: Milestone 2 finished and measured; next step chosen)
- **Verified first:** git clean on `main` at `e3e07c3`; remote `origin`
  (github.com/klai2kass/project-genesis); 109 tests OK (38.7 s).
- **Curiosity probe built and run** (`experiments/curiosity_probe.py`,
  10 seeds, forced and mixed worlds, plus 30 extra mixed seeds). Result in
  section 4. Re-run from a clean copy of the commit (`git archive`): curiosity
  probe, mixed extra and stage compare give identical numbers (speed aside).
- **Final checks:** 109 tests OK (43.4 s); `make_baseline.py --check` ALL SAME.
- **Trait drift** (`experiments/trait_drift.py`): no selection in normal runs.
- **Report written:** `docs/MILESTONE2_REPORT.md`.
- **Docs brought up to date:** README (Milestone 2 rules, settings, files,
  test count), VISION (works today / not built / next), `docs/MILESTONE2_V2.md`
  ("As built" table: stage 6 scoring and stage 7 company not built,
  `trait_report.py` replaced by `trait_drift.py`), this file rewritten.
- **Browser checked** (section 3): works, no console errors.
- **Next step chosen with evidence** (`experiments/encounter_probe.py`,
  includes a throwaway home prototype): section 5.
- **No simulation code changed.** Baseline and determinism tests untouched.
- **Not done:** industriousness in mixed worlds; measures 3, 4, 8 of
  `MILESTONE2_V2.md` section 7.

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

## Appendix: earlier results kept for reference

### Regeneration experiment results (earlier session)

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

### Recommended `regrow_per_tick` (decided: 6)

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

