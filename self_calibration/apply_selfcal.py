"""Apply self-calibration tables to target Measurement Sets."""

from __future__ import annotations

import os
from pathlib import Path

from utils import ensure_dir, get_casa_task

from .utils import (
    clear_calibration_and_model,
    copy_ms_safely,
    generate_spws,
    get_selfcal_config,
    split_ms,
    spw_tag_from_spw,
)


def apply_round_tables(config, round_name: str, input_ms: str, output_ms: str) -> str:
    """Apply one round of per-SPW self-calibration tables and split output MS."""
    sc = get_selfcal_config(config)
    round_cfg = sc.get_round(round_name)
    applycal = get_casa_task("applycal")
    clear_calibration_and_model(input_ms)

    for spw in generate_spws(sc.nchan_total, sc.nchan_per_spw, sc.spw_id):
        spw_tag = spw_tag_from_spw(spw)
        caltable = Path(sc.caltbdir) / round_name / f"slfcal_{round_name}_spw_{spw_tag}.gcal"
        if not caltable.exists():
            print(f"Calibration table missing: {caltable}; skipping {spw}")
            continue
        kwargs = dict(
            vis=str(input_ms),
            spw=spw,
            gaintable=[str(caltable)],
            interp="linear",
            calwt=False,
            applymode="calonly",
            flagbackup=False,
        )
        # The updated event script intentionally applies to the full MS time range.
        # For legacy reproduction, set apply_timerange=True in the round config.
        if round_cfg.apply_timerange:
            kwargs["timerange"] = sc.timerange
        print(f"Applying {caltable} to {spw}")
        try:
            applycal(**kwargs)
        except Exception as exc:
            print(f"Applycal failed for {spw_tag}: {exc}")

    split_ms(input_ms, output_ms, datacolumn="corrected")
    print(f"Self-calibrated MS saved to: {output_ms}")
    return str(output_ms)


def apply_all_rounds_to_full_ms(config, overwrite_working_copy: bool = False) -> str:
    """Apply all configured self-calibration rounds to a full target MS.

    This implements the final ``applycal to all`` block from the event-specific
    update script: the original target MS is copied into the self-cal directory,
    all per-SPW gain tables are applied in sequence, and a final calibrated MS is
    split out.
    """
    sc = get_selfcal_config(config)
    applycal = get_casa_task("applycal")
    working_ms = Path(sc.slfcaldir) / sc.full_working_ms_name
    output_ms = Path(sc.slfcaldir) / sc.full_output_ms_name

    copy_ms_safely(sc.input_ms, working_ms, overwrite=overwrite_working_copy)
    clear_calibration_and_model(working_ms)

    for spw in generate_spws(sc.nchan_total, sc.nchan_per_spw, sc.spw_id):
        spw_tag = spw_tag_from_spw(spw)
        gaintables = [
            str(Path(sc.caltbdir) / round_cfg.name / f"slfcal_{round_cfg.name}_spw_{spw_tag}.gcal")
            for round_cfg in sc.rounds
        ]
        missing = [table for table in gaintables if not os.path.exists(table)]
        if missing:
            print(f"Missing gain tables for {spw_tag}; skipping. Missing: {missing}")
            continue
        print(f"Applying all self-cal tables to SPW {spw_tag}")
        applycal(
            vis=str(working_ms),
            spw=spw,
            gaintable=gaintables,
            interp="linear",
            calwt=False,
            applymode="calonly",
            flagbackup=False,
        )

    split_ms(working_ms, output_ms, datacolumn="corrected")
    print(f"Final full self-calibrated MS saved to: {output_ms}")
    return str(output_ms)
