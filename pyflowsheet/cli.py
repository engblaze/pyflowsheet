import argparse
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="pyflowsheet",
        description="Pyflowsheet CLI: Process Flow Diagram compiler and validator",
    )
    parser.parse_args(argv if argv is not None else sys.argv[1:])
    return 0


if __name__ == "__main__":
    sys.exit(main())
