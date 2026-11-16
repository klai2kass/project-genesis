"""Ask the world WHY: show the last decisions of one agent.

Examples:
    python3 why.py --seed 42 --ticks 300              (lists who is alive)
    python3 why.py --seed 42 --ticks 300 --agent 12   (agent 12's last 5 decisions)
    python3 why.py --seed 42 --ticks 300 --agent 12 --last 20
    python3 why.py --load saves/quicksave.json --ticks 50 --agent 12

How it works: the world is replayed from the seed (or from a save) for the
number of ticks you ask for. Because the same seed always gives the same
story, this shows exactly what happened, every time.
"""

import argparse
from collections import deque

from genesis import (create_world, format_agent_history, format_agent_list,
                     load_world, step)


def main():
    parser = argparse.ArgumentParser(description="Show why an agent did what it did.")
    parser.add_argument("--seed", default="1", help="any number or word")
    parser.add_argument("--ticks", type=int, default=300,
                        help="how many ticks to run before looking")
    parser.add_argument("--load", help="start from this save file instead of a seed")
    parser.add_argument("--agent", type=int,
                        help="the agent's number; leave out to list who is alive")
    parser.add_argument("--last", type=int, default=5,
                        help="how many decisions to show")
    args = parser.parse_args()

    world = load_world(args.load) if args.load else create_world(args.seed)
    history = deque(maxlen=max(1, args.last))
    for _ in range(args.ticks):
        for event in step(world):
            if event["agent"] == args.agent:
                history.append(event)
        if not world["agents"]:
            break

    if args.agent is None:
        print(format_agent_list(world))
        print("\nPick one and add:  --agent NUMBER")
    else:
        print(format_agent_history(args.agent, list(history), world))


if __name__ == "__main__":
    main()
