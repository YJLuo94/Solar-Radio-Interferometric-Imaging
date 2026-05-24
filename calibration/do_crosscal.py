"""Solve delay, bandpass, phase, and gain calibration tables."""

from __future__ import annotations

import sys


def main(config_file: str) -> None:
    print(f"Running cross-calibration using configuration: {config_file}")
    print("TODO: call CASA gaincal/bandpass with observation-specific parameters.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: casa --nogui -c calibration/do_crosscal.py CONFIG.yml")
    main(sys.argv[-1])
