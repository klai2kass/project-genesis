# Project Genesis: vision

The permanent reference for every future session. If a feature does not
serve this, question it. If this file and the code disagree about what
**works today**, the code wins and this file gets fixed.

## Principles

1. **Genesis is an artificial world simulation, not a predetermined game.**
   There is no script, no win condition and no story written in advance.
2. **Inhabitants develop organically** through their environment and through
   each other, not through hand-placed events.
3. **Individuals eventually are unique**: personalities, needs, goals,
   memories, relationships and histories of their own.
4. **The ecosystem is interconnected.** Changing one thing (food, climate,
   population) ripples through everything else.
5. **Societies, cultures, economies, governments and civilizations emerge**
   from individual behaviour. They are never scripted or hard-coded.
6. **Local and offline.** It runs on one Mac, free, with no network and no
   paid service.
7. **Ordinary code does the routine thinking.** Simple rules (and later,
   only if rules prove too rigid, scoring) decide everyday behaviour.
   LLMs may later help with complex reasoning and conversation, but are
   never required for every individual action.
8. **Observable, measurable, reproducible, expandable.** Every decision can
   be explained ("why" log), every run can be measured (summaries), the same
   seed and settings give the same result, and new features plug in without
   rewrites.

## Working rules that follow from the principles

- The simulation core (`genesis/`) runs with no window, so tests are fast.
- Randomness only through the seeded dice in `genesis/rng.py`.
- Old saves keep loading. Never silently drop information.
- Do not report numbers the simulation does not track.
- Python 3.9, standard library only.

## Roadmap

### Works today (Milestones 1 and 2, checked in STATUS.md)

- Seeded world with land, water and regrowing food.
- About 50 founders, settling near 93 agents, that look for food (walking
  around water), gather, eat, rest, reproduce and die.
- A **rest need** (resting halves energy use, only when not hungry) and two
  inherited **personality traits**: industriousness (how fast an agent
  tires) and curiosity (how often a wandering agent turns).
- Same seed gives the same result; Milestone 1 behaviour is frozen and
  reproducible (`tests/test_baseline.py`).
- "Why" record for every decision: need, options considered, reason; the
  last decisions of every agent are kept in saves.
- Save and load, with older saves upgraded and keeping their old rules;
  headless runner with `--set` and `--summary`; `why.py`.
- Browser map with pause, speed, step, save, load and an agent inspector.
- Measurement scripts in `experiments/`; what they found for Milestone 2 is
  in `docs/MILESTONE2_REPORT.md` (short version: rest changes behaviour;
  curiosity changes how agents walk and, in competition, which families
  survive; in normal runs no trait is selected yet).

### Not built, deliberately

- A scoring decision system (rules in a fixed order are still enough).
- A "company" need, sociability or any social behaviour.
- Memory of places or of other agents. **Agents remember nothing except
  their own last decisions and the food they are walking to.**

### Next (proposed in STATUS.md, not built)

- **Milestone 3, step 1: a home.** Each agent remembers where it was born and,
  when it has nothing better to do, drifts back toward it. A throwaway
  prototype (`experiments/encounter_probe.py`) showed this doubles how often
  family members meet and how often the same two agents meet repeatedly,
  without changing survival. Step 2: memory of encounters (who, where, when).

### Future ambition (nothing below exists)

- **Memory and relationships:** agents recognise individuals they met;
  family, friendship, rivalry.
- **Groups:** cooperation, shared knowledge, simple communities.
- **Culture and economy:** habits passed on, trade and exchange, emerging
  from needs and scarcity.
- **Governance and civilization:** rules and leadership that arise from
  groups, not from a script.
- **Optional LLM layer:** richer reasoning and dialogue for a few
  important moments, always with a plain-code fallback.
