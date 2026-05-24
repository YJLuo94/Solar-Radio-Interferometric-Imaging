"""Default configuration for the MeerKAT 2024-12-29 scan-4 point-source workflow.

This file is a modular translation of ``meerkat_proc_1229_scan4_point.py``.
The numerical parameters and CASA task settings are intentionally kept close to
that legacy script.  Edit the dataclass values below or create a separate config
file for another observation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ProcessingSteps:
    """Switches controlling which pipeline steps are executed."""

    doinfo: bool = True
    do_partition: bool = True
    do_flag1: bool = True
    calc_ref: bool = False
    do_setjy: bool = True
    do_crosscal1: bool = True
    do_applycal1: bool = True
    do_flag2: bool = True
    do_split1: bool = True
    do_crosscal2: bool = True
    do_applycal2: bool = True
    do_split: bool = True
    do_qlimg: bool = True
    do_sciimg: bool = True
    # Run the solar target self-calibration workflow after cross-calibration.
    do_slfcal: bool = False



@dataclass
class SelfCalRoundConfig:
    """Configuration for one solar target self-calibration round."""

    name: str
    model_niter: int
    model_robust: float
    calmode: str
    minsnr: float = 3.0
    solint: str = "int"
    uvrange: str = ""
    mask_mode: str = "reuse_r1"
    mask_source_round: Optional[str] = None
    peak_fraction: Optional[float] = None
    apply_timerange: bool = False
    post_image_robust: Optional[float] = None


@dataclass
class SelfCalConfig:
    """Configuration for MeerKAT solar target self-calibration.

    Defaults reproduce the updated 2024-12-29 scan-4 event workflow. The older
    selfcal.py functions are retained through optional peak-fraction masks,
    gain-table diagnostics, and dynamic-range plots.
    """

    # Execution switches.
    do_split_seed_ms: bool = True
    overwrite_seed_ms: bool = False
    do_precal_imaging: bool = True
    do_selfcal_rounds: bool = True
    image_after_each_round: bool = True
    plot_gaincal: bool = False
    do_dynamic_range: bool = True
    do_apply_all_to_full_ms: bool = False
    overwrite_full_working_ms: bool = False

    # Paths.
    slfcaldir: str = "/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/"
    input_ms: str = "/data/p022/solar_meerkat/2024_dec_29/scan4/flare/20241229.flare.cal.r.ms"
    seed_ms_name: str = "20241229.flare.slfcal0.r.ms"
    seed_datacolumn: str = "data"
    full_working_ms_name: str = "20241229.flare.cal.r.ms"
    full_output_ms_name: str = "20241229.flare.cal.r.slfcaled.ms"

    # Time, frequency, and coordinate setup.
    split_tag: str = "112028"
    timerange: str = "11:20:28~11:20:30"
    phasecenter: str = "J2000 18h34m22.09 -23d12m03.0"
    refantenna: str = "m002"
    nchan_total: int = 4096
    nchan_per_spw: int = 32
    spw_id: int = 0
    freq_start_ghz: float = 0.856
    freq_step_ghz: float = 0.000208984

    # Image setup used by the self-calibration scripts.
    npix: int = 1024
    cell: str = "2.5arcsec"
    stokes: str = "I"
    clean_gain: float = 0.05
    restoringbeam: str = ""
    precal_niter: int = 10000
    precal_robust: float = -0.5
    post_image_niter: int = 10000
    post_image_robust: float = -0.5

    # Mask and diagnostics.
    full_disk_radius_arcsec: float = 1100.0
    peak_mask_fraction: float = 0.10
    dr_background_region: tuple[int, int, int, int] = (30, 60, 30, 60)
    panel_ncols: int = 16
    panel_nrows: int = 8
    panel_figsize: tuple[int, int] = (20, 12)
    panel_dpi: int = 300
    panel_cmap: str = "jet"
    gain_plot_ncols: int = 6

    ephem: dict = field(default_factory=lambda: {
        "time": [60673.46944444445, 60673.47986111111],
        "ra": [278.58900, 278.60038],
        "dec": [-23.20101, -23.20037],
        "p0": [3.1699, 3.1649],
        "delta": [0.98335911187512, 0.98335931555501],
    })

    rounds: List[SelfCalRoundConfig] = field(
        default_factory=lambda: [
            SelfCalRoundConfig(name="r1", model_niter=2000, model_robust=1.0, calmode="p", minsnr=3.0, mask_mode="full_disk"),
            SelfCalRoundConfig(name="r2", model_niter=5000, model_robust=0.5, calmode="p", minsnr=3.0, mask_mode="reuse_r1"),
            SelfCalRoundConfig(name="r3", model_niter=5000, model_robust=0.0, calmode="a", minsnr=3.0, mask_mode="reuse_r1"),
        ]
    )

    @property
    def imagedir(self) -> str:
        return str(Path(self.slfcaldir) / "images") + "/"

    @property
    def maskdir(self) -> str:
        return str(Path(self.slfcaldir) / "masks") + "/"

    @property
    def imagedir_slfcaled(self) -> str:
        return str(Path(self.slfcaldir) / "images_slfcaled") + "/"

    @property
    def caltbdir(self) -> str:
        return str(Path(self.slfcaldir) / "caltbs") + "/"

    @property
    def figdir(self) -> str:
        return str(Path(self.slfcaldir) / "figures") + "/"

    def round_ms_name(self, round_number: int) -> str:
        return f"20241229.flare.slfcalr{round_number}.r.ms"

    def get_round(self, name: str) -> SelfCalRoundConfig:
        for round_config in self.rounds:
            if round_config.name == name:
                return round_config
        raise KeyError(f"Self-calibration round not found: {name}")


@dataclass
class FullDiskImagingConfig:
    """Configuration for full-disk science imaging after self-calibration.

    This module translates the legacy ``disk_img_slfcal.py`` script. It makes
    multi-time, multi-frequency full-disk Stokes images from a self-calibrated
    target MS and optionally exports original, katbeam-corrected, and
    holography-PB-corrected FITS products.
    """

    enabled: bool = False

    # Paths.
    workdir: str = "/data/p022/solar_meerkat/2024_dec_29/scan4/full_disk_img_n/"
    msvis: str = "/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/20241229.flare.cal.r.slfcaled.ms/"
    holography_beam_file: str = "/data/p022/solar_meerkat/PB/MeerKAT_Lband_beam_StokesIV.npz"

    # Output subdirectories under ``workdir``.
    fits_root_name: str = "fits"
    tbf_root_name: str = "fitstb"
    fits_corr_holo_root_name: str = "fits_corr_holo"
    tbf_corr_holo_root_name: str = "fitstb_corr_holo"
    fits_corr_kat_root_name: str = "fits_corr_katbeam"
    tbf_corr_kat_root_name: str = "fitstb_corr_katbeam"

    # Solar and pointing coordinates.
    pointing_coord: str = "18h31m53.22s -20d34m14.7s"
    solar_coord: str = "18h34m22.09s -23d12m03.0s"
    phasecenter: str = "J2000 18h34m22.09 -23d12m03.0"
    ephem: dict = field(default_factory=lambda: {
        "time": [60673.46944444445, 60673.47986111111],
        "ra": [278.58900, 278.60038],
        "dec": [-23.20101, -23.20037],
        "p0": [3.1699, 3.1649],
        "delta": [0.98335911187512, 0.98335931555501],
    })

    # Frequency setup. The default is 16 channels per imaging chunk, matching
    # the final science-imaging script.
    spw_id: int = 0
    nchan_total: int = 4096
    nchan_per_spw: int = 16

    # tclean setup.
    imsize: List[int] = field(default_factory=lambda: [2048, 2048])
    cell: str = "1.5arcsec"
    specmode: str = "mfs"
    pblimit: float = 0.1
    restoringbeam: list = field(default_factory=list)
    niter: int = 50000
    gain: float = 0.05
    interactive: bool = False
    weighting: str = "briggs"
    robust: float = -0.5
    gridder: str = "standard"
    datacolumn: str = "data"
    stokes_list: List[str] = field(default_factory=lambda: ["I", "V"])

    # PB correction setup.
    do_holography_pbcor: bool = True
    do_katbeam_pbcor: bool = True
    export_original: bool = True
    export_tb: bool = True
    pbband: str = "LBand"
    pb_minval: float = 1e-6
    nan_to_one: bool = False

    # Timerange generation. The default reproduces the legacy test slice
    # ``trangelist[40:41]`` in disk_img_slfcal.py.
    timerange_start: str = "2024-12-29 11:19:40"
    timerange_duration_sec: float = 2.0
    timerange_step_sec: float = 2.0
    n_timeranges: int = 50
    time_indices: List[int] = field(default_factory=lambda: [40])

    @property
    def fits_root(self) -> str:
        return str(Path(self.workdir) / self.fits_root_name)

    @property
    def tbf_root(self) -> str:
        return str(Path(self.workdir) / self.tbf_root_name)

    @property
    def fits_corr_holo_root(self) -> str:
        return str(Path(self.workdir) / self.fits_corr_holo_root_name)

    @property
    def tbf_corr_holo_root(self) -> str:
        return str(Path(self.workdir) / self.tbf_corr_holo_root_name)

    @property
    def fits_corr_kat_root(self) -> str:
        return str(Path(self.workdir) / self.fits_corr_kat_root_name)

    @property
    def tbf_corr_kat_root(self) -> str:
        return str(Path(self.workdir) / self.tbf_corr_kat_root_name)

@dataclass
class MeerKATConfig:
    """Configuration values translated from the original scan-4 CASA script."""

    steps: ProcessingSteps = field(default_factory=ProcessingSteps)
    selfcal: SelfCalConfig = field(default_factory=SelfCalConfig)
    full_disk_imaging: FullDiskImagingConfig = field(default_factory=FullDiskImagingConfig)

    # Extra Python paths used by the legacy local CASA environment.
    extra_python_paths: List[str] = field(
        default_factory=lambda: [
            "/data/p022/Software/site-packages/",
            "/data/p022/Software/",
            "/data/p022/Software/processMeerKAT/",
            "/data/p022/Software/processMeerKAT/aux_scripts/",
            "/data/p022/Software/processMeerKAT/crosscal_scripts/",
            "/data/p022/Software/processMeerKAT/selfcal_scripts/",
        ]
    )

    # General information.
    ncpus: int = 4
    solar_burst: bool = False
    orims: str = "/data/p022/dec2024_meerkat/1735466915_sdp_l0.ms/"
    outputcalvis: str = "20241229.scan4.cal.ms"
    workfolder: str = "/data/p022/solar_meerkat/2024_dec_29/scan4/pipe_new/"
    dopol: bool = False
    doparallel: bool = True
    domms: bool = True

    # Partition and split options.
    channelbin: int = 1
    specavg: int = 1
    timeavg: str = "0s"
    spw_s: str = ""
    timeran: str = ""
    scans: str = "10,11,12,13"
    badants: List[int] = field(default_factory=list)
    badfreqranges: List[str] = field(
        default_factory=lambda: ["935~947MHz", "1160~1310MHz", "1476~1611MHz", "1670~1700MHz"]
    )
    refantant: str = "m002"

    # Field selection.
    bpfield: str = "J1939-6342"
    phasefield: str = "J1830-3602"
    tarfield: str = "Pointing_4"

    # Cross-calibration control.
    minbaselines: int = 4
    calprefix: str = "cal/callib"

    # Quick-look image parameters.
    timerange1: str = "11:17:00 ~ 11:30:30"
    spw1: str = "*:0.88~0.92 GHz"

    # Science image parameters.
    timerange2: str = "11:17:00 ~ 11:30:30"
    spw2: str = "*:0.88~0.92 GHz"
    dopb_cor: bool = True
    pbband: str = "LBand"
    deconvolver: str = "multiscale"
    multiscale: List[int] = field(default_factory=lambda: [0, 5, 10, 15])
    nterms: int = 2
    gridder: str = "wproject"
    wprojplanes: int = 512
    niter: int = 50000
    cell: str = "1.5arcsec"
    robust: float = -0.5
    imsize: List[int] = field(default_factory=lambda: [6144, 6144])
    threshold: str = "0.01 mJy"
    stokes: str = "I"
    restoringbeam: str = ""
    pbthreshold: float = 0.1

    @property
    def visname(self) -> str:
        return Path(self.orims).name

    @property
    def msvis0(self) -> str:
        return self.visname.replace(".ms", ".cal0.ms")

    @property
    def msvisr1(self) -> str:
        return self.visname.replace(".ms", ".calr1.ms")

    @property
    def gainfields(self) -> str:
        return f"{self.bpfield},{self.phasefield}"

    @property
    def calfields(self) -> str:
        return f"{self.bpfield},{self.phasefield}"

    @property
    def logfile(self) -> str:
        return "Log.txt"

    def round_calprefix(self, round_label: str) -> str:
        """Return the calibration table prefix for a cross-calibration round.

        This preserves the original naming convention, e.g. ``cal/callibr1`` and
        ``cal/callibr2`` for round labels ``r1`` and ``r2``.
        """
        return f"{self.calprefix}{round_label}"


def get_default_config() -> MeerKATConfig:
    """Return the default scan-4 MeerKAT configuration."""
    return MeerKATConfig()
