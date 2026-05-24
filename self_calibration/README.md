# Self-calibration

This module contains scripts for optional solar-target self-calibration.

Solar self-calibration is recommended as a manual, inspection-driven step. The user should inspect intermediate images, masks, calibration tables, and dynamic-range improvement before deciding whether to proceed to the next round.

Suggested components:

- `do_selfcal.py`: run one self-calibration round.
- `create_masks.py`: create full-disk, active-region, or peak-based CLEAN masks.
