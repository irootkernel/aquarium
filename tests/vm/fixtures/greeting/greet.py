"""Print a greeting from a small command-line application."""

import argparse


def greeting(name):
    return f"Hello, {name}!"


def main():
    parser = argparse.ArgumentParser(description="Print a greeting.")
    parser.add_argument("name", nargs="?", default="world")
    args = parser.parse_args()
    print(greeting(args.name))


if __name__ == "__main__":
    main()
