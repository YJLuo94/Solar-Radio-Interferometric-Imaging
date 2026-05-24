"""Main entry point for the modular MeerKAT solar processing workflow.

Run inside CASA, for example:

    execfile('process_main.py')

or with CASA 6 Python:

    python process_main.py

The default parameters reproduce the non-self-calibration workflow from
``docs/legacy/meerkat_proc_1229_scan4_point.py``.
"""

from __future__ import annotations

import time

from calibration.do_applycal import apply_crosscal_round
from calibration.do_crosscal import run_crosscal_round
from calibration.setjy import set_flux_model
from config import get_default_config
from imaging.qlook_image import make_quicklook_image
from imaging.sci_image import make_science_image
from imaging.full_disk_science_imaging import run_full_disk_science_imaging
from ms_processing.split_cal import split_round1_ms, split_target_ms
from pb_correction.apply_pb_correction import run_katbeam_pb_correction
from pre_processing.initial_flag import (
    calculate_reference_antenna,
    flag_round1,
    flag_round2_after_calibration,
)
from pre_processing.pre_calibration import partition_ms, write_ms_information
from self_calibration.selfcal_pipeline import run_selfcal_pipeline
from utils import add_extra_python_paths, append_log, ensure_clean_dir, init_log, setup_workdir


def prepare_environment(config) -> None:
    """Set paths, working directory, log file, and calibration directory."""
    add_extra_python_paths(config.extra_python_paths)
    setup_workdir(config.workfolder)
    init_log(config.logfile)
    ensure_clean_dir("cal")


def run_pipeline(config=None) -> None:
    """Run the configured MeerKAT processing workflow."""
    config = config or get_default_config()
    steps = config.steps
    start_time = time.time()

    prepare_environment(config)

    if steps.doinfo:
        write_ms_information(config)

    if steps.do_partition:
        partition_ms(config)

    msvis0 = config.msvis0

    if steps.do_flag1:
        flag_round1(config, msvis0)

    if steps.calc_ref:
        calculate_reference_antenna(config, msvis0)

    if steps.do_setjy:
        set_flux_model(config, msvis0)

    calprefix1 = config.round_calprefix("r1")
    if steps.do_crosscal1:
        calprefix1 = run_crosscal_round(config, msvis0, "r1")

    if steps.do_applycal1:
        apply_crosscal_round(config, msvis0, calprefix1, "r1")

    if steps.do_flag2:
        flag_round2_after_calibration(config, msvis0)

    msvisr1 = config.msvisr1
    if steps.do_split1:
        msvisr1 = split_round1_ms(config, msvis0)

    calprefix2 = config.round_calprefix("r2")
    if steps.do_crosscal2:
        calprefix2 = run_crosscal_round(config, msvisr1, "r2")

    if steps.do_applycal2:
        apply_crosscal_round(config, msvisr1, calprefix2, "r2")

    target_ms = config.outputcalvis
    if steps.do_split:
        target_ms = split_target_ms(config, msvisr1)

    if steps.do_qlimg:
        make_quicklook_image(config, target_ms)

    science_imagename = "sciimg/sciimg"
    if steps.do_sciimg:
        science_imagename = make_science_image(config, target_ms)

    if config.dopb_cor:
        run_katbeam_pb_correction(config, science_imagename)

    if steps.do_slfcal:
        run_selfcal_pipeline(config)

    if getattr(config.full_disk_imaging, "enabled", False):
        run_full_disk_science_imaging(config)

    total_minutes = (time.time() - start_time) / 60.0
    append_log(config.logfile, f"All tasks completed in {total_minutes:.2f} minutes.")
    print(f"All tasks completed in {total_minutes:.2f} minutes.")


if __name__ == "__main__":
    run_pipeline()
