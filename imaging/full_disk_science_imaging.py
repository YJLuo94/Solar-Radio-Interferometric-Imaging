"""Full-disk science imaging after MeerKAT solar self-calibration.

This module is a modular translation of ``docs/legacy/disk_img_slfcal.py``. It
creates final Stokes I/V full-disk images for selected time intervals and
frequency chunks, applies both holography and katbeam primary-beam corrections,
and exports original and PB-corrected FITS/Tb products.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List

import numpy as np
from astropy.coordinates import SkyCoord
from astropy.time import Time

from pb_correction.shifted_center import (
    do_pb_corr_shifted_center_holo,
    do_pb_corr_shifted_center_katbeam,
)
from utils import ensure_dir, get_casa_task, get_msmetadata_tool


def get_full_disk_config(config):
    """Return ``config.full_disk_imaging`` with a clear error if missing."""
    if not hasattr(config, "full_disk_imaging"):
        raise AttributeError("The configuration does not define 'full_disk_imaging'.")
    return config.full_disk_imaging


def generate_spws(nchan_total: int, nchan_per_spw: int, spw_id: int = 0) -> List[str]:
    """Generate CASA SPW channel-selection strings."""
    return [f"{spw_id}:{i}~{min(i + nchan_per_spw - 1, nchan_total - 1)}" for i in range(0, nchan_total, nchan_per_spw)]


def generate_timeranges(fd) -> List[str]:
    """Generate CASA timerange strings from the full-disk imaging config."""
    start = Time(fd.timerange_start)
    timeranges = []
    for i in range(fd.n_timeranges):
        ti = Time(start + i * fd.timerange_step_sec / 86400.0, format="datetime")
        te = Time(start + (i * fd.timerange_step_sec + fd.timerange_duration_sec) / 86400.0, format="datetime")
        trange = ti.iso.replace("-", "/").replace(" ", "/") + "~" + te.iso.replace("-", "/").replace(" ", "/")
        timeranges.append(trange)
    if fd.time_indices:
        return [timeranges[i] for i in fd.time_indices]
    return timeranges


def time_subfolder_from_timerange(trange: str) -> str:
    """Return the historical HH_MM_SS tag from a CASA timerange string."""
    return trange[11:19].replace(":", "_")


def pointing_to_solar_offset(fd) -> tuple[float, float]:
    """Return solar-center minus pointing-center offset in degrees."""
    c_pointing = SkyCoord(fd.pointing_coord)
    c_sun = SkyCoord(fd.solar_coord)
    return c_sun.ra.value - c_pointing.ra.value, c_sun.dec.value - c_pointing.dec.value


def _frequency_tag(msvis: str, spw: str) -> str:
    """Return rounded mid-frequency tag, e.g. ``0960MHz``."""
    msmd = get_msmetadata_tool()
    msmd.open(msvis)
    try:
        start_chan = int(spw.split(":", 1)[1].split("~", 1)[0])
        end_chan = int(spw.split("~", 1)[1]) + 1
        freqs_hz = msmd.chanfreqs(0)[start_chan:end_chan]
    finally:
        msmd.close()
    midfreq_mhz = float(np.mean(freqs_hz) / 1e6)
    return f"{int(round(midfreq_mhz)):04d}MHz"


def _register_fits(vis: str, msinfo, imagefile: str, fitsfile: str, trange: str, fd, to_tb: bool = False) -> None:
    """Register a CASA image into helioprojective FITS coordinates."""
    from suncasa.utils import helioimage2fits as hf

    hf.imreg(
        vis=vis,
        msinfo=msinfo,
        imagefile=imagefile,
        fitsfile=fitsfile,
        timerange=trange,
        ephem=fd.ephem,
        usephacenter=False,
        toTb=to_tb,
    )


def _make_output_dirs(fd, time_subfolder: str) -> None:
    """Create all output folders used by the full-disk imaging workflow."""
    base_dirs = [
        fd.fits_root,
        fd.tbf_root,
        fd.fits_corr_holo_root,
        fd.tbf_corr_holo_root,
        fd.fits_corr_kat_root,
        fd.tbf_corr_kat_root,
    ]
    ensure_dir(fd.workdir)
    for base in base_dirs:
        ensure_dir(base)
        ensure_dir(Path(base) / time_subfolder)


def _remove_intermediate_products(imagename: str) -> None:
    """Remove intermediate CASA products that are not needed downstream."""
    import shutil

    for ext in [".flux", ".mask", ".model", ".residual", ".sumwt", ".pb", ".psf"]:
        path = Path(imagename + ext)
        if path.exists():
            shutil.rmtree(path)


def run_full_disk_science_imaging(config) -> list:
    """Run full-disk science imaging using the configured self-calibrated MS.

    Returns
    -------
    list
        Per-time, per-frequency success records, matching the spirit of the
        legacy ``success_log`` variable.
    """
    from suncasa.utils import helioimage2fits as hf

    fd = get_full_disk_config(config)
    ensure_dir(fd.workdir)
    os.chdir(fd.workdir)

    for base_dir in [
        fd.fits_root,
        fd.tbf_root,
        fd.fits_corr_holo_root,
        fd.tbf_corr_holo_root,
        fd.fits_corr_kat_root,
        fd.tbf_corr_kat_root,
    ]:
        ensure_dir(base_dir)

    msinfo = hf.read_msinfo(fd.msvis)
    shifted_ra_deg, shifted_dec_deg = pointing_to_solar_offset(fd)
    spws = generate_spws(fd.nchan_total, fd.nchan_per_spw, fd.spw_id)
    timeranges = generate_timeranges(fd)
    tclean = get_casa_task("tclean")

    success_log = []
    for trange in timeranges:
        time_subfolder = time_subfolder_from_timerange(trange)
        temp_path = Path(fd.workdir) / time_subfolder
        ensure_dir(temp_path)
        _make_output_dirs(fd, time_subfolder)
        os.chdir(temp_path)

        success_log_t = []
        for i, spw in enumerate(spws):
            spw_tag = f"{i:04d}"
            freq_tag = _frequency_tag(fd.msvis, spw)
            chn_result = {"chn": i, "spw": spw, "freq_tag": freq_tag}

            for stokes in fd.stokes_list:
                imagename = f"chn_{time_subfolder}_{spw_tag}_{freq_tag}_{stokes}"
                inpimage = imagename + ".image"
                try:
                    tclean(
                        vis=fd.msvis,
                        imagename=imagename,
                        spw=spw,
                        timerange=trange,
                        datacolumn=fd.datacolumn,
                        imsize=fd.imsize,
                        cell=fd.cell,
                        phasecenter=fd.phasecenter,
                        stokes=stokes,
                        specmode=fd.specmode,
                        niter=fd.niter,
                        pblimit=fd.pblimit,
                        interactive=fd.interactive,
                        restoringbeam=fd.restoringbeam,
                        weighting=fd.weighting,
                        robust=fd.robust,
                        gridder=fd.gridder,
                        gain=fd.gain,
                    )
                    _remove_intermediate_products(imagename)

                    if fd.do_holography_pbcor:
                        _, holo_pbcor_image = do_pb_corr_shifted_center_holo(
                            inpimage,
                            beam_file=fd.holography_beam_file,
                            shifted_ra_deg=shifted_ra_deg,
                            shifted_dec_deg=shifted_dec_deg,
                            pb_minval=fd.pb_minval,
                            nan_to_one=fd.nan_to_one,
                        )
                        _register_fits(
                            fd.msvis,
                            msinfo,
                            holo_pbcor_image,
                            str(Path(fd.fits_corr_holo_root) / time_subfolder / f"{imagename}.fits"),
                            trange,
                            fd,
                        )
                        if fd.export_tb:
                            _register_fits(
                                fd.msvis,
                                msinfo,
                                holo_pbcor_image,
                                str(Path(fd.tbf_corr_holo_root) / time_subfolder / f"{imagename}.tb.fits"),
                                trange,
                                fd,
                                to_tb=True,
                            )

                    if fd.do_katbeam_pbcor:
                        _, kat_pbcor_image = do_pb_corr_shifted_center_katbeam(
                            inpimage,
                            shifted_ra_deg=shifted_ra_deg,
                            shifted_dec_deg=shifted_dec_deg,
                            pb_minval=fd.pb_minval,
                            nan_to_one=fd.nan_to_one,
                            pbband=fd.pbband,
                        )
                        _register_fits(
                            fd.msvis,
                            msinfo,
                            kat_pbcor_image,
                            str(Path(fd.fits_corr_kat_root) / time_subfolder / f"{imagename}.fits"),
                            trange,
                            fd,
                        )
                        if fd.export_tb:
                            _register_fits(
                                fd.msvis,
                                msinfo,
                                kat_pbcor_image,
                                str(Path(fd.tbf_corr_kat_root) / time_subfolder / f"{imagename}.tb.fits"),
                                trange,
                                fd,
                                to_tb=True,
                            )

                    if fd.export_original:
                        _register_fits(
                            fd.msvis,
                            msinfo,
                            inpimage,
                            str(Path(fd.fits_root) / time_subfolder / f"{imagename}.fits"),
                            trange,
                            fd,
                        )
                        if fd.export_tb:
                            _register_fits(
                                fd.msvis,
                                msinfo,
                                inpimage,
                                str(Path(fd.tbf_root) / time_subfolder / f"{imagename}.tb.fits"),
                                trange,
                                fd,
                                to_tb=True,
                            )

                    chn_result[stokes] = True
                except Exception as exc:
                    print(f"Failed: {imagename} | Time: {trange} | Error: {exc}")
                    chn_result[stokes] = False

            success_log_t.append(chn_result)
        success_log.append(success_log_t)

    return success_log
