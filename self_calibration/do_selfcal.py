"""Core self-calibration loop for MeerKAT solar target data."""

from __future__ import annotations

from pathlib import Path

from utils import ensure_dir

from .apply_selfcal import apply_round_tables
from .create_masks import build_mask_pattern, ensure_round_masks
from .gaincal_tools import plot_gaincal_summary, run_gaincal_per_spw
from .initial_imaging import image_selfcal_round, image_spw_sequence
from .utils import clear_calibration_and_model, get_selfcal_config


def round_input_ms(config, round_name: str) -> str:
    """Return the input MS for a self-calibration round."""
    sc = get_selfcal_config(config)
    idx = int(round_name.replace("r", ""))
    if idx == 1:
        return str(Path(sc.slfcaldir) / sc.seed_ms_name)
    return str(Path(sc.slfcaldir) / sc.round_ms_name(idx - 1))


def round_output_ms(config, round_name: str) -> str:
    """Return the output MS for a self-calibration round."""
    sc = get_selfcal_config(config)
    idx = int(round_name.replace("r", ""))
    return str(Path(sc.slfcaldir) / sc.round_ms_name(idx))


def build_model_images_for_round(config, round_name: str, input_ms: str) -> list[str]:
    """Run CLEAN with ``savemodel='modelcolumn'`` for a self-calibration round."""
    sc = get_selfcal_config(config)
    round_cfg = sc.get_round(round_name)
    ensure_round_masks(config, round_name)
    mask_pattern = build_mask_pattern(config, round_name)
    if not mask_pattern:
        mask_pattern = None

    img_dir = ensure_dir(Path(sc.imagedir) / round_name)
    clear_calibration_and_model(input_ms)
    return image_spw_sequence(
        config,
        vis=input_ms,
        output_dir=str(img_dir),
        image_prefix=f"img_{round_name}",
        niter=round_cfg.model_niter,
        robust=round_cfg.model_robust,
        datacolumn="data",
        savemodel="modelcolumn",
        mask_pattern=mask_pattern,
        uvrange=round_cfg.uvrange,
        cleanup=True,
    )


def run_selfcal_round(config, round_name: str) -> str:
    """Run model imaging, gaincal, applycal, split, and post-round imaging."""
    input_ms = round_input_ms(config, round_name)
    output_ms = round_output_ms(config, round_name)
    print(f"========== Starting self-calibration {round_name.upper()} ==========")
    print(f"Input MS:  {input_ms}")
    print(f"Output MS: {output_ms}")

    build_model_images_for_round(config, round_name, input_ms)
    run_gaincal_per_spw(config, round_name, input_ms)
    sc = get_selfcal_config(config)
    if sc.plot_gaincal:
        plot_gaincal_summary(config, round_name)
    apply_round_tables(config, round_name, input_ms, output_ms)
    if sc.image_after_each_round:
        image_selfcal_round(config, round_name, output_ms)
    print(f"========== Finished self-calibration {round_name.upper()} ==========")
    return output_ms


def run_selfcal_rounds(config) -> str:
    """Run all configured self-calibration rounds."""
    sc = get_selfcal_config(config)
    last_ms = ""
    for round_cfg in sc.rounds:
        last_ms = run_selfcal_round(config, round_cfg.name)
    return last_ms
