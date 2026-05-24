# Self-calibration

This folder contains the modular MeerKAT solar target self-calibration workflow.

Recommended entry points:

- `selfcal_pipeline.py` — high-level orchestration.
- `do_selfcal.py` — run individual self-calibration rounds.
- `prepare_selfcal.py` — split the seed MS.
- `create_masks.py` — full-disk and peak-fraction masks.
- `dr_check.py` — dynamic-range diagnostics.

The default configuration in `config.py` follows the updated 2024-12-29 scan-4 workflow. Optional behavior from the earlier exploratory script can be enabled by editing `config.selfcal` in a demo or custom config file.
