"""Primary-beam correction utilities using the katbeam MeerKAT beam model."""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

from utils import append_log, get_image_tool


def do_pb_corr(inpimage: str, pbthreshold: float = 0, pbband: str = "LBand", overwrite: bool = True) -> tuple[str, str]:
    """Apply a katbeam primary-beam correction to a CASA image.

    Parameters
    ----------
    inpimage
        Input CASA image name.
    pbthreshold
        Cutoff threshold below which PB-corrected pixels are set to NaN.
    pbband
        MeerKAT band. Must be ``"LBand"``, ``"SBand"``, or ``"UHF"``.
    overwrite
        If true, existing PB and PB-corrected image directories are replaced.

    Returns
    -------
    tuple[str, str]
        ``(pb_image, pb_corrected_image)``.
    """
    from katbeam import JimBeam

    ia = get_image_tool()

    pbcorimage = inpimage.replace(".image", ".katbeam_pbcor.image")
    pbimage = inpimage.replace(".image", ".katbeam.pb")

    ia.open(inpimage)
    csys = ia.coordsys().torecord()
    imgdata = ia.getchunk()
    shape = ia.shape()
    ia.close()

    cx, cy = shape[0] // 2, shape[1] // 2

    # Size of each pixel.
    cdelt = np.abs(csys["direction0"]["cdelt"][0])
    unit = csys["direction0"]["units"][0]
    if unit == "rad":
        cdelt = np.rad2deg(cdelt)
    elif unit == "'":  # arcmin
        cdelt /= 60.0

    # Frequency of image, converted from Hz to MHz.
    try:
        freq = csys["spectral1"]["wcs"]["crval"] / 1e6
    except KeyError:
        freq = csys["spectral2"]["wcs"]["crval"] / 1e6

    if pbband == "LBand":
        pbeam = JimBeam("MKAT-AA-L-JIM-2020")
    elif pbband == "SBand":
        pbeam = JimBeam("MKAT-AA-S-JIM-2020")
    elif pbband == "UHF":
        pbeam = JimBeam("MKAT-AA-UHF-JIM-2020")
    else:
        raise ValueError("pbband must be one of 'LBand', 'SBand', or 'UHF'.")

    x = np.linspace(-cx, cx + 1, shape[0])
    y = np.linspace(-cy, cy + 1, shape[1])
    xx, yy = np.meshgrid(x, y)

    # Convert pixel offsets into angular separations in degrees.
    xx *= cdelt
    yy *= cdelt

    beam_i = pbeam.I(xx, yy, freq)

    # Match PB shape with CASA image data for correction.
    if len(shape) == 4:
        beam_i = beam_i[:, :, None, None]

    pbcor_imgdata = imgdata / beam_i

    if pbthreshold > 0:
        pbcor_imgdata[beam_i < pbthreshold] = np.nan

    for outpath in [pbimage, pbcorimage]:
        if Path(outpath).exists() and overwrite:
            shutil.rmtree(outpath)

    shutil.copytree(inpimage, pbimage)
    ia.open(pbimage)
    ia.putchunk(beam_i)
    ia.close()

    shutil.copytree(inpimage, pbcorimage)
    ia.open(pbcorimage)
    ia.putchunk(pbcor_imgdata)
    ia.close()

    return pbimage, pbcorimage


def run_katbeam_pb_correction(config, imagename: str = "sciimg/sciimg") -> str:
    """Run katbeam PB correction on the science image from ``tclean``."""
    if config.deconvolver == "mtmfs":
        imagefile = f"{imagename}.image.tt0"
    else:
        imagefile = f"{imagename}.image"

    try:
        _, pbcor_image = do_pb_corr(imagefile, config.pbthreshold, config.pbband)
        print(f"Primary-beam-corrected image: {pbcor_image}")
        append_log(
            config.logfile,
            (
                "Do primary beam correction.\n"
                f"Primary-beam-corrected image: {pbcor_image}.\n"
                "Primary beam correction completed"
            ),
        )
        return pbcor_image
    except Exception as exc:
        print("Primary beam correction failed")
        append_log(config.logfile, f"Primary beam correction failed: {exc}")
        raise
