"""Partition or split Measurement Sets by scan, time range, or frequency chunk."""

from __future__ import annotations

import sys


def main(config_file: str) -> None:
    print(f"Partitioning MS using configuration: {config_file}")
    print("TODO: call CASA partition or split according to the observing setup.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: casa --nogui -c ms_processing/partition_ms.py CONFIG.yml")
    main(sys.argv[-1])
