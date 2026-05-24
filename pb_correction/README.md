# Primary-beam Correction

This module contains scripts for primary-beam correction of MeerKAT solar images.

For off-axis solar observations, the primary-beam correction should account for the relative offset between the pointing/phase center and the solar disk center. The correction may use `katbeam` or holography-based beam models, depending on the available calibration products.

- `shifted_center.py`: katbeam and holography PB correction for off-axis solar images with a pointing-to-Sun offset.
