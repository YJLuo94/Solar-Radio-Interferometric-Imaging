"""Flux-density scale setup for MeerKAT calibrators."""

from __future__ import annotations

from utils import append_log, get_casa_task


def set_flux_model(config, msvis: str | None = None) -> None:
    """Set the flux model for the bandpass/flux calibrator."""
    delmod = get_casa_task("delmod")
    casa_setjy = get_casa_task("setjy")
    msvis = msvis or config.msvis0

    if config.dopol:
        print("Polarization calibration is not implemented in this workflow yet.")

    # Clear possible previous calibration models.
    delmod(vis=msvis)

    # Manual model for J0408-6545; otherwise use the MeerKAT standard model.
    manual_flux_fields = ["J0408-6545", "0408-6545", ""]
    if config.bpfield in manual_flux_fields:
        casa_setjy(
            vis=msvis,
            field=config.bpfield,
            scalebychan=True,
            standard="manual",
            fluxdensity=[17.066, 0.0, 0.0, 0.0],
            spix=[-1.179],
            reffreq="1284MHz",
            ismms=config.domms,
        )
    else:
        casa_setjy(
            vis=msvis,
            field=config.bpfield,
            spw=config.spw_s,
            scalebychan=True,
            standard="Stevens-Reynolds 2016",
            ismms=config.domms,
        )

    append_log(config.logfile, "Do flux calibration step.\nFlux calibration step completed")
