"""Extract total or source-resolved dynamic spectra."""

from __future__ import annotations

import argparse
from pathlib import Path

from config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract dynamic spectra")
    parser.add_argument("config", type=Path, help="Path to a YAML configuration file")
    args = parser.parse_args()

    config = load_config(args.config)
    print(f"Extracting dynamic spectra for {config.get('project', {}).get('name', 'unnamed_project')}")
    print("TODO: define source regions and extract frequency-time spectra.")


if __name__ == "__main__":
    main()
