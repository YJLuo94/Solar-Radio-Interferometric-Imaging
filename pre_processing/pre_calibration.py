"""
Inspect the input Measurement Set and prepare data for calibration.

Run with CASA, for example:
    casa --nogui -c pre_processing/pre_calibration.py demo/example_meerkat_config.yml
"""

from __future__ import annotations

import sys
from pathlib import Path

# CASA tasks such as listobs, split, and partition are available only inside CASA.


def main(config_file: str) -> None:
    print(f"Pre-calibration setup using configuration: {config_file}")
    print("TODO: add listobs, metadata recording, data selection, and partitioning steps.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: casa --nogui -c pre_processing/pre_calibration.py CONFIG.yml")
    main(sys.argv[-1])
