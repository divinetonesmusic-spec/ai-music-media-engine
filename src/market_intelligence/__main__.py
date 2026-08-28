"""``python -m market_intelligence`` entry point."""

import sys

from .preflight import main

if __name__ == "__main__":
    sys.exit(main())
