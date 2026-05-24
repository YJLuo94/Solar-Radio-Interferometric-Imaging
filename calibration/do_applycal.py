"""Apply cross-calibration tables to calibrator and target fields."""

from __future__ import annotations

from utils import append_log, get_casa_task


def apply_crosscal_round(config, msvis: str, calprefix: str, round_label: str) -> str:
    """Apply delay, bandpass, and gain/flux calibration tables."""
    applycal = get_casa_task("applycal")
    fluxfile = f"{calprefix}.flux" if len(config.gainfields.split(",")) > 1 else f"{calprefix}.gain_ap"

    # Bandpass field: use the flux calibrator gain solution.
    applycal(
        vis=msvis,
        field=config.bpfield,
        calwt=False,
        gaintable=[f"{calprefix}.delay", f"{calprefix}.bp", fluxfile],
        gainfield=[config.phasefield, config.bpfield, config.bpfield],
        parang=False,
        interp="linear,linearflag",
    )

    # Phase calibrator.
    applycal(
        vis=msvis,
        field=config.phasefield,
        calwt=False,
        gaintable=[f"{calprefix}.delay", f"{calprefix}.bp", fluxfile],
        gainfield=[config.phasefield, config.bpfield, config.phasefield],
        parang=False,
        interp="linear,linearflag",
    )

    # Solar target field.
    applycal(
        vis=msvis,
        field=config.tarfield,
        calwt=False,
        gaintable=[f"{calprefix}.delay", f"{calprefix}.bp", fluxfile],
        gainfield=[config.phasefield, config.bpfield, config.phasefield],
        parang=False,
        interp="linear,linearflag",
    )

    label = "First" if round_label == "r1" else "Second" if round_label == "r2" else round_label
    append_log(
        config.logfile,
        (
            f"Do {label} round of applycal.\n"
            f"Delay calibration table: {calprefix}.delay\n"
            f"Bandpass calibration table: {calprefix}.bp\n"
            f"Gain/bootstrap calibration table: {fluxfile}\n"
            f"Apply delay, bandpass, and gain calibration on {msvis}.\n"
            f"{label} round of applycal completed"
        ),
    )
    return fluxfile
