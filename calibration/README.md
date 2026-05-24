# Calibration

This module contains scripts for calibrator-based cross-calibration.

Typical scripts:

- `setjy.py`: set the flux-density scale for the primary calibrator.
- `do_crosscal.py`: solve delay, bandpass, phase, and gain calibration.
- `do_applycal.py`: apply calibration tables to the target data.

The exact CASA parameters should be adjusted for each observation and inspected after each major step.
