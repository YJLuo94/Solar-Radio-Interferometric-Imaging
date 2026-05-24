"""Set the calibrator flux-density scale using CASA `setjy`."""

from __future__ import annotations

import sys


def main(config_file: str) -> None:
    print(f"Setting flux-density scale using configuration: {config_file}")
    print("TODO: call CASA setjy for the primary flux calibrator.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: casa --nogui -c calibration/setjy.py CONFIG.yml")
    main(sys.argv[-1])
