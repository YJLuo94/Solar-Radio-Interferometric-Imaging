# Mapping from legacy self-calibration scripts to modules

The self-calibration module combines functionality from two legacy scripts:

- `docs/legacy/slfcal_update.py`: event-specific workflow used for the 2024-12-29 flare.
- `docs/legacy/selfcal.py`: earlier exploratory script with useful optional functions.

| Legacy block | New module |
| --- | --- |
| Directory setup | `self_calibration/utils.py`, `prepare_selfcal.py` |
| Split short self-cal MS | `prepare_selfcal.py` |
| Precal imaging and FITS registration | `initial_imaging.py` |
| Frequency-panel plotting | `initial_imaging.py` |
| Full-disk mask generation | `create_masks.py` |
| Peak-fraction mask generation | `create_masks.py` |
| Model imaging with `savemodel='modelcolumn'` | `do_selfcal.py`, `initial_imaging.py` |
| Per-SPW gaincal | `gaincal_tools.py` |
| Gain-table summary plot | `gaincal_tools.py` |
| Per-SPW applycal and split | `apply_selfcal.py` |
| Post-round imaging | `initial_imaging.py` |
| Dynamic-range comparison | `dr_check.py` |
| Apply all rounds to full MS | `apply_selfcal.py` |

The default configuration follows `slfcal_update.py`. Optional functions from `selfcal.py` are exposed through `SelfCalConfig` and the demo script.
