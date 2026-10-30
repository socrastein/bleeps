"""Lets the tool run as `python3 -m bleeps`, with no installation."""

import sys

from bleeps.cli import main

if __name__ == "__main__":
    sys.exit(main())
