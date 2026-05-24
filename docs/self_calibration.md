# Solar Target Self-calibration

This module organizes the MeerKAT solar target self-calibration workflow into small, reviewable components. The default configuration follows the updated event-specific `slfcal_update.py` workflow, while optional functions from the older `selfcal.py` script are retained for future use.

## Main workflow

1. Split a short seed Measurement Set from the cross-calibrated target MS.
2. Produce pre-self-calibration images for all frequency chunks.
3. Generate CLEAN masks.
4. For each self-calibration round:
   - build model images with `tclean` and `savemodel='modelcolumn'`;
   - run `gaincal` per SPW;
   - optionally inspect gain tables;
   - apply one calibration table per SPW;
   - split a new corrected MS;
   - image the corrected MS for inspection.
5. Compute dynamic-range diagnostics.
6. Optionally apply all self-calibration tables to the full target MS.

## Default event setup

The default `SelfCalConfig` uses:

- 4096 channels split into 128 chunks of 32 channels;
- `timerange='11:20:28~11:20:30'`;
- `cell='2.5arcsec'` and `npix=1024`;
- a full-disk mask with radius 1100 arcsec for the first round;
- three self-calibration rounds: phase, phase, and amplitude-only by default.

These defaults preserve the behavior of the updated 2024-12-29 scan-4 script. For experiments based on the older workflow, enable peak-fraction masks and set the third round to `calmode='ap'` in a custom configuration.

## Files

- `prepare_selfcal.py`: split the seed MS.
- `initial_imaging.py`: pre-self-calibration and post-round imaging.
- `create_masks.py`: full-disk and peak-fraction masks.
- `do_selfcal.py`: round-level model imaging, gaincal, applycal, and split.
- `gaincal_tools.py`: per-SPW gaincal and optional summary plots.
- `apply_selfcal.py`: apply a single round or all rounds to a full MS.
- `dr_check.py`: dynamic-range diagnostics.
- `selfcal_pipeline.py`: high-level orchestration.
