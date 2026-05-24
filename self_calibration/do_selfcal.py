"""
Run one self-calibration round on the solar target.

This script is a template. In real processing, self-calibration should be done
per frequency chunk/SPW and inspected carefully.
"""

from __future__ import annotations

import sys


def main(config_file: str) -> None:
    print(f"Running solar self-calibration using configuration: {config_file}")
    print("TODO: image target, solve gains per frequency chunk, apply calibration, and split corrected MS.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: casa --nogui -c self_calibration/do_selfcal.py CONFIG.yml")
    main(sys.argv[-1])
