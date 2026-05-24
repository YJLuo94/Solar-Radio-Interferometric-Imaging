"""Generate radio/EUV context movies from image products."""

from __future__ import annotations

import argparse
from pathlib import Path

from config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate science movies")
    parser.add_argument("config", type=Path, help="Path to a YAML configuration file")
    args = parser.parse_args()

    config = load_config(args.config)
    print(f"Generating movies for {config.get('project', {}).get('name', 'unnamed_project')}")
    print("TODO: generate frame images and encode movies.")


if __name__ == "__main__":
    main()
