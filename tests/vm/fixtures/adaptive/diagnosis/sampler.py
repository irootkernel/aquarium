"""A deterministic reproduction of a caller-visible intermittent sample loss."""

import argparse
import json


def sample(sequence):
    return None if sequence % 3 == 2 else {"sequence": sequence, "value": 42}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("sequence", type=int)
    args = parser.parse_args()
    print(json.dumps(sample(args.sequence)))
