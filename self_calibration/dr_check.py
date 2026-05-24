"""Dynamic-range diagnostics for self-calibration products."""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Iterable, List

import matplotlib.pyplot as plt
import numpy as np
import sunpy.map

from utils import ensure_dir

from .utils import frequency_axis, get_selfcal_config


def compute_dr_rect(fits_file: str, x1: int = 30, x2: int = 60, y1: int = 30, y2: int = 60) -> float:
    """Compute dynamic range as peak divided by true RMS in a rectangular region."""
    try:
        m = sunpy.map.Map(fits_file)
        data = np.asarray(m.data)
        subregion = data[y1:y2, x1:x2]
        rms = np.sqrt(np.nanmean(subregion**2))
        peak = np.nanmax(data)
        return float(peak / rms) if rms > 0 else np.nan
    except Exception as exc:
        print(f"Failed to process {fits_file}: {exc}")
        return np.nan


def fits_for_stage(config, stage: str, spw_tag: str) -> str:
    """Return the expected FITS path for a self-calibration stage."""
    sc = get_selfcal_config(config)
    if stage == "precal":
        return str(Path(sc.imagedir) / "precal" / f"precal_{sc.split_tag}_spw_0_{spw_tag}.fits")
    return str(Path(sc.imagedir_slfcaled) / stage / f"slfcaled_{stage}_{sc.split_tag}_spw_0_{spw_tag}.fits")


def compute_dynamic_ranges(config, stages: Iterable[str] | None = None) -> dict[str, list[float]]:
    """Compute dynamic ranges for precal and selected self-calibration rounds."""
    sc = get_selfcal_config(config)
    stages = list(stages or ["precal"] + [round_cfg.name for round_cfg in sc.rounds])
    panel_tags, _ = frequency_axis(config)
    x1, x2, y1, y2 = sc.dr_background_region
    out: dict[str, list[float]] = {stage: [] for stage in stages}
    for tag in panel_tags:
        for stage in stages:
            fname = fits_for_stage(config, stage, tag)
            out[stage].append(compute_dr_rect(fname, x1=x1, x2=x2, y1=y1, y2=y2) if os.path.exists(fname) else np.nan)
    return out


def save_dynamic_range_csv(config, drs: dict[str, list[float]], output_csv: str) -> str:
    """Save a CSV table containing DR values and ratios over precal."""
    panel_tags, freqs = frequency_axis(config)
    stages = list(drs.keys())
    output_csv = str(output_csv)
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        header = ["SPW Tag", "Freq (GHz)"] + stages
        if "precal" in drs:
            header += [f"{stage}/precal" for stage in stages if stage != "precal"]
        writer.writerow(header)
        precal = np.array(drs.get("precal", []), dtype=float)
        for i, tag in enumerate(panel_tags):
            row = [tag, f"{freqs[i]:.6f}"] + [f"{drs[stage][i]:.6g}" for stage in stages]
            if "precal" in drs:
                for stage in stages:
                    if stage == "precal":
                        continue
                    ratio = np.array(drs[stage], dtype=float)[i] / precal[i]
                    row.append(f"{ratio:.6g}")
            writer.writerow(row)
    print(f"Dynamic-range CSV saved to: {output_csv}")
    return output_csv


def plot_dynamic_ranges(config, drs: dict[str, list[float]]) -> list[str]:
    """Plot absolute DR values and improvement factors over precal."""
    sc = get_selfcal_config(config)
    figdir = ensure_dir(sc.figdir)
    _, freqs = frequency_axis(config)
    stages = list(drs.keys())
    outputs = []

    fig, ax = plt.subplots(figsize=(14, 6), constrained_layout=True)
    for stage in stages:
        ax.plot(freqs, drs[stage], marker="o", ms=3, lw=1, label=stage)
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Dynamic Range (Peak / RMS)")
    ax.set_title("Dynamic Range Comparison")
    ax.legend()
    ax.grid(True)
    out1 = figdir / "dynamic_range_comparison_all.png"
    fig.savefig(out1, dpi=sc.panel_dpi, bbox_inches="tight")
    plt.close(fig)
    outputs.append(str(out1))

    if "precal" in drs:
        precal = np.array(drs["precal"], dtype=float)
        fig, ax = plt.subplots(figsize=(14, 5), constrained_layout=True)
        for stage in stages:
            if stage == "precal":
                continue
            ax.plot(freqs, np.array(drs[stage], dtype=float) / precal, marker="o", ms=3, lw=1, label=f"{stage}/precal")
        ax.axhline(1.0, color="gray", linestyle="--")
        ax.set_xlabel("Frequency (GHz)")
        ax.set_ylabel("DR Improvement Factor")
        ax.set_title("Dynamic Range Improvement over Precal")
        ax.legend()
        ax.grid(True)
        out2 = figdir / "dynamic_range_ratio_all.png"
        fig.savefig(out2, dpi=sc.panel_dpi, bbox_inches="tight")
        plt.close(fig)
        outputs.append(str(out2))

    for out in outputs:
        print(f"Saved: {out}")
    return outputs


def run_dynamic_range_diagnostics(config, stages: Iterable[str] | None = None) -> dict[str, list[float]]:
    """Compute and save dynamic-range diagnostics."""
    sc = get_selfcal_config(config)
    stages = list(stages or ["precal"] + [round_cfg.name for round_cfg in sc.rounds])
    drs = compute_dynamic_ranges(config, stages=stages)
    save_dynamic_range_csv(config, drs, str(Path(sc.figdir) / "dynamic_range_all.csv"))
    plot_dynamic_ranges(config, drs)
    return drs
