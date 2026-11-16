"""Run the world with no window at all ("headless").

Examples:
    python3 run_headless.py --seed 42 --ticks 1000
    python3 run_headless.py --seed 42 --ticks 500 --save saves/day500.json
    python3 run_headless.py --load saves/day500.json --ticks 500
    python3 run_headless.py --seed 42 --ticks 200 --log decisions.jsonl
"""

import argparse
import json

from genesis import create_world, fingerprint, load_world, save_world, step


def main():
    parser = argparse.ArgumentParser(description="Run Project Genesis without a UI.")
    parser.add_argument("--seed", default="1", help="any number or word")
    parser.add_argument("--ticks", type=int, default=1000)
    parser.add_argument("--load", help="start from this save file instead of a seed")
    parser.add_argument("--save", help="write the final world to this file")
    parser.add_argument("--log", help="write every decision (with its why) to this file")
    parser.add_argument("--every", type=int, default=100,
                        help="print a status line every N ticks (0 = quiet)")
    args = parser.parse_args()

    world = load_world(args.load) if args.load else create_world(args.seed)
    log_file = open(args.log, "w", encoding="utf-8") if args.log else None

    if args.every:
        print("%8s %6s %8s %8s %8s %8s" %
              ("tick", "alive", "births", "starved", "old age", "food"))
    for _ in range(args.ticks):
        events = step(world)
        if log_file:
            for event in events:
                log_file.write(json.dumps(event) + "\n")
        if args.every and world["tick"] % args.every == 0:
            stats = world["stats"]
            print("%8d %6d %8d %8d %8d %8d" %
                  (world["tick"], len(world["agents"]), stats["births"],
                   stats["deaths_starved"], stats["deaths_old_age"],
                   sum(world["food"])))
        if not world["agents"]:
            print("Everyone died at tick %d." % world["tick"])
            break

    if log_file:
        log_file.close()
        print("Decision log written to", args.log)
    if args.save:
        save_world(world, args.save)
        print("Saved to", args.save)
    print("seed=%s tick=%d alive=%d fingerprint=%s" %
          (world["seed"], world["tick"], len(world["agents"]), fingerprint(world)))


if __name__ == "__main__":
    main()
