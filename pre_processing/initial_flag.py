"""Initial and post-calibration flagging utilities."""

from __future__ import annotations

from utils import append_log, get_casa_task


def flag_round1(config, msvis: str | None = None) -> None:
    """Run the first round of conservative RFI and data-quality flagging."""
    flagdata = get_casa_task("flagdata")
    msvis = msvis or config.msvis0

    # Bad frequencies: RFI channels.
    if config.badfreqranges:
        badspw = "*:" + ",*:".join(config.badfreqranges)
        flagdata(vis=msvis, mode="manual", spw=badspw)

    # Bad antennas.
    if config.badants:
        badant_str = ",".join(str(bb) for bb in config.badants)
        flagdata(vis=msvis, mode="manual", antenna=badant_str)

    # Flag autocorrelations.
    flagdata(
        vis=msvis,
        mode="manual",
        autocorr=True,
        action="apply",
        flagbackup=True,
        savepars=False,
        writeflags=True,
    )

    # Clip zero-amplitude components. For scans without solar bursts, also set a
    # maximum amplitude threshold, following the original script.
    if config.solar_burst:
        flagdata(vis=msvis, mode="clip", clipzeros=True)
    else:
        flagdata(vis=msvis, mode="clip", clipminmax=[0.0, 50.0], clipoutside=True, clipzeros=True)

    flagdata(vis=msvis, mode="summary", datacolumn="DATA", name="flagr1.before_tfcrop.summary")

    # Calibration fields.
    flagdata(
        vis=msvis,
        mode="tfcrop",
        field=config.calfields,
        ntime="scan",
        timecutoff=5.0,
        freqcutoff=5.0,
        timefit="line",
        freqfit="line",
        extendflags=False,
        timedevscale=5.0,
        freqdevscale=5.0,
        extendpols=True,
        growaround=False,
        action="apply",
        flagbackup=True,
        overwrite=True,
        writeflags=True,
        datacolumn="DATA",
    )

    # Target field: skip or flag conservatively if preserving solar bursts.
    if not config.solar_burst:
        flagdata(
            vis=msvis,
            mode="tfcrop",
            field=config.tarfield,
            ntime="scan",
            timecutoff=6.0,
            freqcutoff=6.0,
            timefit="poly",
            freqfit="poly",
            extendflags=False,
            timedevscale=5.0,
            freqdevscale=5.0,
            extendpols=True,
            growaround=False,
            action="apply",
            flagbackup=True,
            overwrite=True,
            writeflags=True,
            datacolumn="DATA",
        )

    flagdata(vis=msvis, mode="summary", datacolumn="DATA", name="flagr1.before_extend.summary")

    flagdata(
        vis=msvis,
        mode="extend",
        field=config.calfields,
        datacolumn="data",
        clipzeros=True,
        ntime="scan",
        extendflags=False,
        extendpols=True,
        growtime=80.0,
        growfreq=80.0,
        growaround=False,
        flagneartime=False,
        flagnearfreq=False,
        action="apply",
        flagbackup=True,
        overwrite=True,
        writeflags=True,
    )

    if not config.solar_burst:
        flagdata(
            vis=msvis,
            mode="extend",
            field=config.tarfield,
            datacolumn="data",
            clipzeros=True,
            ntime="scan",
            extendflags=False,
            extendpols=True,
            growtime=80.0,
            growfreq=80.0,
            growaround=False,
            flagneartime=False,
            flagnearfreq=False,
            action="apply",
            flagbackup=True,
            overwrite=True,
            writeflags=True,
        )

    flagdata(vis=msvis, mode="summary", datacolumn="DATA", name="flagr1.after_extend.summary")

    append_log(
        config.logfile,
        (
            "Do flag round 1 step.\n"
            "Flagged bad frequency channels, bad antennas, and autocorrelations.\n"
            "Applied clip, tfcrop, and extend flagging.\n"
            "Check the CASA logger for detailed flagging summaries.\n"
            "Flag round 1 step completed"
        ),
    )


def calculate_reference_antenna(config, msvis: str | None = None) -> tuple[str, list]:
    """Calculate the reference antenna using the legacy ``calc_refant`` helper."""
    msvis = msvis or config.msvis0
    import calc_refant

    refant, badants = calc_refant.get_ref_ant(visname=msvis, fluxfield=config.bpfield)
    config.refantant = refant
    config.badants = badants

    append_log(
        config.logfile,
        (
            "Do calculate reference antenna step.\n"
            f"Set reference antenna: {refant}; find bad antennas: {badants}\n"
            "Calculate reference antenna completed"
        ),
    )
    return refant, badants


