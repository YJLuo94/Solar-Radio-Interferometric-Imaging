"""
Initial flagging before calibration.

This script is intended for conservative pre-calibration flagging. Solar data can
contain strong real emission, so automatic flagging should be inspected carefully.
"""

from __future__ import annotations

import sys


def main(config_file: str) -> None:
    print(f"Initial flagging using configuration: {config_file}")
    print("TODO: add manual flagging, tfcrop/rflag settings, and summary plots as needed.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: casa --nogui -c pre_processing/initial_flag.py CONFIG.yml")
    main(sys.argv[-1])
