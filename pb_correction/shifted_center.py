"""Primary-beam correction for off-axis MeerKAT solar imaging.

These routines preserve the coordinate-offset logic from the full-disk science
imaging script: the CASA image is centered on the solar disk, but the MeerKAT
primary beam is evaluated relative to the original telescope pointing center.
The RA/Dec offset between the solar disk center and pointing center must
therefore be included when evaluating the PB model.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np

from utils import get_image_tool


def _image_frequency_mhz(csys: dict) -> float:
    """Return the image reference frequency in MHz from a CASA coordsys record."""
    try:
        return csys["spectral1"]["wcs"]["crval"] / 1e6
    except KeyError:
        return csys["spectral2"]["wcs"]["crval"] / 1e6


def _pixel_scale_deg(csys: dict) -> float:
    """Return absolute pixel size in degrees from a CASA coordsys record."""
    cdelt = abs(csys["direction0"]["cdelt"][0])
    unit = csys["direction0"]["units"][0]
    if unit == "rad":
        cdelt = np.rad2deg(cdelt)
    elif unit == "'":
        cdelt /= 60.0
    return cdelt


def _offset_grids(shape, cdelt_deg: float, shifted_ra_deg: float, shifted_dec_deg: float):
    """Return RA/Dec offset grids in degrees for a CASA image array."""
    cx, cy = shape[0] // 2, shape[1] // 2
    x = np.linspace(-cx, cx - 1, shape[0])
    y = np.linspace(-cy, cy - 1, shape[1])
    xx, yy = np.meshgrid(x, y)
    # Preserve the orientation used in the tested legacy script.
    xx = xx.T * cdelt_deg + shifted_ra_deg
    yy = yy.T * cdelt_deg + shifted_dec_deg
    return xx, yy


def _write_image_like(inpimage: str, outimage: str, data, overwrite: bool = True) -> None:
    """Copy a CASA image table and replace its data chunk."""
    outpath = Path(outimage)
    if outpath.exists():
        if overwrite:
            shutil.rmtree(outpath)
        else:
            raise FileExistsError(f"Output CASA image already exists: {outimage}")
    shutil.copytree(inpimage, outimage)
    ia = get_image_tool()
    ia.open(outimage)
    ia.putchunk(data)
    ia.done()


def do_pb_corr_shifted_center_katbeam(
    inpimage: str,
    shifted_ra_deg: float = 0.0,
    shifted_dec_deg: float = 0.0,
    pb_minval: float | None = 1e-6,
    nan_to_one: bool = False,
    pbband: str = "LBand",
    overwrite: bool = True,
) -> tuple[str, str]:
    """Apply katbeam PB correction with a pointing-to-Sun coordinate offset.

    Parameters
    ----------
    inpimage
        Input CASA image.
    shifted_ra_deg, shifted_dec_deg
        Offset, in degrees, from the telescope pointing center to the solar disk
        center in the image coordinate frame.
    pb_minval
        Minimum PB value used to avoid division by zero or extreme corrections.
    nan_to_one
        If true, divide directly by the PB array. If false, preserve NaNs in the
        PB model as NaNs in the corrected image.
    pbband
        MeerKAT band: ``"LBand"``, ``"SBand"``, or ``"UHF"``.
    overwrite
        Replace existing output CASA image directories.

    Returns
    -------
    tuple[str, str]
        ``(pb_image, pb_corrected_image)``.
    """
    from katbeam import JimBeam

    if pbband == "LBand":
        pbeam = JimBeam("MKAT-AA-L-JIM-2020")
    elif pbband == "SBand":
        pbeam = JimBeam("MKAT-AA-S-JIM-2020")
    elif pbband == "UHF":
        pbeam = JimBeam("MKAT-AA-UHF-JIM-2020")
    else:
        raise ValueError("pbband must be one of 'LBand', 'SBand', or 'UHF'.")

    ia = get_image_tool()
    ia.open(inpimage)
    csys = ia.coordsys().torecord()
    imgdata = ia.getchunk()
    shape = imgdata.shape
    ia.close()

    freq_mhz = _image_frequency_mhz(csys)
    cdelt_deg = _pixel_scale_deg(csys)
    xx, yy = _offset_grids(shape, cdelt_deg, shifted_ra_deg, shifted_dec_deg)

    beam_i = pbeam.I(xx, yy, freq_mhz)
    if len(shape) == 4:
        beam_i = beam_i[:, :, None, None]

    if pb_minval is not None:
        beam_i = np.where(beam_i < pb_minval, pb_minval, beam_i)

    pbcor_imgdata = imgdata / beam_i if nan_to_one else np.where(np.isnan(beam_i), np.nan, imgdata / beam_i)

    pbimage = inpimage.replace(".image", ".katbeam.pb")
    pbcorimage = inpimage.replace(".image", ".katbeam_pbcor.image")
    _write_image_like(inpimage, pbimage, beam_i, overwrite=overwrite)
    _write_image_like(inpimage, pbcorimage, pbcor_imgdata, overwrite=overwrite)
    return pbimage, pbcorimage


def do_pb_corr_shifted_center_holo(
    inpimage: str,
    beam_file: str,
    shifted_ra_deg: float = 0.0,
    shifted_dec_deg: float = 0.0,
    pb_minval: float | None = 1e-6,
    nan_to_one: bool = False,
    overwrite: bool = True,
) -> tuple[str, str]:
    """Apply holography-based PB correction with a pointing-to-Sun offset."""
    from scipy.interpolate import RegularGridInterpolator

    beam_data = np.load(beam_file)
    beam_i_all = beam_data["beam"][0]
    freqs = beam_data["freq_MHz"]
    offsets = beam_data["offsets"]

    ia = get_image_tool()
    ia.open(inpimage)
    csys = ia.coordsys().torecord()
    imgdata = ia.getchunk()
    shape = imgdata.shape
    ia.close()

    freq_mhz = _image_frequency_mhz(csys)
    cdelt_deg = _pixel_scale_deg(csys)
    xx, yy = _offset_grids(shape, cdelt_deg, shifted_ra_deg, shifted_dec_deg)

    idx = int(np.argmin(np.abs(freqs - freq_mhz)))
    log_beam = np.log10(np.abs(beam_i_all[idx]) + 1e-6)
    interp = RegularGridInterpolator((offsets, offsets), log_beam, bounds_error=False, fill_value=np.nan)
    points = np.stack([yy.ravel(), xx.ravel()], axis=-1)
    logpb = interp(points).reshape(shape[0], shape[1])
    pb = 10.0 ** logpb
    if len(shape) == 4:
        pb = pb[:, :, None, None]

    if pb_minval is not None:
        pb = np.where(pb < pb_minval, pb_minval, pb)

    pbcor_imgdata = imgdata / pb if nan_to_one else np.where(np.isnan(pb), np.nan, imgdata / pb)

    pbimage = inpimage.replace(".image", ".holopb")
    pbcorimage = inpimage.replace(".image", ".holo_pbcor.image")
    _write_image_like(inpimage, pbimage, pb, overwrite=overwrite)
    _write_image_like(inpimage, pbcorimage, pbcor_imgdata, overwrite=overwrite)
    return pbimage, pbcorimage
