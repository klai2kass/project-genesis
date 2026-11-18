"""Personality traits and the dice that make them.

Two traits, each a whole number 0 to 100 (50 = neutral, behaves like
Milestone 1):
    curiosity        how straight a wandering agent walks (agents.py, _wander):
                     curious agents turn LESS, so they cover more ground
    industriousness  how slowly an agent tires while moving (needs.py)

The dice for traits are NOT the world's main dice. Each agent gets its own
little generator, made fresh from two saved facts only:

    Rng(seed_to_state("<world seed>|traits|<agent id>"))

It makes exactly two draws (curiosity first, then industriousness) and is
thrown away; the results are stored in agent["traits"]. So:
  - no generator state needs saving; save/load cannot change trait values;
  - no draw anywhere else (food, wandering, child placement) can change a
    trait, and making traits never moves the main dice.
See docs/MILESTONE2_V2.md section 2a. Golden numbers: tests/test_trait_streams.py.
"""

from .rng import Rng, seed_to_state

TRAIT_NAMES = ["curiosity", "industriousness"]   # fixed draw order
NEUTRAL = 50


def trait_stream(seed, agent_id):
    return Rng(seed_to_state("%s|traits|%d" % (seed, agent_id)))


def _clamp(value):
    return max(0, min(100, value))


def founder_traits(seed, agent_id, cfg):
    """Traits for an agent placed at world creation."""
    r = trait_stream(seed, agent_id)
    lo, hi = cfg["trait_founder_min"], cfg["trait_founder_max"]
    return {name: r.between(lo, hi) for name in TRAIT_NAMES}


def child_traits(seed, child_id, parent_traits, cfg):
    """Parent's value plus an independent whole number in -m..m, per trait."""
    r = trait_stream(seed, child_id)
    m = cfg["trait_mutation"]
    return {name: _clamp(parent_traits.get(name, NEUTRAL) + r.between(-m, m))
            for name in TRAIT_NAMES}


def neutral_traits():
    return {name: NEUTRAL for name in TRAIT_NAMES}


def trait_effect(base, trait, span):
    """The neutral-at-50 rule: base + (trait - 50) * span // 100 (floor)."""
    return base + ((trait - NEUTRAL) * span) // 100


def turn_percent(agent, cfg):
    """Chance (0-100) that a wandering agent turns this tick.

    curiosity_straight = 1 (default since the curiosity fix, 2026-11-18):
        turn_chance - ((curiosity - 50) * turn_span) // 100
        curious agents turn less and walk straighter, so they reach more
        new tiles (measured: experiments/curiosity_study.py). With the
        defaults: curiosity 0 -> 25%, 10 -> 23%, 50 -> 15%, 90 -> 7%,
        100 -> 5%. The // rounds down, so 46..49 give 16% and 50..54 15%.
    curiosity_straight = 0 (Milestone 2 rule, kept for old saves):
        turn_chance + ((curiosity - 50) * turn_span) // 100
        curious agents turned MORE: a jittery walk that covered FEWER new
        tiles, the opposite of the word (curiosity 90 explored less than 10
        in 30 of 30 seeds, experiments/results/curiosity_before.txt).
    Curiosity 50 gives turn_chance (15%) either way, so neutral agents and
    the frozen Milestone 1 baseline are unchanged."""
    shift = ((agent["traits"]["curiosity"] - NEUTRAL) * cfg["turn_span"]) // 100
    if cfg["curiosity_straight"]:
        p = cfg["turn_chance"] - shift
    else:
        p = cfg["turn_chance"] + shift
    return max(0, min(100, p))


def tire_rate(agent, cfg):
    """Rest lost per tire_scale moving ticks. Higher industriousness = slower."""
    ind = agent["traits"]["industriousness"]
    # exactly as documented: tire_base - ((ind - 50) * tire_span) // 100
    return max(0, cfg["tire_base"] - ((ind - NEUTRAL) * cfg["tire_span"]) // 100)
