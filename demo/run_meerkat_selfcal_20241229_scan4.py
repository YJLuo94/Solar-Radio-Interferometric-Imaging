"""Run the MeerKAT 2024-12-29 scan-4 solar self-calibration workflow.

Run this script from the repository root inside CASA after editing paths in
``config.py`` if needed.

    execfile('demo/run_meerkat_selfcal_20241229_scan4.py')
"""

from config import get_default_config
from self_calibration.selfcal_pipeline import run_selfcal_pipeline

config = get_default_config()

# This demo runs the standalone solar self-calibration workflow, not the full
# cross-calibration workflow.
config.steps.do_slfcal = True

# Keep the event-specific defaults from slfcal_update.py. Uncomment examples
# below for alternative behaviors from the older selfcal.py script.
# config.selfcal.plot_gaincal = True
# config.selfcal.do_apply_all_to_full_ms = True
# config.selfcal.rounds[1].mask_mode = 'peak_fraction'
# config.selfcal.rounds[1].mask_source_round = 'r1'
# config.selfcal.rounds[2].mask_mode = 'peak_fraction'
# config.selfcal.rounds[2].mask_source_round = 'r2'
# config.selfcal.rounds[2].calmode = 'ap'
# config.selfcal.rounds[2].model_niter = 10000
# config.selfcal.rounds[2].model_robust = -0.5

run_selfcal_pipeline(config)
