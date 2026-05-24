# Repository Guidelines for Codex

This repository contains a CASA/Python workflow for solar radio data processing.

## General rules

- Do not change scientific processing logic unless explicitly requested.
- Do not modify CASA task parameters such as `tclean`, `gaincal`, `bandpass`, `applycal`, `split`, `mstransform`, or `flagdata` without explicit instruction.
- Do not change the order of calibration, self-calibration, imaging, or primary-beam correction steps unless explicitly requested.
- Prefer small, reviewable changes over large rewrites.
- Keep comments and docstrings in English.
- Do not add large data files, FITS products, Measurement Sets, CASA images, calibration tables, movies, or generated products to the repository.
- Move hard-coded local paths into `config.py` or documented configuration files where appropriate.
- Preserve compatibility with inspection-driven CASA workflows.

## Review guidelines

- Focus on bugs, path-handling issues, unsafe file deletion, inconsistent naming, and unclear documentation.
- Treat accidental inclusion of large data products as a serious issue.
- Flag changes that may alter scientific results.
