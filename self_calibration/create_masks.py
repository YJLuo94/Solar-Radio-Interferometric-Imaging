"""CLEAN mask generation for MeerKAT solar self-calibration."""

from __future__ import annotations

import glob
import os
from pathlib import Path

import numpy as np

from utils import ensure_dir, get_image_tool

from .utils import get_selfcal_config, parse_cell_arcsec


def create_full_disk_masks(config, output_round: str = "r1") -> list[str]:
    """Create circular full-disk masks from the pre-self-calibration images."""
    sc = get_selfcal_config(config)
    image_dir = Path(sc.imagedir) / "precal"
    mask_dir = ensure_dir(Path(sc.maskdir) / output_round)
    radius_pix = int(sc.full_disk_radius_arcsec / parse_cell_arcsec(sc.cell))
    ia = get_image_tool()
    created = []

    for image_file in sorted(glob.glob(str(image_dir / f"precal_{sc.split_tag}_spw_0_*.image"))):
        try:
            ia.open(image_file)
            shape = ia.shape()
            nx, ny = shape[0], shape[1]
            cx, cy = nx // 2, ny // 2
            csys = ia.coordsys().torecord()
            ia.done()

            mask_path = mask_dir / os.path.basename(image_file).replace(".image", ".mask")
            if mask_path.exists():
                import shutil
                shutil.rmtree(mask_path)

            ia.fromshape(str(mask_path), shape, csys)
            mask = ia.getchunk()
            mask[:] = 0
            yy, xx = np.ogrid[:ny, :nx]
            disk = (xx - cx) ** 2 + (yy - cy) ** 2 <= radius_pix**2
            # CASA image arrays use x, y, stokes, frequency ordering here.
            mask[:, :, 0, 0] = disk.T.astype(mask.dtype)
            ia.putchunk(mask)
            ia.done()
            created.append(str(mask_path))
            print(f"Created full-disk mask: {mask_path}")
        except Exception as exc:
            print(f"Failed to create mask for {image_file}: {exc}")
            try:
                ia.done()
            except Exception:
                pass
    return created


def create_peak_fraction_masks(config, source_round: str, output_round: str, fraction: float | None = None) -> list[str]:
    """Create masks from pixels above a fraction of the previous-round peak."""
    sc = get_selfcal_config(config)
    fraction = sc.peak_mask_fraction if fraction is None else fraction
    source_dir = Path(sc.imagedir_slfcaled) / source_round
    mask_dir = ensure_dir(Path(sc.maskdir) / output_round)
    ia = get_image_tool()
    created = []

    pattern = source_dir / f"slfcaled_{source_round}_{sc.split_tag}_spw_0_*.image"
    for image_file in sorted(glob.glob(str(pattern))):
        try:
            ia.open(image_file)
            shape = ia.shape()
            csys = ia.coordsys().torecord()
            data = ia.getchunk()
            peak = np.nanmax(data)
            threshold = fraction * peak
            mask_data = (data >= threshold).astype(int)
            ia.done()

            mask_path = mask_dir / os.path.basename(image_file).replace(".image", ".mask")
            if mask_path.exists():
                import shutil
                shutil.rmtree(mask_path)
            ia.fromshape(str(mask_path), shape, csys)
            ia.putchunk(mask_data)
            ia.done()
            created.append(str(mask_path))
            print(f"Created peak-fraction mask: {mask_path} (threshold={threshold:.3g})")
        except Exception as exc:
            print(f"Failed to create peak-fraction mask for {image_file}: {exc}")
            try:
                ia.done()
            except Exception:
                pass
    return created


def build_mask_pattern(config, round_name: str) -> str:
    """Return the filename pattern for the mask used by a self-calibration round."""
    sc = get_selfcal_config(config)
    round_cfg = sc.get_round(round_name)
    if round_cfg.mask_mode in {"full_disk", "reuse_r1"}:
        return str(Path(sc.maskdir) / "r1" / f"precal_{sc.split_tag}_spw_0_{{spw_tag}}.mask")
    if round_cfg.mask_mode == "peak_fraction":
        source_round = round_cfg.mask_source_round or f"r{int(round_name[1:]) - 1}"
        return str(Path(sc.maskdir) / round_name / f"slfcaled_{source_round}_{sc.split_tag}_spw_0_{{spw_tag}}.mask")
    if round_cfg.mask_mode == "none":
        return ""
    raise ValueError(f"Unknown mask mode for {round_name}: {round_cfg.mask_mode}")


def ensure_round_masks(config, round_name: str) -> None:
    """Create masks required by a round when requested by the round config."""
    sc = get_selfcal_config(config)
    round_cfg = sc.get_round(round_name)
    if round_cfg.mask_mode == "full_disk":
        create_full_disk_masks(config, output_round="r1")
    elif round_cfg.mask_mode == "peak_fraction":
        source_round = round_cfg.mask_source_round or f"r{int(round_name[1:]) - 1}"
        create_peak_fraction_masks(config, source_round=source_round, output_round=round_name, fraction=round_cfg.peak_fraction)
    elif round_cfg.mask_mode in {"reuse_r1", "none"}:
        return
    else:
        raise ValueError(f"Unknown mask mode: {round_cfg.mask_mode}")
