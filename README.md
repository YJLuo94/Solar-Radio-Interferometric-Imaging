# Solar Radio Data Processing and Imaging Framework

A modular workflow for processing solar radio interferometric observations, currently developed and tested with VLA and MeerKAT solar data.

<img width="2560" height="1440" alt="Solar radio data processing workflow" src="https://github.com/user-attachments/assets/b658fd4c-4bff-4f53-ab25-30a5418f1c67" />

**Figure:** Schematic workflow for solar radio data processing and imaging. The pipeline converts interferometric visibility data into calibrated measurement sets, high-dynamic-range radio images, FITS image products, movies, and spatially resolved dynamic spectra for physical diagnostics.

## Repository Structure

```text
solar-radio-processing/
├── pre_processing/          # Scripts for data reduction, inspection, and flagging
├── calibration/             # Scripts for calibration
├── self_calibration/        # Scripts for self-calibration
├── imaging/                 # Scripts for quick-look imaging and science imaging
├── pb_correction/           # Scripts for primary beam correction
├── ms_processing/           # Scripts for measurement set processing and data preparation
├── output/                  # Scripts for generating science products
├── demo/                    # Example workflows for VLA and MeerKAT solar data
└── docs/                    # Documentation



# Solar Radio Data Processing and Imaging Framework

This repository summarizes a modular workflow for processing solar radio interferometric observations, with a current focus on MeerKAT solar data and related high-dynamic-range imaging spectroscopy products.

The workflow is designed for solar observations with advanced radio interferometric arrays, where the target is a strong, spatially extended, and rapidly varying radio source. It includes the key steps required to convert calibrated or semi-calibrated visibility data into science-ready radio images, FITS products, movies, and spatially resolved dynamic spectra.

## Overview

Solar observations with general-purpose radio interferometric arrays require dedicated processing strategies. Compared with typical deep-sky radio sources, the Sun is bright, extended, and highly variable, especially during flares. This creates specific challenges for calibration, self-calibration, imaging stability, primary beam correction, and high-dynamic-range imaging.

This repository organizes the processing workflow into functional modules, including data inspection, calibration, self-calibration, imaging, primary beam correction, FITS product generation, dynamic spectrum extraction, and visualization.

<img width="2560" height="1440" alt="附图_01" src="https://github.com/user-attachments/assets/b658fd4c-4bff-4f53-ab25-30a5418f1c67" />

**Figure:** Schematic workflow for solar radio data processing and imaging. The pipeline converts interferometric visibility data into calibrated measurement sets, high-dynamic-range radio images, FITS image products, movies, and spatially resolved dynamic spectra for physical diagnostics.

## Workflow

The typical processing sequence is:

```text
Raw visibility data
        ↓
Data inspection and preprocessing
        ↓
Calibration / self-calibration
        ↓
Multi-frequency radio imaging
        ↓
Primary beam correction
        ↓
FITS image products / image cubes
        ↓
Movies and context overlays
        ↓
Spatially resolved dynamic spectra
        ↓
Physical diagnostics

```markdown
