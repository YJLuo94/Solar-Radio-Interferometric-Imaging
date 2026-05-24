"""Build FITS image cubes from frequency-time image products."""

from __future__ import annotations

import argparse
from pathlib import Path

from config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Build FITS image cubes")
    parser.add_argument("config", type=Path, help="Path to a YAML configuration file")
    args = parser.parse_args()

    config = load_config(args.config)
    print(f"Building FITS image cubes for {config.get('project', {}).get('name', 'unnamed_project')}")
    print("TODO: collect image products and write analysis-ready FITS cubes.")


if __name__ == "__main__":
    main()
