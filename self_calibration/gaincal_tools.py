"""Gain calibration and inspection utilities for self-calibration."""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib.pyplot as plt

from utils import ensure_dir, get_casa_task

from .utils import generate_spws, get_selfcal_config, spw_tag_from_spw


def run_gaincal_per_spw(config, round_name: str, vis: str) -> list[str]:
    """Run CASA ``gaincal`` independently for each SPW chunk."""
    sc = get_selfcal_config(config)
    round_cfg = sc.get_round(round_name)
    gaincal = get_casa_task("gaincal")
    cal_dir = ensure_dir(Path(sc.caltbdir) / round_name)
    caltables = []

    for spw in generate_spws(sc.nchan_total, sc.nchan_per_spw, sc.spw_id):
        spw_tag = spw_tag_from_spw(spw)
        caltable = cal_dir / f"slfcal_{round_name}_spw_{spw_tag}.gcal"
        print(f"Running gaincal for {round_name}, SPW {spw} -> {caltable}")
        try:
            gaincal(
                vis=str(vis),
                caltable=str(caltable),
                spw=spw,
                refant=sc.refantenna,
                gaintable=[],
                selectdata=True,
                timerange=sc.timerange,
                calmode=round_cfg.calmode,
                gaintype="G",
                solint=round_cfg.solint,
                uvrange=round_cfg.uvrange,
                minsnr=round_cfg.minsnr,
                combine="",
                parang=True,
                append=False,
            )
            caltables.append(str(caltable))
            print(f"Gaincal completed for {spw_tag}")
        except Exception as exc:
            print(f"Gaincal failed for {spw_tag}: {exc}")
    return caltables


def plot_gaincal_summary(config, round_name: str) -> str | None:
    """Create a simple diagnostic plot of the per-SPW gain tables.

    This reproduces the useful inspection block from the older selfcal.py script.
    It uses the CASA table tool from the execution namespace when available.
    """
    sc = get_selfcal_config(config)
    cal_dir = Path(sc.caltbdir) / round_name
    caltables = sorted(cal_dir.glob("*.gcal"))
    if not caltables:
        print(f"No gain tables found in {cal_dir}")
        return None

    try:
        from casatools import table
        tb = table()
    except Exception:
        import __main__
        tb = getattr(__main__, "tb", None)
        if tb is None:
            print("CASA table tool was not found; skipping gaincal summary plot.")
            return None

    ncols = sc.gain_plot_ncols
    nrows = (len(caltables) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(4 * ncols, 3 * nrows), constrained_layout=True)
    if nrows == 1:
        axes = [axes]

    for idx, caltable in enumerate(caltables):
        row, col = divmod(idx, ncols)
        ax = axes[row][col] if nrows > 1 else axes[0][col]
        try:
            tb.open(str(caltable))
            phase = tb.getcol("CPARAM")[0].real
            tb.close()
            ax.plot(phase, ".-", ms=2)
            ax.set_title(caltable.name, fontsize=8)
            ax.set_xlabel("Solution Index")
            ax.set_ylabel("Gain real part")
            ax.grid(True)
        except Exception as exc:
            ax.set_title(f"Error: {caltable.name}", fontsize=7)
            ax.text(0.5, 0.5, str(exc), ha="center", va="center", fontsize=6)
            ax.axis("off")

    for i in range(len(caltables), nrows * ncols):
        row, col = divmod(i, ncols)
        ax = axes[row][col] if nrows > 1 else axes[0][col]
        ax.axis("off")

    output = cal_dir / f"gaincal_summary_{round_name}.png"
    fig.suptitle(f"GainCal Solutions - {round_name.upper()}", fontsize=16)
    fig.savefig(output, dpi=sc.panel_dpi)
    plt.close(fig)
    print(f"Gaincal summary plot saved to {output}")
    return str(output)
