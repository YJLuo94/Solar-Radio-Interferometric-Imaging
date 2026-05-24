"""Cross-calibration routines for MeerKAT calibrator fields."""

from __future__ import annotations

from utils import append_log, get_casa_task


def run_crosscal_round(config, msvis: str, round_label: str) -> str:
    """Run one round of delay, bandpass, gain, and fluxscale calibration.

    Parameters
    ----------
    config
        Pipeline configuration object.
    msvis
        Measurement Set to calibrate.
    round_label
        Round label such as ``"r1"`` or ``"r2"``.

    Returns
    -------
    str
        Calibration table prefix used by this round.
    """
    gaincal = get_casa_task("gaincal")
    bandpass = get_casa_task("bandpass")
    fluxscale = get_casa_task("fluxscale")

    calprefix = config.round_calprefix(round_label)

    # Delay calibration: use the phase calibrator field.
    gaincal(
        vis=msvis,
        caltable=f"{calprefix}.delay",
        field=config.phasefield,
        refant=config.refantant,
        spw="",
        minblperant=config.minbaselines,
        gaintype="K",
        gaintable=[],
        gainfield=[],
        combine="",
        solint="inf",
        minsnr=3,
        solmode="",
        solnorm=False,
        parang=False,
        append=False,
    )

    # Bandpass calibration.
    bandpass(
        vis=msvis,
        caltable=f"{calprefix}.bp",
        field=config.bpfield,
        refant=config.refantant,
        spw="",
        bandtype="B",
        minblperant=config.minbaselines,
        fillgaps=8,
        gaintable=[f"{calprefix}.delay"],
        gainfield=[config.phasefield],
        combine="scan",
        solnorm=False,
        solint="inf",
        parang=False,
        append=False,
    )

    # Complex gain calibration.
    gaincal(
        vis=msvis,
        caltable=f"{calprefix}.gain_ap",
        field=config.gainfields,
        refant=config.refantant,
        spw="",
        minblperant=config.minbaselines,
        gaintype="G",
        calmode="ap",
        solint="inf",
        solnorm=False,
        combine="",
        gaintable=[f"{calprefix}.delay", f"{calprefix}.bp"],
        gainfield=[config.phasefield, config.bpfield],
        parang=False,
        append=False,
    )

    # Flux scale bootstrap when multiple gain fields are available.
    if len(config.gainfields.split(",")) > 1:
        fluxscale(
            vis=msvis,
            caltable=f"{calprefix}.gain_ap",
            reference=[config.bpfield],
            transfer="",
            fluxtable=f"{calprefix}.flux",
            append=False,
            display=False,
            listfile=f"{calprefix}.fluxscale.txt",
        )

    label = "First" if round_label == "r1" else "Second" if round_label == "r2" else round_label
    append_log(
        config.logfile,
        (
            f"Do {label} round of cross-cal.\n"
            "Complete delay, bandpass, and gain calibration.\n"
            f"Delay calibration table: {calprefix}.delay\n"
            f"Bandpass calibration table: {calprefix}.bp\n"
            f"Gain calibration table: {calprefix}.gain_ap\n"
            f"{label} round of cross-cal completed"
        ),
    )
    return calprefix
