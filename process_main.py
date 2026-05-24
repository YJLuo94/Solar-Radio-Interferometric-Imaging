"""
Top-level workflow driver.

This file is intentionally lightweight. For real observations, run and inspect
each processing stage step by step rather than treating the workflow as a
black-box pipeline.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from config import load_config


def main() -> None:
    parser = argparse.ArgumentParser(description="Solar radio processing workflow driver")
    parser.add_argument("config", type=Path, help="Path to a YAML configuration file")
    args = parser.parse_args()

    config = load_config(args.config)
    project_name = config.get("project", {}).get("name", "unnamed_project")

    print(f"Loaded configuration for: {project_name}")
    print("This driver is a workflow entry point. Run CASA processing steps individually for full inspection.")


if __name__ == "__main__":
    main()
