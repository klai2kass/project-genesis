"""A tiny random number generator that we fully control.

Why not Python's built-in `random`? Two reasons:
1. Its whole memory is ONE number here, so saving a world also saves
   "where the dice are". Load the save and the dice continue exactly.
2. It gives the same numbers on every computer and Python version,
   so "same seed = same world" always holds.

(The algorithm is called mulberry32. You never need to change it.)
"""

import zlib

MASK = 0xFFFFFFFF  # keeps numbers inside 32 bits


def seed_to_state(seed):
    """Turn a seed (a number or any text) into the generator's start number.

    We do NOT use Python's hash() here: it changes every time Python starts,
    which would silently break "same seed = same world".
    """
    return zlib.crc32(str(seed).encode("utf-8")) & MASK


class Rng:
    def __init__(self, state):
        self.state = state & MASK

    def random(self):
        """A decimal number from 0 up to (not including) 1."""
        self.state = (self.state + 0x6D2B79F5) & MASK
        t = self.state
        t = ((t ^ (t >> 15)) * (t | 1)) & MASK
        t = t ^ ((t + (((t ^ (t >> 7)) * (t | 61)) & MASK)) & MASK)
        return ((t ^ (t >> 14)) & MASK) / 4294967296.0

    def below(self, n):
        """A whole number from 0 to n-1."""
        return int(self.random() * n)

    def between(self, low, high):
        """A whole number from low to high, both included."""
        return low + self.below(high - low + 1)

    def choice(self, items):
        """Pick one item from a list."""
        return items[self.below(len(items))]

    def chance(self, probability):
        """True with the given probability (0.2 means 20% of the time)."""
        return self.random() < probability
