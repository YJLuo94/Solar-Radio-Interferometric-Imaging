"""Quick-look imaging for calibrated MeerKAT solar target data."""

from __future__ import annotations

from pathlib import Path

from utils import append_log, ensure_clean_dir, get_casa_task


def make_quicklook_image(config, msvis: str | None = None) -> str:
    """Generate a quick-look Stokes-I MFS image."""
    tclean = get_casa_task("tclean")
    msvis = msvis or config.outputcalvis
    ensure_clean_dir("qlimg")

    imagename = "qlimg/qlimage"

    try:
        tclean(
            vis=msvis,
            datacolumn="corrected",
            imagename=imagename,
            timerange=config.timerange1,
            spw=config.spw1,
            imsize=[2048, 2048],
            cell="2arcsec",
            stokes="I",
            gridder="standard",
            specmode="mfs",
            phasecenter="",
            weighting="briggs",
            robust=0,
            niter=2000,
            threshold=0,
            calcpsf=True,
            outlierfile="",
            pblimit=0,
            restoringbeam="",
            parallel=config.doparallel,
        )
        print("Quick-look image completed")
        append_log(
            config.logfile,
            (
                "Do quick-look image.\n"
                f"Timerange: {config.timerange1}\n"
                f"Frequency range: {config.spw1}\n"
                f"Successfully made quick-look image: {imagename}.\n"
                "Quick-look image completed"
            ),
        )
    except Exception as exc:
        print(f"{imagename} failed, see log for reason")
        append_log(
            config.logfile,
            f"Do quick-look image.\nQuick-look image failed: {exc}",
        )
        raise

    return imagename
