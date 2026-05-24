"""Measurement Set inspection and partitioning utilities."""

from __future__ import annotations

from pathlib import Path

try:
    import matplotlib.pyplot as plt
except Exception:  # CASA may not always provide a fully usable pyplot backend.
    plt = None

from utils import append_log, get_casa_task, get_msmetadata_tool


def write_ms_information(config) -> None:
    """Run ``listobs`` and ``plotants`` for the input Measurement Set."""
    listobs = get_casa_task("listobs")
    plotants = get_casa_task("plotants")

    listfile = f"{config.visname}.listobs"
    figfile = f"{config.visname}.ants.png"

    listobs(vis=config.orims, listfile=listfile, overwrite=True)
    plotants(vis=config.orims, figfile=figfile)
    if plt is not None:
        plt.close()

    append_log(
        config.logfile,
        (
            "Do information step.\n"
            f"Listobs file: {listfile}\n"
            f"Antenna position image: {figfile}\n"
            "Information step completed"
        ),
    )


def partition_ms(config) -> str:
    """Split/average the input MS and optionally create an MMS for parallel CASA.

    This is the modular version of the original ``do_partition`` block.  It
    keeps the original convention of creating ``*.cal0.ms`` from the input MS.
    """
    mstransform = get_casa_task("mstransform")
    msmd = get_msmetadata_tool()

    outputvis = config.msvis0
    chanaverage = config.channelbin > 1
    correlation = "" if config.dopol else "XX,YY"

    msmd.open(config.orims)
    nscans = msmd.nscans()
    msmd.done()

    if not config.domms:
        nscan = 1
    elif config.scans == "":
        nscan = nscans
    else:
        nscan = len(config.scans.split(","))

    mstransform(
        vis=config.orims,
        outputvis=outputvis,
        spw=config.spw_s,
        createmms=config.domms,
        datacolumn="DATA",
        chanaverage=chanaverage,
        chanbin=config.channelbin,
        scan=config.scans,
        numsubms=nscan,
        separationaxis="scan",
        keepflags=True,
        usewtspectrum=True,
        nthreads=config.ncpus,
        correlation=correlation,
    )

    append_log(
        config.logfile,
        (
            "Do partition step.\n"
            f"Split and averaged MS file: {outputvis}\n"
            "Partition step completed"
        ),
    )
    return outputvis
