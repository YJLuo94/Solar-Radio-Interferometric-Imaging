# MeerKAT Solar Workflow Demo

This file outlines the intended MeerKAT workflow.

1. Prepare `example_meerkat_config.yml` with local paths and observation-specific settings.
2. Inspect the input Measurement Set and prepare partitions.
3. Apply initial flagging before calibration.
4. Set the flux-density scale and solve cross-calibration tables.
5. Apply calibration and split the calibrated target MS.
6. Generate quick-look images.
7. Decide whether solar self-calibration is needed.
8. Generate science images.
9. Apply primary-beam correction.
10. Build FITS image cubes, movies, and dynamic spectra.
