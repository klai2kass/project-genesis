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
7. **Ordinary code does the routine thinking.** Simple rules and scoring
   decide everyday behaviour. LLMs may later help with complex reasoning and
   conversation, but are never required for every individual action.
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

### Works today (Milestone 1, checked in STATUS.md)

- Seeded world with land, water and regrowing food.
- About 50 agents that look for food, eat, move, reproduce and die.
- Same seed gives the same result (fingerprint tests).
- Browser map with pause, speed, step, save, load and an agent inspector.
- "Why" record for every decision: need, options considered, reason.
- Save and load; headless runner; `why.py`.

### Near term (planned, not built)

- Backward-compatible saves, `--set` overrides, a run summary.
- Smarter movement around water.
- Agent history stored inside saves.
- Experiments to tune how harsh scarcity is.

### Future ambition (nothing below exists)

- **Milestone 2:** numerical needs (hunger, rest, companionship) and
  personality traits that change decisions; a scoring decision system with
  readable "why" records.
- **Memory and relationships:** agents remember places and individuals;
  family, friendship, rivalry.
- **Groups:** cooperation, shared knowledge, simple communities.
- **Culture and economy:** habits passed on, trade and exchange, emerging
  from needs and scarcity.
- **Governance and civilization:** rules and leadership that arise from
  groups, not from a script.
- **Optional LLM layer:** richer reasoning and dialogue for a few
  important moments, always with a plain-code fallback.
