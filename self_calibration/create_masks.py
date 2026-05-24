"""Create CLEAN masks for solar self-calibration and science imaging."""

from __future__ import annotations

import sys


def main(config_file: str) -> None:
    print(f"Creating masks using configuration: {config_file}")
    print("TODO: create full-disk, active-region, or peak-based masks.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: casa --nogui -c self_calibration/create_masks.py CONFIG.yml")
    main(sys.argv[-1])
