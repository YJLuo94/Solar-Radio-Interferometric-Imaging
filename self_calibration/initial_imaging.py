"""Initial and post-self-calibration imaging helpers."""

from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import sunpy.map

from utils import ensure_dir, get_casa_task

from .utils import (
    frequency_axis,
    generate_spws,
    get_selfcal_config,
    read_msinfo,
    register_image,
    remove_casa_products,
    spw_image_tag,
)


def image_spw_sequence(
    config,
    vis: str,
    output_dir: str,
    image_prefix: str,
    niter: int,
    robust: float,
    datacolumn: str = "data",
    savemodel: str | None = None,
    mask_pattern: str | None = None,
    uvrange: str = "",
    cleanup: bool = True,
) -> List[str]:
    """Image all configured SPW chunks and register them to FITS.

    Parameters
    ----------
    mask_pattern : str, optional
        Format string receiving ``spw_tag`` and ``spw_image_tag``. For example:
        ``'/path/precal_{split_tag}_spw_0_{spw_tag}.mask'``.
    """
    sc = get_selfcal_config(config)
    output_dir = ensure_dir(output_dir)
    tclean = get_casa_task("tclean")
    msinfo = read_msinfo(vis)
    fits_list: List[str] = []

    for spw in generate_spws(sc.nchan_total, sc.nchan_per_spw, sc.spw_id):
        tag = spw_image_tag(spw)
        spw_tag = tag.replace("spw_0_", "")
        imagename = output_dir / f"{image_prefix}_{tag}"
        imagefile = str(imagename) + ".image"
        fitsfile = str(imagename) + ".fits"
        mask = ""
        usemask = "auto-multithresh"
        if mask_pattern:
            mask = mask_pattern.format(
                split_tag=sc.split_tag,
                spw_tag=spw_tag,
                spw_image_tag=tag,
            )
            usemask = "user"

        print(f">>> Imaging {spw} -> {imagename}")
        kwargs = dict(
            vis=str(vis),
            imagename=str(imagename),
            spw=spw,
            timerange=sc.timerange,
            imsize=[sc.npix, sc.npix],
            cell=sc.cell,
            weighting="briggs",
            robust=robust,
            niter=niter,
            interactive=False,
            specmode="mfs",
            stokes=sc.stokes,
            gain=sc.clean_gain,
            datacolumn=datacolumn,
        )
        if savemodel:
            kwargs["savemodel"] = savemodel
        if uvrange:
            kwargs["uvrange"] = uvrange
        if mask_pattern:
            kwargs["usemask"] = usemask
            kwargs["mask"] = mask
        if sc.restoringbeam is not None:
            kwargs["restoringbeam"] = sc.restoringbeam

        tclean(**kwargs)

        if not os.path.exists(imagefile):
            print(f"Skipping {tag}: .image was not created.")
            continue

        try:
            register_image(vis, imagefile, fitsfile, config, msinfo=msinfo)
            fits_list.append(fitsfile)
        except Exception as exc:
            print(f"Image registration failed for {imagefile}: {exc}")

        if cleanup:
            remove_casa_products(str(imagename))

    return fits_list


def plot_frequency_panel(config, fits_dir: str, prefix: str, output_png: str) -> str:
    """Create the 16x8 frequency-labeled panel plot used for quick inspection."""
    sc = get_selfcal_config(config)
    panel_tags, mid_freqs = frequency_axis(config)
    fits_dict = {}
    for fname in glob.glob(os.path.join(fits_dir, f"{prefix}_spw_0_*.fits")):
        basename = os.path.basename(fname)
        parts = basename.split("_spw_0_")
        if len(parts) == 2:
            fits_dict[parts[-1].replace(".fits", "")] = fname

    fig, axes = plt.subplots(
        sc.panel_nrows,
        sc.panel_ncols,
        figsize=sc.panel_figsize,
        gridspec_kw={"wspace": 0.0, "hspace": 0.0},
    )

    for idx, (spw_tag, freq) in enumerate(zip(panel_tags, mid_freqs)):
        row, col = divmod(idx, sc.panel_ncols)
        ax = axes[row][col]
        ax.set_xticks([])
        ax.set_yticks([])
        fname = fits_dict.get(spw_tag)
        plotted = False
        if fname and os.path.exists(fname):
            try:
                m = sunpy.map.Map(fname)
                ax.imshow(m.data, cmap=sc.panel_cmap, origin="lower", aspect="equal")
                plotted = True
            except Exception as exc:
                print(f"Failed to plot {spw_tag}: {exc}")
        if plotted:
            ax.text(
                0.05,
                0.92,
                f"{freq:.3f} GHz",
                transform=ax.transAxes,
                fontsize=6,
                color="white",
                ha="left",
                va="top",
                bbox=dict(facecolor="black", alpha=0.3, lw=0),
            )
        else:
            ax.imshow(np.ones((10, 10)), cmap="gray", vmin=0, vmax=1, origin="lower", aspect="equal")
            ax.text(0.05, 0.92, f"{freq:.3f} GHz", transform=ax.transAxes, fontsize=6, color="gray", ha="left", va="top")

    output_png = str(output_png)
    Path(output_png).parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_png, dpi=sc.panel_dpi)
    plt.close(fig)
    print(f"Frequency panel saved to: {output_png}")
    return output_png


def run_precal_imaging(config) -> list[str]:
    """Generate pre-self-calibration images for inspection and mask creation."""
    sc = get_selfcal_config(config)
    vis = str(Path(sc.slfcaldir) / sc.seed_ms_name)
    outdir = str(Path(sc.imagedir) / "precal")
    prefix = f"precal_{sc.split_tag}"
    fits_list = image_spw_sequence(
        config,
        vis=vis,
        output_dir=outdir,
        image_prefix=prefix,
        niter=sc.precal_niter,
        robust=sc.precal_robust,
        datacolumn="data",
        cleanup=True,
    )
    plot_frequency_panel(config, outdir, prefix, str(Path(outdir) / f"precal_image_{sc.split_tag}.png"))
    return fits_list


def image_selfcal_round(config, round_name: str, vis: str) -> list[str]:
    """Image the MS produced by a self-calibration round."""
    sc = get_selfcal_config(config)
    round_cfg = sc.get_round(round_name)
    outdir = str(Path(sc.imagedir_slfcaled) / round_name)
    prefix = f"slfcaled_{round_name}_{sc.split_tag}"
    fits_list = image_spw_sequence(
        config,
        vis=vis,
        output_dir=outdir,
        image_prefix=prefix,
        niter=sc.post_image_niter,
        robust=sc.post_image_robust if round_cfg.post_image_robust is None else round_cfg.post_image_robust,
        datacolumn="data",
        cleanup=True,
    )
    plot_frequency_panel(config, outdir, prefix, str(Path(outdir) / f"slfcaled_image_{round_name}_{sc.split_tag}.png"))
    return fits_list
