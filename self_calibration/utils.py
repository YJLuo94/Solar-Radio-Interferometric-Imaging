"""Utility functions shared by the self-calibration modules.

The functions here intentionally keep the naming conventions from the legacy
CASA scripts, because many downstream plots and file lookups depend on those
names.
"""

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import numpy as np

from utils import ensure_dir, get_casa_task, get_image_tool


def get_selfcal_config(config):
    """Return ``config.selfcal`` with a clear error message if it is missing."""
    if not hasattr(config, "selfcal"):
        raise AttributeError(
            "The main configuration does not define 'selfcal'. "
            "Use the updated config.py or attach a SelfCalConfig instance."
        )
    return config.selfcal


def as_path(path: str | Path) -> Path:
    """Return a path object without resolving non-existent CASA table paths."""
    return Path(str(path))


def make_dirs(config) -> None:
    """Create the standard self-calibration output directories."""
    sc = get_selfcal_config(config)
    for path in [
        sc.slfcaldir,
        sc.imagedir,
        sc.maskdir,
        sc.imagedir_slfcaled,
        sc.caltbdir,
        sc.figdir,
    ]:
        ensure_dir(path)


def generate_spws(nchan_total: int = 4096, nchan_per_spw: int = 32, spw_id: int = 0) -> List[str]:
    """Generate CASA SPW channel-selection strings.

    Example
    -------
    ``generate_spws(4096, 32)`` returns ``['0:0~31', '0:32~63', ...]``.
    """
    return [f"{spw_id}:{i}~{min(i + nchan_per_spw - 1, nchan_total - 1)}" for i in range(0, nchan_total, nchan_per_spw)]


def parse_spw(spw: str) -> Tuple[int, int]:
    """Return the first and last channel from a string such as ``0:32~63``."""
    chan_part = spw.split(":", 1)[1]
    ch_start, ch_end = chan_part.split("~")
    return int(ch_start), int(ch_end)


def spw_tag_from_spw(spw: str) -> str:
    """Return the channel tag used in file names, e.g. ``0032-0063``."""
    ch_start, ch_end = parse_spw(spw)
    return f"{ch_start:04d}-{ch_end:04d}"


def spw_image_tag(spw: str) -> str:
    """Return the full ``spw_0_XXXX-YYYY`` tag used for FITS products."""
    ch_start, ch_end = parse_spw(spw)
    return f"spw_0_{ch_start:04d}-{ch_end:04d}"


def frequency_axis(config, n_panels: int | None = None) -> Tuple[List[str], List[float]]:
    """Return panel tags and mid-channel frequencies in GHz."""
    sc = get_selfcal_config(config)
    n_panels = n_panels or sc.nchan_total // sc.nchan_per_spw
    panel_tags: List[str] = []
    mid_freqs: List[float] = []
    for i in range(n_panels):
        ch_start = i * sc.nchan_per_spw
        ch_end = min(ch_start + sc.nchan_per_spw - 1, sc.nchan_total - 1)
        mid_ch = (ch_start + ch_end) / 2.0
        panel_tags.append(f"{ch_start:04d}-{ch_end:04d}")
        mid_freqs.append(sc.freq_start_ghz + mid_ch * sc.freq_step_ghz)
    return panel_tags, mid_freqs


def parse_cell_arcsec(cell: str) -> float:
    """Parse a CASA cell string, e.g. ``2.5arcsec`` or ``2.5 arcsec``."""
    try:
        return float(re.findall(r"[\d.]+", str(cell))[0])
    except Exception as exc:
        raise ValueError(f"Failed to parse cell size from {cell!r}") from exc


def remove_casa_products(imagename: str | Path, suffixes: Sequence[str] | None = None) -> None:
    """Remove intermediate CASA image products for a given image root."""
    suffixes = suffixes or [".flux", ".mask", ".model", ".psf", ".residual", ".sumwt", ".pb"]
    for ext in suffixes:
        path = Path(str(imagename) + ext)
        if path.exists():
            shutil.rmtree(path)


def casa_table_exists(path: str | Path) -> bool:
    """Return True if a CASA table/image directory exists."""
    return Path(path).exists()


def split_tag_to_timerange_tag(timerange: str) -> str:
    """Create a compact tag from a CASA timerange string.

    The default event keeps the historical ``112028`` tag. This helper is used
    only when users want to derive a tag automatically for other events.
    """
    digits = re.sub(r"\D", "", timerange.split("~", 1)[0])
    return digits[-6:] if len(digits) >= 6 else digits


def copy_ms_safely(input_ms: str | Path, output_ms: str | Path, overwrite: bool = False) -> None:
    """Copy an MS directory without accidentally overwriting by default."""
    input_ms = Path(input_ms)
    output_ms = Path(output_ms)
    if output_ms.exists():
        if not overwrite:
            print(f"Working MS already exists: {output_ms}")
            return
        shutil.rmtree(output_ms)
    print(f"Copying {input_ms} -> {output_ms}")
    shutil.copytree(input_ms, output_ms)


def clear_calibration_and_model(vis: str | Path) -> None:
    """Run CASA ``clearcal`` and ``delmod`` for an MS."""
    clearcal = get_casa_task("clearcal")
    delmod = get_casa_task("delmod")
    clearcal(str(vis))
    delmod(str(vis))


def split_ms(vis: str | Path, outputvis: str | Path, datacolumn: str = "corrected", **kwargs) -> None:
    """Thin wrapper around CASA ``split`` with path conversion."""
    split = get_casa_task("split")
    split(vis=str(vis), outputvis=str(outputvis), datacolumn=datacolumn, **kwargs)


def read_msinfo(vis: str | Path):
    """Read MS metadata using SunCASA's ``helioimage2fits`` helper."""
    from suncasa.utils import helioimage2fits as hf

    return hf.read_msinfo(str(vis))


def register_image(vis: str | Path, imagefile: str | Path, fitsfile: str | Path, config, msinfo=None) -> None:
    """Register a CASA image into solar FITS coordinates using SunCASA."""
    from suncasa.utils import helioimage2fits as hf

    sc = get_selfcal_config(config)
    msinfo = msinfo or hf.read_msinfo(str(vis))
    hf.imreg(
        vis=str(vis),
        msinfo=msinfo,
        imagefile=str(imagefile),
        fitsfile=str(fitsfile),
        ephem=sc.ephem,
        timerange=sc.timerange,
        usephacenter=False,
        verbose=True,
    )