def flag_round2_after_calibration(config, msvis: str | None = None) -> None:
    """Flag calibrated data after the first cross-calibration round."""
    flagdata = get_casa_task("flagdata")
    msvis = msvis or config.msvis0

    # Calibration fields: tight flagging on corrected data.
    flagdata(vis=msvis, mode="summary", datacolumn="corrected", name="flagr2.before_tfcrop.summary")
    flagdata(
        vis=msvis,
        mode="tfcrop",
        datacolumn="corrected",
        field=config.calfields,
        ntime="scan",
        timecutoff=6.0,
        freqcutoff=5.0,
        timefit="line",
        freqfit="line",
        flagdimension="freqtime",
        extendflags=False,
        timedevscale=5.0,
        freqdevscale=5.0,
        extendpols=False,
        growaround=False,
        action="apply",
        flagbackup=True,
        overwrite=True,
        writeflags=True,
    )

    flagdata(vis=msvis, mode="summary", datacolumn="corrected", name="flagr2.after_tfcrop.summary")
    flagdata(
        vis=msvis,
        mode="rflag",
        datacolumn="corrected",
        field=config.calfields,
        timecutoff=5.0,
        freqcutoff=5.0,
        timefit="poly",
        freqfit="line",
        flagdimension="freqtime",
        extendflags=False,
        timedevscale=4.0,
        freqdevscale=4.0,
        spectralmax=500.0,
        extendpols=False,
        growaround=False,
        flagneartime=False,
        flagnearfreq=False,
        action="apply",
        flagbackup=True,
        overwrite=True,
        writeflags=True,
    )

    flagdata(vis=msvis, mode="summary", datacolumn="corrected", name="flagr2.after_rflag.summary")
    flagdata(
        vis=msvis,
        mode="extend",
        field=config.calfields,
        datacolumn="corrected",
        clipzeros=True,
        ntime="scan",
        extendflags=False,
        extendpols=False,
        growtime=90.0,
        growfreq=90.0,
        growaround=False,
        flagneartime=False,
        flagnearfreq=False,
        action="apply",
        flagbackup=True,
        overwrite=True,
        writeflags=True,
    )
    flagdata(vis=msvis, mode="summary", datacolumn="corrected", name="flagr2.after_extend.summary")

    # Target field: moderate flagging. More careful target flagging should be
    # done during self-calibration or event-specific inspection.
    if not config.solar_burst:
        flagdata(
            vis=msvis,
            mode="tfcrop",
            datacolumn="corrected",
            field=config.tarfield,
            ntime="scan",
            timecutoff=6.0,
            freqcutoff=5.0,
            timefit="poly",
            freqfit="line",
            flagdimension="freqtime",
            extendflags=False,
            timedevscale=5.0,
            freqdevscale=5.0,
            extendpols=False,
            growaround=False,
            action="apply",
            flagbackup=True,
            overwrite=True,
            writeflags=True,
        )
        flagdata(vis=msvis, field=config.tarfield, mode="summary", datacolumn="corrected", name="flagr2.after_tfcrop_tar.summary")

        flagdata(
            vis=msvis,
            mode="rflag",
            datacolumn="corrected",
            field=config.tarfield,
            timecutoff=5.0,
            freqcutoff=5.0,
            timefit="poly",
            freqfit="poly",
            flagdimension="freqtime",
            extendflags=False,
            timedevscale=5.0,
            freqdevscale=5.0,
            spectralmax=500.0,
            extendpols=False,
            growaround=False,
            flagneartime=False,
            flagnearfreq=False,
            action="apply",
            flagbackup=True,
            overwrite=True,
            writeflags=True,
        )
        flagdata(vis=msvis, field=config.tarfield, mode="summary", datacolumn="corrected", name="flagr2.after_rflag_tar.summary")

    append_log(
        config.logfile,
        (
            "Do flag after first round of calibration.\n"
            f"Applied tfcrop, rflag, and extend to {config.calfields}.\n"
            f"Applied tfcrop and rflag to {config.tarfield}.\n"
            "Flag after first round of calibration completed"
        ),
    )
