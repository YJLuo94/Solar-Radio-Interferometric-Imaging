"""
Default configuration helpers for solar-radio-processing.

The main workflow is expected to use YAML configuration files. This module
contains small helper functions that are safe to use outside CASA.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_config(config_file: str | Path) -> dict[str, Any]:
    """Load a YAML configuration file."""
    config_path = Path(config_file).expanduser().resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if config is None:
        raise ValueError(f"Configuration file is empty: {config_path}")
    return config


def get_path(config: dict[str, Any], key: str) -> Path:
    """Return a path from the `paths` section of the configuration."""
    try:
        return Path(config["paths"][key]).expanduser()
    except KeyError as exc:
        raise KeyError(f"Missing paths.{key} in configuration") from exc
