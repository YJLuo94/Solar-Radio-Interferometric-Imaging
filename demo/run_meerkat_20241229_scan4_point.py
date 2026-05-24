"""Example launcher for the MeerKAT 2024-12-29 scan-4 pointing workflow.

Run this from the repository root inside CASA after editing ``config.py`` or the
parameters below.
"""

from config import get_default_config
from process_main import run_pipeline

cfg = get_default_config()

# Example: disable science imaging for a quick calibration-only test.
# cfg.steps.do_sciimg = False
# cfg.dopb_cor = False

run_pipeline(cfg)
