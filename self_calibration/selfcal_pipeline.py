"""High-level self-calibration workflow."""

from __future__ import annotations

from .apply_selfcal import apply_all_rounds_to_full_ms
from .do_selfcal import run_selfcal_rounds
from .dr_check import run_dynamic_range_diagnostics
from .initial_imaging import run_precal_imaging
from .prepare_selfcal import split_selfcal_seed_ms
from .utils import get_selfcal_config, make_dirs


def run_selfcal_pipeline(config) -> str:
    """Run the configured self-calibration pipeline.

    The default configuration reproduces the event-specific structure of
    ``slfcal_update.py`` while retaining optional features from the older
    ``selfcal.py`` script, such as peak-fraction masks, gain-table inspection,
    and DR diagnostics.
    """
    sc = get_selfcal_config(config)
    make_dirs(config)

    if sc.do_split_seed_ms:
        split_selfcal_seed_ms(config, overwrite=sc.overwrite_seed_ms)

    if sc.do_precal_imaging:
        run_precal_imaging(config)

    if sc.do_selfcal_rounds:
        last_ms = run_selfcal_rounds(config)
    else:
        last_ms = ""

    if sc.do_dynamic_range:
        run_dynamic_range_diagnostics(config)

    if sc.do_apply_all_to_full_ms:
        last_ms = apply_all_rounds_to_full_ms(config, overwrite_working_copy=sc.overwrite_full_working_ms)

    return last_ms
