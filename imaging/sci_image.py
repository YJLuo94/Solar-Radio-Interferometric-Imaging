"""Science imaging for calibrated MeerKAT solar target data."""

from __future__ import annotations

from utils import append_log, ensure_clean_dir, get_casa_task


def make_science_image(config, msvis: str | None = None) -> str:
    """Generate the science-quality Stokes image for the selected time/frequency range."""
    tclean = get_casa_task("tclean")
    msvis = msvis or config.outputcalvis
    ensure_clean_dir("sciimg")

    imagename = "sciimg/sciimg"

    try:
        tclean(
            vis=msvis,
            datacolumn="corrected",
            imagename=imagename,
            timerange=config.timerange2,
            spw=config.spw2,
            imsize=config.imsize,
            cell=config.cell,
            stokes=config.stokes,
            gridder=config.gridder,
            specmode="mfs",
            phasecenter="",
            wprojplanes=config.wprojplanes,
            deconvolver=config.deconvolver,
            restoration=True,
            weighting="briggs",
            robust=config.robust,
            niter=config.niter,
            scales=config.multiscale,
            threshold=config.threshold,
            nterms=config.nterms,
            calcpsf=True,
            mask="",
            outlierfile="",
            pblimit=config.pbthreshold,
            restoringbeam=config.restoringbeam,
            parallel=config.doparallel,
        )
        print("Science image completed")
        append_log(
            config.logfile,
            (
                "Do science image.\n"
                f"Timerange: {config.timerange2}\n"
                f"Frequency range: {config.spw2}\n"
                f"Successfully made science image: {imagename}.\n"
                "Science image completed"
            ),
        )
    except Exception as exc:
        print(f"{imagename} failed, see log for reason")
        append_log(config.logfile, f"Do science image.\nScience image failed: {exc}")
        raise

    return imagename
