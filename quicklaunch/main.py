"""BeamNG QuickLaunch — skip-menu freeroam launcher (retail -level / -lua)."""
from __future__ import annotations

import sys
from pathlib import Path

# allow running as script from this folder
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ui import run_app  # noqa: E402


def main() -> int:
    run_app()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
