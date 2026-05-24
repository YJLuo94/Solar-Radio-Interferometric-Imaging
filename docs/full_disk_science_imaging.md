# Full-disk science imaging

This module translates the legacy `disk_img_slfcal.py` workflow into the modular
repository layout. It is intended for the final imaging stage after the target
Measurement Set has already been self-calibrated.

The workflow performs the following operations:

1. Generate time intervals from a start time, duration, step size, and optional
   index selection.
2. Image each selected time interval and each frequency chunk with `tclean`.
3. Image both Stokes `I` and `V` by default.
4. Apply holography-based and/or katbeam-based primary-beam correction.
5. Register original and PB-corrected CASA images to solar FITS files.
6. Optionally export brightness-temperature FITS products.

The primary-beam correction is evaluated relative to the original MeerKAT
pointing center. This is important for off-axis solar observations, where the
solar disk center and telescope pointing center are not the same. The offset is
specified through `FullDiskImagingConfig.pointing_coord` and
`FullDiskImagingConfig.solar_coord`.

## Entry point

Run inside CASA from the repository root:

```python
execfile('demo/run_full_disk_imaging_20241229_scan4.py')
```

The default configuration reproduces the test slice used in the original script,
where `time_indices = [40]`. For a full production run, set:

```python
cfg.full_disk_imaging.time_indices = []
```

before calling `run_full_disk_science_imaging(cfg)`.

## Main files

- `imaging/full_disk_science_imaging.py`: main full-disk imaging loop.
- `pb_correction/shifted_center.py`: shifted-center katbeam and holography PB correction.
- `demo/run_full_disk_imaging_20241229_scan4.py`: event-specific demo entry point.
- `docs/legacy/disk_img_slfcal.py`: original legacy script for reference.
