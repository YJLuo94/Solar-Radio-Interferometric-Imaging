# Solar Radio Processing

`solar-radio-processing` is a modular CASA/Python workflow for processing solar radio interferometric observations, with an emphasis on MeerKAT solar imaging spectroscopy. The repository is designed as an inspection-driven research workflow rather than a fully automated black-box pipeline. Each major processing step is kept visible so that calibration, self-calibration, imaging, primary-beam correction, and science-product generation can be inspected and adjusted for different observations.

The current structure is designed around MeerKAT solar data, but the `demo/` directory also includes a placeholder workflow for VLA solar observations so that common steps can be generalized later.

## Workflow Overview

This repository follows a modular workflow for solar radio imaging spectroscopy. The CASA-based components are used for Measurement Set preparation, flagging, calibration, self-calibration, and imaging, while the Python-based components are used for post-processing, primary-beam correction, visualization, and science-product generation. The workflow starts from an input MeerKAT Measurement Set and a user-defined configuration file, and produces calibrated target Measurement Sets, FITS image cubes, movies, and dynamic spectra.

<img width="2560" height="1440" alt="Solar radio data processing workflow" src="https://github.com/user-attachments/assets/b658fd4c-4bff-4f53-ab25-30a5418f1c67" />

<p align="center">
  <b>Figure 1.</b> Modular workflow of the solar radio processing pipeline. The workflow starts from an input Measurement Set and a user-defined configuration file, followed by data inspection, partitioning, initial flagging, cross-calibration, optional solar self-calibration, and science imaging. The final science products include calibrated target Measurement Sets, FITS image cubes, radio/EUV context movies, and dynamic spectra.
</p>

## Repository Structure

```text
solar-radio-processing/
├── pre_processing/          # Scripts for data reduction, inspection, and flagging
├── calibration/             # Scripts for calibrator-based calibration
├── self_calibration/        # Scripts for solar-target self-calibration
├── imaging/                 # Scripts for quick-look imaging and science imaging
├── pb_correction/           # Scripts for primary-beam correction
├── ms_processing/           # Scripts for Measurement Set processing and data preparation
├── output/                  # Scripts for generating science products
├── demo/                    # Example workflows for VLA and MeerKAT solar data
├── docs/                    # Documentation
├── tests/                   # Minimal tests and future validation scripts
└── .github/workflows/       # GitHub Actions configuration
```

## Main Processing Stages

### 1. Pre-processing

The `pre_processing/` module contains scripts for inspecting input Measurement Sets, recording metadata, selecting data, partitioning by spectral windows or frequency chunks, and applying initial flagging before calibration.

### 2. Cross-calibration

The `calibration/` module contains scripts for setting the flux-density scale, solving delay, bandpass, phase, and gain calibration, and applying the resulting calibration tables to the data.

### 3. Solar self-calibration

The `self_calibration/` module contains scripts for optional self-calibration on the solar target. This step is intentionally inspection-driven because solar observations can contain bright coherent bursts, weak extended emission, and strong frequency-dependent structure. The default design is to let the user inspect intermediate images and choose suitable masks, solution intervals, and calibration modes.

### 4. Imaging

The `imaging/` module contains quick-look imaging scripts for data inspection and science imaging scripts for producing final Stokes images for selected time intervals and frequency chunks.

### 5. Primary-beam correction

The `pb_correction/` module contains scripts for applying frequency-dependent primary-beam correction. For off-axis MeerKAT solar observations, this step is essential for recovering physically meaningful brightness distributions across the solar disk.

### 6. Science products

The `output/` module contains scripts for building FITS image cubes, generating radio/EUV context movies, and extracting dynamic spectra or source-resolved diagnostics.

## Installation

The CASA processing scripts should be run inside a CASA environment. The Python post-processing scripts can be run in a standard conda environment.

```bash
conda env create -f environment.yml
conda activate solar-radio-processing
pip install -e .
```

CASA is not installed by this environment file. Install CASA separately and run CASA-specific scripts using the appropriate CASA version for the data reduction.

## Quick Start

1. Edit the example configuration file:

```bash
cp demo/example_meerkat_config.yml my_meerkat_config.yml
```

2. Update local paths, time ranges, calibrator names, and frequency settings in `my_meerkat_config.yml`.

3. Run the workflow step by step. For example:

```bash
casa --nogui -c pre_processing/pre_calibration.py my_meerkat_config.yml
casa --nogui -c pre_processing/initial_flag.py my_meerkat_config.yml
casa --nogui -c calibration/setjy.py my_meerkat_config.yml
casa --nogui -c calibration/do_crosscal.py my_meerkat_config.yml
casa --nogui -c calibration/do_applycal.py my_meerkat_config.yml
```

4. Inspect the calibrated target data and decide whether self-calibration is needed.

5. Generate quick-look images and final science products:

```bash
casa --nogui -c imaging/qlook_image.py my_meerkat_config.yml
casa --nogui -c imaging/sci_image.py my_meerkat_config.yml
python pb_correction/apply_pb_correction.py my_meerkat_config.yml
python output/make_fits_cube.py my_meerkat_config.yml
```

The commands above are intended as a workflow template. Individual observations may require different flagging, calibration, imaging, and self-calibration parameters.

## Data Policy

Large MeerKAT/VLA Measurement Sets, CASA image products, calibration tables, FITS cubes, movies, and intermediate data products should not be committed to this repository. Use the `.gitignore` file to keep large data products local.

## Citation

If you use this workflow or adapt scripts from this repository, please cite the associated solar radio processing paper or project, and cite this repository using the metadata in `CITATION.cff`.

## License

This project is released under the BSD 3-Clause License. See `LICENSE` for details.
