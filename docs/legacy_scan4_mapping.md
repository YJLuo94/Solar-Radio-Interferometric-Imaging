# Mapping from the legacy scan-4 script to the modular workflow

This note records how `docs/legacy/meerkat_proc_1229_scan4_point.py` was split
into the current repository structure. The purpose of this refactor is to keep
the CASA task order and scientific parameters close to the original script while
making each processing step easier to inspect, rerun, and document.

| Legacy script block | Modular location |
|---|---|
| Step switches and user parameters | `config.py` |
| Add local software paths, create work folder, initialize log | `process_main.py`, `utils.py` |
| `listobs` and `plotants` information step | `pre_processing/pre_calibration.py` |
| `mstransform` partitioning to `*.cal0.ms` | `pre_processing/pre_calibration.py` |
| First-round flagging before calibration | `pre_processing/initial_flag.py` |
| Optional reference antenna calculation | `pre_processing/initial_flag.py` |
| `delmod` and `setjy` flux-density scale setup | `calibration/setjy.py` |
| Delay, bandpass, gain, and fluxscale calibration | `calibration/do_crosscal.py` |
| Apply calibration to flux, phase, and target fields | `calibration/do_applycal.py` |
| Post-calibration flagging | `pre_processing/initial_flag.py` |
| Split calibrated round-1 MS | `ms_processing/split_cal.py` |
| Final target MS split | `ms_processing/split_cal.py` |
| Quick-look `tclean` imaging | `imaging/qlook_image.py` |
| Science `tclean` imaging | `imaging/sci_image.py` |
| katbeam primary-beam correction | `pb_correction/apply_pb_correction.py` |
| End-to-end execution order | `process_main.py` |

## Notes

- Self-calibration is intentionally not included in this refactor because the
  uploaded legacy script did not include the self-calibration section.
- The refactor keeps the original two-round cross-calibration design.
- Obvious typographical issues and undefined exception variables from the legacy
  script were cleaned up, but the CASA task parameters were otherwise preserved.
- The original script is kept under `docs/legacy/` for traceability.
