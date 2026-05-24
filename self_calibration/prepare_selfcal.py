"""Preparation steps for solar target self-calibration."""

from __future__ import annotations

from pathlib import Path

from utils import get_casa_task

from .utils import get_selfcal_config, make_dirs


def split_selfcal_seed_ms(config, overwrite: bool = False) -> str:
    """Split the short target interval used to derive self-calibration tables.

    This follows the event-specific strategy in ``slfcal_update.py``: a compact
    MS is split from the cross-calibrated solar target data and used for model
    imaging and gain solving.
    """
    sc = get_selfcal_config(config)
    make_dirs(config)
    outputvis = Path(sc.slfcaldir) / sc.seed_ms_name
    if outputvis.exists() and not overwrite:
        print(f"Seed self-cal MS already exists: {outputvis}")
        return str(outputvis)

    split = get_casa_task("split")
    split(
        vis=sc.input_ms,
        outputvis=str(outputvis),
        datacolumn=sc.seed_datacolumn,
        timerange=sc.timerange,
    )
    print(f"Seed self-cal MS saved to: {outputvis}")
    return str(outputvis)
