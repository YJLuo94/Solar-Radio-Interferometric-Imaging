"""Apply calibration tables to the data."""

from __future__ import annotations

import sys


def main(config_file: str) -> None:
    print(f"Applying calibration tables using configuration: {config_file}")
    print("TODO: call CASA applycal and verify corrected data.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: casa --nogui -c calibration/do_applycal.py CONFIG.yml")
    main(sys.argv[-1])
