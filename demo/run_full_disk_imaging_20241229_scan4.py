"""Run full-disk science imaging after self-calibration.

Run inside CASA from the repository root with:

    execfile('demo/run_full_disk_imaging_20241229_scan4.py')

The defaults reproduce the event-specific full-disk imaging setup from
``docs/legacy/disk_img_slfcal.py``. Edit ``cfg.full_disk_imaging`` below before
running a large production job.
"""

from config import get_default_config
from imaging.full_disk_science_imaging import run_full_disk_science_imaging
from utils import add_extra_python_paths

cfg = get_default_config()
add_extra_python_paths(cfg.extra_python_paths)

fd = cfg.full_disk_imaging
fd.enabled = True

# Example: by default this reproduces the legacy test slice trangelist[40:41].
# Set to an empty list to process all generated timeranges.
fd.time_indices = [40]

# Typical production outputs.
fd.do_holography_pbcor = True
fd.do_katbeam_pbcor = True
fd.export_original = True
fd.export_tb = True

run_full_disk_science_imaging(cfg)
