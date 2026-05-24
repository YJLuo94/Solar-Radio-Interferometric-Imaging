"""Apply primary-beam correction to MeerKAT solar images."""

from __future__ import annotations

import argparse
from pathlib import Path

from config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply primary-beam correction")
    parser.add_argument("config", type=Path, help="Path to a YAML configuration file")
    args = parser.parse_args()

    config = load_config(args.config)
    print(f"Applying PB correction for {config.get('project', {}).get('name', 'unnamed_project')}")
    print("TODO: implement katbeam or holography-based correction.")


if __name__ == "__main__":
    main()
