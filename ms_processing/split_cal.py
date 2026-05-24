"""Split calibrated target data into a working Measurement Set."""

from __future__ import annotations

import sys


def main(config_file: str) -> None:
    print(f"Splitting calibrated target MS using configuration: {config_file}")
    print("TODO: call CASA split with selected target, time ranges, and frequency ranges.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: casa --nogui -c ms_processing/split_cal.py CONFIG.yml")
    main(sys.argv[-1])
