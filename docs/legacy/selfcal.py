######################This is the script for self-calibration
import sys
sys.path.append("/data/p022/Software/site-packages/") 
sys.path.append("/data/p022/Software/")

from suncasa.utils import helioimage2fits as hf
msvis = "/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/20241229.falre.r.slfcal0.ms/"
msinfo = hf.read_msinfo(msvis)
ephem2={'time':[60673.46944444445,60673.47986111111],'ra':[278.58900,278.60038],\
    'dec':[-23.20101,-23.20037],'p0':[3.1699,3.1649],'delta':[0.98335911187512,0.98335931555501]}

####switchs
dofullsun=0 # initial full-sun imaging
domasks=0 # get masks
doslfcal=0 # main cycle of doing selfcalibration
doapply=1 # apply the results
doclean_slfcaled=1 # perform clean for self-calibrated data


###Working diectionary
slfcaldir = "/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/"#place to put all selfcalibration products
imagedir = slfcaldir+'images/' #place to put all selfcalibration images
maskdir = slfcaldir+'masks/' #place to put clean masks
imagedir_slfcaled = slfcaldir+'images_slfcaled/' #place to put final self-calibrated images
caltbdir = slfcaldir+'caltbs/' # place to put calibration tables
# make these directories if they do not already exist
dirs = [slfcaldir, imagedir, maskdir, imagedir_slfcaled, caltbdir]
for d in dirs:
    if not os.path.exists(d):
        os.makedirs(d)

# ============ Prior definitions for spectral windows, antennas, pixel scale =========

# Split SPW 0 into 128 spectral windows, each with 32 channels
spws = [f'0:{i}~{i+31}' for i in range(0, 4096, 32)]
split_tag = '112028'

# Use all antennas by default (can set to e.g. 'm001&m002' if needed)
antennas = ''

# Image parameters
npix = 1024                     # Number of pixels per side
cell = '2.5arcsec'              # Pixel scale; covers full Sun (~2500 arcsec)

# Number of self-calibration rounds
nround = 3                      # e.g., [phase, phase, amplitude+phase]

# Phase center (for off-pointed solar observations)
phasecenter = 'J2000 18h34m22.09 -23d12m03.0'

# === Measurement Sets ===
slfcalms = slfcaldir + '20241229.falre.r.slfcal0.ms'        # Input MS for self-calibration
slfcaledms = slfcaldir + '20241229.falre.r.slfcaled.ms'     # Output MS (after final applycal)


if dofullsun:
    print(">>> Starting initial imaging (no model) for comparison...")

    import os
    import matplotlib.pyplot as plt
    import sunpy.map
    import numpy as np
    import glob
    from casatools import image as ia_tool
    from suncasa.utils import helioimage2fits as hf

    # === Paths and directories ===
    msvis = slfcalms  # slfcalms is already defined earlier
    msinfo = hf.read_msinfo(msvis)
    ephem2 = {'time':[60673.46944444445,60673.47986111111],
              'ra':[278.58900,278.60038],
              'dec':[-23.20101,-23.20037],
              'p0':[3.1699,3.1649],
              'delta':[0.98335911187512,0.98335931555501]}

    imagedir_precal = imagedir + 'precal/'
    if not os.path.exists(imagedir_precal):
        os.makedirs(imagedir_precal)

    timerange = '11:20:28~11:20:30'
    ia = ia_tool()
    fits_list = []

    # === Imaging each SPW block ===
    for spw in spws:
        ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
        spw_tag = f'spw_0_{ch_start:04d}-{ch_end:04d}'
        imagename = imagedir_precal + f'precal_{split_tag}_{spw_tag}'
        imagefile = imagename + '.image'
        im_fits = imagename + '.fits'

        print(f">>> Imaging {spw}")
        tclean(vis=slfcalms,
               imagename=imagename,
               spw=spw,
               timerange=timerange,
               imsize=[npix, npix],
               cell=cell,
               weighting='briggs',
               robust=-0.5,
               niter=10000,
               interactive=False,
               specmode='mfs',
               stokes='I',
               gain=0.05)

        if not os.path.exists(imagefile):
            print(f"⚠️ Skipping {spw_tag}: .image not created.")
            continue

        print(f">>> Registering image {imagefile} to {im_fits}")
        hf.imreg(vis=slfcalms,
                 msinfo=msinfo,
                 imagefile=imagefile,
                 fitsfile=im_fits,
                 ephem=ephem2,
                 timerange=timerange,
                 usephacenter=False,
                 verbose=True)

        # Remove intermediate CASA files
        clnjunks = ['.flux', '.mask', '.model', '.residual', '.sumwt', '.pb']
        for ext in clnjunks:
            f = imagename + ext
            if os.path.exists(f):
                os.system('rm -rf ' + f)

        if os.path.exists(im_fits):
            fits_list.append(im_fits)

    # === Plotting parameters ===
    ncols, nrows = 16, 8
    figsize = (20, 12)
    f_start = 0.856  # GHz
    f_step = 0.000208984  # GHz

    # === Panel label generation ===
    panel_tags = []
    mid_channels = []
    mid_freqs = []
    for i in range(ncols * nrows):
        ch_start = i * 32
        ch_end = min(ch_start + 31, 4095)
        tag = f"{ch_start:04d}-{ch_end:04d}"
        mid_ch = (ch_start + ch_end) // 2
        mid_freq = f_start + mid_ch * f_step
        panel_tags.append(tag)
        mid_channels.append(mid_ch)
        mid_freqs.append(mid_freq)

    # === Map FITS files to tags ===
    fits_dict = {}
    fits_files = glob.glob(os.path.join(imagedir_precal, f'precal_{split_tag}_spw_0_*.fits'))
    for f in fits_files:
        basename = os.path.basename(f)
        parts = basename.split('_spw_0_')
        if len(parts) == 2:
            spw_tag = parts[-1].replace('.fits', '')
            fits_dict[spw_tag] = f

    # === Plotting grid ===
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize,
                             gridspec_kw={'wspace': 0.0, 'hspace': 0.0})

    for idx, (spw_tag, freq) in enumerate(zip(panel_tags, mid_freqs)):
        row, col = divmod(idx, ncols)
        ax = axes[row][col]
        ax.set_xticks([])
        ax.set_yticks([])

        fname = fits_dict.get(spw_tag)
        plotted = False

        if fname and os.path.exists(fname):
            try:
                m = sunpy.map.Map(fname)
                data = m.data
                ax.imshow(data, cmap='jet', origin='lower', aspect='equal')
                plotted = True
            except Exception as e:
                print(f"⚠️ Failed to plot {spw_tag}: {e}")

        if plotted:
            ax.text(0.05, 0.92, f"{freq:.3f} GHz", transform=ax.transAxes,
                    fontsize=6, color='white', ha='left', va='top',
                    bbox=dict(facecolor='black', alpha=0.3, lw=0))
        else:
            ax.imshow(np.ones((10, 10)), cmap='gray', vmin=0, vmax=1, origin='lower', aspect='equal')
            ax.text(0.05, 0.92, f"{freq:.3f} GHz", transform=ax.transAxes,
                    fontsize=6, color='gray', ha='left', va='top')

    # === Save figure ===
    output_file = os.path.join(imagedir_precal, f"precal_image_{split_tag}.png")
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f"✅ Final image grid saved to: {output_file}")



# =========== Step 2 (optional), generate masks =========
# for the first round, use the full-disk as the mask
if domasks:
    import os
    import glob
    import re
    from casatools import image

    # === Parse cell string robustly (e.g. '2.5 arcsec' or '2.5arcsec')
    def parse_cell_arcsec(cell_str):
        try:
            return float(re.findall(r'[\d.]+', cell_str)[0])
        except:
            raise ValueError(f"❌ Failed to parse cell size from '{cell_str}'")

    # === Parameters ===
    cell_arcsec = parse_cell_arcsec(cell)  # e.g., '2.5 arcsec'
    radius_arcsec = 1100.0
    radius_pix = int(radius_arcsec / cell_arcsec)

    imagedir_precal = imagedir + 'precal/'
    mask_round_dir = os.path.join(maskdir, 'round1')
    if not os.path.exists(mask_round_dir):
        os.makedirs(mask_round_dir)

    ia = image()
    image_files = sorted(glob.glob(os.path.join(imagedir_precal, f'precal_{split_tag}_spw_0_*.image')))

    for imfile in image_files:
        try:
            # Open the image
            ia.open(imfile)
            shape = ia.shape()
            nx, ny = shape[0], shape[1]
            cx, cy = nx // 2, ny // 2
            csys = ia.coordsys().torecord()
            ia.done()

            # Prepare output path
            maskname = os.path.basename(imfile).replace('.image', '.mask')
            maskpath = os.path.join(mask_round_dir, maskname)
            if os.path.exists(maskpath):
                os.system(f'rm -rf {maskpath}')

            # Create new mask from shape and csys
            ia.fromshape(maskpath, shape, csys)
            mask = ia.getchunk()
            mask[:] = 0

            for x in range(nx):
                for y in range(ny):
                    if (x - cx)**2 + (y - cy)**2 <= radius_pix**2:
                        mask[x, y, 0, 0] = 1

            ia.putchunk(mask)
            ia.done()
            print(f"✅ Created full-disk mask: {maskpath}")

        except Exception as e:
            print(f"⚠️ Failed to create mask for {imfile}: {e}")
            ia.done()


###if doslfcal:

# =========== Step 3 first round of self-calibration =========

import os
from suncasa.utils import helioimage2fits as hf

# === Round 1 self-calibration parameters ===
calprefix = caltbdir + 'slf' + 'r1'
imgprefix = imagedir + 'r1/'
refantenna = 'm002'
niter = 500
robust = 0.5
calmode = 'p'
uvrange = ''
slfcalms = slfcaldir + '20241229.falre.r.slfcal0.ms'

# === Prepare output directory ===
if not os.path.exists(imgprefix):
    os.makedirs(imgprefix)

# === Clear existing calibration and models ===
clearcal(slfcalms)
delmod(slfcalms)

# === Image generation loop ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    imagename = f'{imgprefix}img_r1_spw_{spw_tag}'
    maskname = os.path.join(maskdir, 'round1', f'precal_{split_tag}_spw_0_{spw_tag}.mask')
    im_fits = imagename + '.fits'

    print(f"🧽 Cleaning model for SPW {spw} → {imagename}")

    tclean(vis=slfcalms,
           imagename=imagename,
           spw=spw,
           timerange='11:20:28~11:20:30',
           imsize=[npix, npix],
           cell=cell,
           weighting='briggs',
           robust=robust,
           niter=niter,
           interactive=False,
           usemask='user',
           mask=maskname,
           savemodel='modelcolumn',
           specmode='mfs',
           stokes='I',
           gain=0.05,
           uvrange=uvrange,
           restoringbeam='')

    print(f"✅ Model image created: {imagename}.image")

    try:
        hf.imreg(vis=slfcalms,
                 msinfo=msinfo,
                 imagefile=imagename + '.image',
                 fitsfile=im_fits,
                 ephem=ephem2,
                 timerange='11:20:28~11:20:30',
                 usephacenter=False,
                 verbose=True)
        print(f"🗂️ Registered FITS saved: {im_fits}")
    except Exception as e:
        print(f"⚠️ Registration failed for {imagename}.image: {e}")

    # Cleanup intermediate CASA files (keep only .image and .fits)
    clnjunks = ['.flux', '.mask', '.model', '.psf', '.residual', '.sumwt', '.pb']
    for ext in clnjunks:
        f = imagename + ext
        if os.path.exists(f):
            os.system(f'rm -rf {f}')

####Generate the self-calibration table 1
# === Define Round 1 calibration folder ===
calround = 'r1'
caltb_round_dir = os.path.join(caltbdir, calround)
if not os.path.exists(caltb_round_dir):
    os.makedirs(caltb_round_dir)

# === Loop over SPWs and run gaincal per SPW ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    caltable = os.path.join(caltb_round_dir, f'slfcal_r1_spw_{spw_tag}.gcal')

    print(f"📡 Running gaincal for SPW {spw} → {caltable}")

    try:
        gaincal(vis=slfcalms,
                caltable=caltable,
                spw=spw,
                refant=refantenna,
                gaintable=[],
                selectdata=True,
                timerange='11:20:28~11:20:30',
                calmode=calmode,
                gaintype='G',
                solint='int',
                uvrange=uvrange,
                minsnr=2.0,
                combine='',
                parang=True,
                append=False)
        print(f"✅ Gaincal completed for SPW {spw_tag}")
    except Exception as e:
        print(f"⚠️ Gaincal failed for SPW {spw_tag}: {e}")

####check calibration tables:

import matplotlib.pyplot as plt
import os

from casaplotms import plotms  # optional: depends on your CASA version

# Round 1 calibration table folder
caltb_round_dir = os.path.join(caltbdir, 'r1')
plot_outfile = os.path.join(caltb_round_dir, 'gaincal_summary_r1.png')

# Get all caltables in that folder
caltables = sorted([os.path.join(caltb_round_dir, f)
                    for f in os.listdir(caltb_round_dir)
                    if f.endswith('.gcal')])

# Plot settings
ncols = 6
nrows = (len(caltables) + ncols - 1) // ncols
figsize = (4 * ncols, 3 * nrows)

fig, axes = plt.subplots(nrows, ncols, figsize=figsize, constrained_layout=True)

for idx, caltable in enumerate(caltables):
    row, col = divmod(idx, ncols)
    ax = axes[row][col] if nrows > 1 else axes[col]

    try:
        # Extract gain table for plotting
        tb.open(caltable)
        ant = tb.getcol('ANTENNA1')
        phase = tb.getcol('CPARAM')[0].real  # or use imag, or abs
        tb.close()

        ax.plot(phase, '.-')
        ax.set_title(os.path.basename(caltable), fontsize=8)
        ax.set_xlabel("Solution Index")
        ax.set_ylabel("Gain Phase")
        ax.grid(True)
    except Exception as e:
        ax.set_title(f"Error: {os.path.basename(caltable)}", fontsize=7)
        ax.text(0.5, 0.5, str(e), ha='center', va='center', fontsize=6)
        ax.axis('off')

# Turn off empty subplots
for i in range(len(caltables), nrows * ncols):
    row, col = divmod(i, ncols)
    ax = axes[row][col] if nrows > 1 else axes[col]
    ax.axis('off')

fig.suptitle("GainCal Phase Solutions - Round 1", fontsize=16)
plt.savefig(plot_outfile, dpi=300)
plt.close()
print(f"✅ Summary plot saved to {plot_outfile}")

##### Applycal

print(">>> Starting safe applycal for Round 1 (per SPW)")

# Step 0: Clear previous calibration and model
clearcal(slfcalms)
delmod(slfcalms)
print("🧹 Cleared previous calibration (clearcal) and model (delmod) from MS.")

# Step 1: Apply calibration one SPW at a time
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    caltable = os.path.join(caltbdir, 'r1', f'slfcal_r1_spw_{spw_tag}.gcal')

    print(f"📡 Applying calibration for SPW {spw} using {caltable}")

    if not os.path.exists(caltable):
        print(f"⚠️ Calibration table {caltable} not found. Skipping.")
        continue

    try:
        applycal(vis=slfcalms,
                 spw=spw,
                 gaintable=[caltable],
                 interp='linear',
                 calwt=False,
                 applymode='calonly',
                 flagbackup=False,
                 timerange='11:20:28~11:20:30')
        print(f"✅ Calibration applied for SPW {spw}")
    except Exception as e:
        print(f"❌ Applycal failed for SPW {spw_tag}: {e}")

####Split the data set
print(">>> Splitting calibrated data into new MS for Round 1")

slfcaledms = slfcaldir + '20241229.falre.r.slfcalr1.ms'
split(vis=slfcalms, outputvis=slfcaledms, datacolumn='corrected')

print(f"✅ Calibrated MS saved to: {slfcaledms}")

####Make images after self-calibration round 1
print(">>> Starting imaging of self-calibrated MS (Round 1)")

import os
import matplotlib.pyplot as plt
import sunpy.map
import numpy as np
import glob
from suncasa.utils import helioimage2fits as hf

# === Paths and setup ===
imagedir_r1 = imagedir_slfcaled + 'r1/'
if not os.path.exists(imagedir_r1):
    os.makedirs(imagedir_r1)

split_tag = '112028'
timerange = '11:20:28~11:20:30'
slfcaledms = slfcaldir + '20241229.falre.r.slfcalr1.ms'
msinfo_r1 = hf.read_msinfo(slfcaledms)

fits_list = []

# === Imaging ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'spw_0_{ch_start:04d}-{ch_end:04d}'
    imagename = imagedir_r1 + f'slfcaled_r1_{split_tag}_{spw_tag}'
    imagefile = imagename + '.image'
    im_fits = imagename + '.fits'

    print(f">>> Imaging {spw}")
    tclean(vis=slfcaledms,
           imagename=imagename,
           spw=spw,
           timerange=timerange,
           imsize=[npix, npix],
           cell=cell,
           weighting='briggs',
           robust=-0.5,
           niter=10000,
           interactive=False,
           specmode='mfs',
           stokes='I',
           gain=0.05)

    if not os.path.exists(imagefile):
        print(f"⚠️ Skipping {spw_tag}: .image not created.")
        continue

    print(f">>> Registering image {imagefile} to {im_fits}")
    hf.imreg(vis=slfcaledms,
             msinfo=msinfo_r1,
             imagefile=imagefile,
             fitsfile=im_fits,
             ephem=ephem2,
             timerange=timerange,
             usephacenter=False,
             verbose=True)

    clnjunks = ['.flux', '.mask', '.model', '.residual', '.sumwt', '.pb', '.psf']
    for ext in clnjunks:
        f = imagename + ext
        if os.path.exists(f):
            os.system('rm -rf ' + f)

    if os.path.exists(im_fits):
        fits_list.append(im_fits)

# === Plotting ===
print(">>> Plotting image grid for self-calibrated MS (Round 1)")

ncols, nrows = 16, 8
figsize = (20, 12)
f_start = 0.856  # GHz
f_step = 0.000208984  # GHz

panel_tags = []
mid_channels = []
mid_freqs = []

for i in range(ncols * nrows):
    ch_start = i * 32
    ch_end = min(ch_start + 31, 4095)
    tag = f"{ch_start:04d}-{ch_end:04d}"
    mid_ch = (ch_start + ch_end) // 2
    mid_freq = f_start + mid_ch * f_step
    panel_tags.append(tag)
    mid_channels.append(mid_ch)
    mid_freqs.append(mid_freq)

fits_dict = {}
fits_files = glob.glob(os.path.join(imagedir_r1, f'slfcaled_r1_{split_tag}_spw_0_*.fits'))
print(f"✅ Found {len(fits_files)} FITS files")

for f in fits_files:
    basename = os.path.basename(f)
    try:
        parts = basename.split('_spw_0_')
        if len(parts) != 2:
            print(f"⚠️ Unrecognized filename: {basename}")
            continue
        spw_tag = parts[-1].replace('.fits', '')
        fits_dict[spw_tag] = f
    except Exception as e:
        print(f"⚠️ Failed to parse: {basename} – {e}")

fig, axes = plt.subplots(nrows, ncols, figsize=figsize,
                         gridspec_kw={'wspace': 0.0, 'hspace': 0.0})

for idx, (spw_tag, freq) in enumerate(zip(panel_tags, mid_freqs)):
    row, col = divmod(idx, ncols)
    ax = axes[row][col]
    ax.set_xticks([])
    ax.set_yticks([])

    fname = fits_dict.get(spw_tag)
    plotted = False

    if fname and os.path.exists(fname):
        try:
            m = sunpy.map.Map(fname)
            data = m.data
            ax.imshow(data, cmap='jet', origin='lower', aspect='equal')
            plotted = True
        except Exception as e:
            print(f"⚠️ Failed to load or plot {spw_tag}: {e}")

    if plotted:
        ax.text(0.05, 0.92, f"{freq:.3f} GHz", transform=ax.transAxes,
                fontsize=6, color='white', ha='left', va='top',
                bbox=dict(facecolor='black', alpha=0.3, lw=0))
    else:
        ax.imshow(np.ones((10, 10)), cmap='gray', vmin=0, vmax=1, origin='lower', aspect='equal')
        ax.text(0.05, 0.92, f"{freq:.3f} GHz", transform=ax.transAxes,
                fontsize=6, color='gray', ha='left', va='top')

output_file = os.path.join(imagedir_r1, f"slfcaled_image_r1_{split_tag}.png")
plt.savefig(output_file, dpi=300)
plt.close()

print(f"✅ Final frequency-labeled Round 1 image grid saved to: {output_file}")

#######Compare DR
import os
import numpy as np
import matplotlib.pyplot as plt
import sunpy.map

# === Input directories ===
precal_dir = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/images/precal/'
r1_dir = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/images_slfcaled/r1/'
split_tag = '112028'
figdir = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/figures/'

# === Create figure output directory ===
if not os.path.exists(figdir):
    os.makedirs(figdir)

# === Frequency info ===
f_start = 0.856  # GHz
f_step = 0.000208984  # GHz
n_spws = 4096 // 32  # 128 SPWs

panel_tags = []
mid_freqs = []
for i in range(n_spws):
    ch_start = i * 32
    ch_end = ch_start + 31
    tag = f"{ch_start:04d}-{ch_end:04d}"
    mid_ch = (ch_start + ch_end) // 2
    mid_freq = f_start + mid_ch * f_step
    panel_tags.append(tag)
    mid_freqs.append(mid_freq)

# === DR calculation with rectangular background region ===
def compute_dr_rect(fits_file, x1=30, x2=60, y1=30, y2=60):
    try:
        m = sunpy.map.Map(fits_file)
        data = m.data
        subregion = data[y1:y2, x1:x2]
        rms = np.sqrt(np.nanmean(subregion**2))
        peak = np.nanmax(data)
        return peak / rms if rms > 0 else np.nan
    except Exception as e:
        print(f"⚠️ Failed to process {fits_file}: {e}")
        return np.nan

# === Compute DRs for each SPW ===
dr_precal = []
dr_r1 = []

for tag in panel_tags:
    f_precal = os.path.join(precal_dir, f'precal_{split_tag}_spw_0_{tag}.fits')
    f_r1 = os.path.join(r1_dir, f'slfcaled_r1_{split_tag}_spw_0_{tag}.fits')

    dr0 = compute_dr_rect(f_precal) if os.path.exists(f_precal) else np.nan
    dr1 = compute_dr_rect(f_r1) if os.path.exists(f_r1) else np.nan

    dr_precal.append(dr0)
    dr_r1.append(dr1)

# === Plot 1: DR comparison ===
fig, ax = plt.subplots(figsize=(14, 6), constrained_layout=True)
ax.plot(mid_freqs, dr_precal, 'o-', label='Precal')
ax.plot(mid_freqs, dr_r1, 's-', label='Selfcal R1')
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("Dynamic Range (Peak / RMS)")
ax.set_title("Dynamic Range Comparison: Precal vs Selfcal Round 1")
ax.legend()
ax.grid(True)
outfile1 = os.path.join(figdir, 'dynamic_range_comparison_r1.png')
fig.savefig(outfile1, dpi=300, bbox_inches='tight')
plt.close(fig)
print(f"✅ Saved: {outfile1}")

# === Plot 2: DR improvement factor ===
dr_ratio = np.array(dr_r1) / np.array(dr_precal)
fig, ax = plt.subplots(figsize=(14, 4), constrained_layout=True)
ax.plot(mid_freqs, dr_ratio, 'd-', color='green')
ax.axhline(1.0, color='gray', linestyle='--')
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("DR Ratio (R1 / Precal)")
ax.set_title("DR Improvement Factor (R1 / Precal)")
ax.grid(True)
outfile2 = os.path.join(figdir, 'dynamic_range_ratio_r1.png')
fig.savefig(outfile2, dpi=300, bbox_inches='tight')
plt.close(fig)
print(f"✅ Saved: {outfile2}")


#############Round 2
# ===========generate masks =========
# for the second round, use the 10% contour
import os
import glob
from casatools import image

# === Paths ===
imagedir_r1 = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/images_slfcaled/r1/'
maskdir_r2 = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/masks/round2/'
split_tag = '112028'

# === Create output folder if not exist ===
if not os.path.exists(maskdir_r2):
    os.makedirs(maskdir_r2)

# === Get all Round 1 .image files ===
image_files = sorted(glob.glob(os.path.join(imagedir_r1, f'slfcaled_r1_{split_tag}_spw_0_*.image')))

ia = image()

for imfile in image_files:
    try:
        # Open image
        ia.open(imfile)
        shape = ia.shape()
        csys = ia.coordsys().torecord()
        data = ia.getchunk()
        peak = data.max()
        threshold = 0.1 * peak
        mask_data = (data >= threshold).astype(int)
        ia.done()

        # Prepare output path
        basename = os.path.basename(imfile).replace('.image', '.mask')
        maskpath = os.path.join(maskdir_r2, basename)
        if os.path.exists(maskpath):
            os.system(f'rm -rf {maskpath}')

        # Create new .mask file
        ia.fromshape(maskpath, shape, csys)
        ia.putchunk(mask_data)
        ia.done()

        print(f"✅ Created mask: {maskpath} (threshold = {threshold:.3g})")

    except Exception as e:
        print(f"⚠️ Failed to create mask for {imfile}: {e}")
        ia.done()

# =========== setup model =========

import os
from casatools import image
from suncasa.utils import helioimage2fits as hf

# === Input MS for Round 2 ===
slfcalms_r1 = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/20241229.falre.r.slfcalr1.ms'

# === Imaging output ===
imgprefix_r2 = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/images/r2/'
if not os.path.exists(imgprefix_r2):
    os.makedirs(imgprefix_r2)

# === Mask path ===
maskdir_r2 = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/masks/round2/'

# === Parameters ===
refantenna = 'm002'
niter = 5000
robust = 0
uvrange = ''
cell = '2.5arcsec'
npix = 1024
split_tag = '112028'
timerange = '11:20:28~11:20:30'

# === Spectral windows ===
spws = [f'0:{i}~{i+31}' for i in range(0, 4096, 32)]

# === Read msinfo and ephemeris (optional, for image registration) ===
msinfo_r1 = hf.read_msinfo(slfcalms_r1)
ephem2 = {
    'time':[60673.46944444445,60673.47986111111],
    'ra':[278.58900,278.60038],
    'dec':[-23.20101,-23.20037],
    'p0':[3.1699,3.1649],
    'delta':[0.98335911187512,0.98335931555501]
}

# === Imaging loop ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    imagename = f'{imgprefix_r2}img_r2_spw_{spw_tag}'
    maskname = os.path.join(maskdir_r2, f'slfcaled_r1_{split_tag}_spw_0_{spw_tag}.mask')
    im_fits = imagename + '.fits'

    print(f"🧽 Cleaning model for SPW {spw} → {imagename}")

    tclean(vis=slfcalms_r1,
           imagename=imagename,
           spw=spw,
           timerange=timerange,
           imsize=[npix, npix],
           cell=cell,
           weighting='briggs',
           robust=robust,
           niter=niter,
           interactive=False,
           usemask='user',
           mask=maskname,
           savemodel='modelcolumn',
           specmode='mfs',
           stokes='I',
           gain=0.05,
           uvrange=uvrange,
           restoringbeam='')

    print(f"✅ Model image created: {imagename}.image")

    try:
        hf.imreg(vis=slfcalms_r1,
                 msinfo=msinfo_r1,
                 imagefile=imagename + '.image',
                 fitsfile=im_fits,
                 ephem=ephem2,
                 timerange=timerange,
                 usephacenter=False,
                 verbose=True)
        print(f"🗂️ Registered FITS saved: {im_fits}")
    except Exception as e:
        print(f"⚠️ Registration failed for {imagename}.image: {e}")

    # Cleanup intermediate files except .image and .fits
    clnjunks = ['.flux', '.mask', '.model', '.psf', '.residual', '.sumwt', '.pb']
    for ext in clnjunks:
        f = imagename + ext
        if os.path.exists(f):
            os.system(f'rm -rf {f}')

# === Gaincal to generate the calibration table ===
import os

# === MS for Round 2 calibration ===
slfcalms_r1 = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/20241229.falre.r.slfcalr1.ms'

# === Calibration output directory ===
caltbdir = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/caltbs/'
caltb_round_dir = os.path.join(caltbdir, 'r2')
if not os.path.exists(caltb_round_dir):
    os.makedirs(caltb_round_dir)

# === Calibration parameters ===
refantenna = 'm002'
calmode = 'p'
uvrange = ''
timerange = '11:20:28~11:20:30'
spws = [f'0:{i}~{i+31}' for i in range(0, 4096, 32)]

# === Gaincal loop ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    caltable = os.path.join(caltb_round_dir, f'slfcal_r2_spw_{spw_tag}.gcal')

    print(f"📡 Running gaincal for SPW {spw} → {caltable}")

    try:
        gaincal(vis=slfcalms_r1,
                caltable=caltable,
                spw=spw,
                refant=refantenna,
                gaintable=[],
                selectdata=True,
                timerange=timerange,
                calmode=calmode,
                gaintype='G',
                solint='int',
                uvrange=uvrange,
                minsnr=2.0,
                combine='',
                parang=True,
                append=False)
        print(f"✅ Gaincal completed for SPW {spw_tag}")
    except Exception as e:
        print(f"⚠️ Gaincal failed for SPW {spw_tag}: {e}")

###################applycal

import os

# === Input MS ===
slfcalms_r1 = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/20241229.falre.r.slfcalr1.ms'

# === Output MS ===
slfcalms_r2 = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/20241229.falre.r.slfcalr2.ms'

# === Calibration table directory ===
caltbdir_r2 = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/caltbs/r2/'

# === Clear existing calibration and model first ===
clearcal(slfcalms_r1)
delmod(slfcalms_r1)
print("🧹 Cleared previous calibration and model from MS.")

# === SPW definition ===
spws = [f'0:{i}~{i+31}' for i in range(0, 4096, 32)]

# === Applycal per SPW ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    caltable = os.path.join(caltbdir_r2, f'slfcal_r2_spw_{spw_tag}.gcal')

    print(f"📡 Applying calibration for SPW {spw} using {caltable}")

    if not os.path.exists(caltable):
        print(f"⚠️ Calibration table {caltable} not found. Skipping.")
        continue

    try:
        applycal(vis=slfcalms_r1,
                 spw=spw,
                 gaintable=[caltable],
                 interp='linear',
                 calwt=False,
                 applymode='calonly',
                 flagbackup=False,
                 timerange='11:20:28~11:20:30')
        print(f"✅ Calibration applied for SPW {spw}")
    except Exception as e:
        print(f"❌ Applycal failed for SPW {spw_tag}: {e}")

# === Split out calibrated MS for Round 2 ===
print(">>> Splitting calibrated data into new MS for Round 2")
split(vis=slfcalms_r1, outputvis=slfcalms_r2, datacolumn='corrected')
print(f"✅ Calibrated MS saved to: {slfcalms_r2}")

###################Imaging###########
import os
import numpy as np
import matplotlib.pyplot as plt
import sunpy.map
import glob
from casatools import image as ia_tool
from suncasa.utils import helioimage2fits as hf

# === Paths and parameters ===
slfcaledms_r2 = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/20241229.falre.r.slfcalr2.ms'
imagedir_r2 = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/images_slfcaled/r2/'
figdir = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/figures/'
split_tag = '112028'
npix = 1024
cell = '2.5arcsec'
timerange = '11:20:28~11:20:30'

# === Create dirs ===
os.makedirs(imagedir_r2, exist_ok=True)
os.makedirs(figdir, exist_ok=True)

# === MS info and ephemeris ===
msinfo = hf.read_msinfo(slfcaledms_r2)
ephem2 = {
    'time':[60673.46944444445,60673.47986111111],
    'ra':[278.58900,278.60038],
    'dec':[-23.20101,-23.20037],
    'p0':[3.1699,3.1649],
    'delta':[0.98335911187512,0.98335931555501]
}

# === SPWs and frequency tags ===
spws = [f'0:{i}~{i+31}' for i in range(0, 4096, 32)]
n_panels = len(spws)
f_start = 0.856
f_step = 0.000208984
panel_tags, mid_freqs = [], []
for i in range(n_panels):
    ch_start = i * 32
    ch_end = ch_start + 31
    tag = f"{ch_start:04d}-{ch_end:04d}"
    mid_ch = (ch_start + ch_end) // 2
    mid_freq = f_start + mid_ch * f_step
    panel_tags.append(tag)
    mid_freqs.append(mid_freq)

# === Imaging loop ===
ia = ia_tool()
fits_list = []
for spw, tag in zip(spws, panel_tags):
    imagename = os.path.join(imagedir_r2, f'slfcaled_r2_{split_tag}_spw_0_{tag}')
    imagefile = imagename + '.image'
    im_fits = imagename + '.fits'

    print(f">>> Imaging SPW {spw}")
    tclean(vis=slfcaledms_r2,
           imagename=imagename,
           spw=spw,
           timerange=timerange,
           imsize=[npix, npix],
           cell=cell,
           weighting='briggs',
           robust=-0.5,
           niter=10000,
           interactive=False,
           specmode='mfs',
           stokes='I',
           gain=0.05,
           restoringbeam='')

    if not os.path.exists(imagefile):
        print(f"⚠️ Skipping {tag}: image not created.")
        continue

    print(f">>> Registering {imagefile} to {im_fits}")
    hf.imreg(vis=slfcaledms_r2,
             msinfo=msinfo,
             imagefile=imagefile,
             fitsfile=im_fits,
             ephem=ephem2,
             timerange=timerange,
             usephacenter=False,
             verbose=True)

    for ext in ['.flux', '.mask', '.model', '.residual', '.sumwt', '.pb']:
        f = imagename + ext
        if os.path.exists(f):
            os.system('rm -rf ' + f)

    if os.path.exists(im_fits):
        fits_list.append(im_fits)

# === Plot frequency grid ===
print(">>> Generating frequency-labeled panel image")

ncols, nrows = 16, 8
figsize = (20, 12)
fits_dict = {}
fits_files = glob.glob(os.path.join(imagedir_r2, f'slfcaled_r2_{split_tag}_spw_0_*.fits'))

for f in fits_files:
    basename = os.path.basename(f)
    parts = basename.split('_spw_0_')
    if len(parts) == 2:
        tag = parts[1].replace('.fits', '')
        fits_dict[tag] = f

fig, axes = plt.subplots(nrows, ncols, figsize=figsize,
                         gridspec_kw={'wspace': 0.0, 'hspace': 0.0})

for idx, (tag, freq) in enumerate(zip(panel_tags, mid_freqs)):
    row, col = divmod(idx, ncols)
    ax = axes[row][col]
    ax.set_xticks([])
    ax.set_yticks([])

    fname = fits_dict.get(tag)
    plotted = False

    if fname and os.path.exists(fname):
        try:
            m = sunpy.map.Map(fname)
            ax.imshow(m.data, cmap='jet', origin='lower', aspect='equal')
            plotted = True
        except Exception as e:
            print(f"⚠️ Failed to plot {tag}: {e}")

    if plotted:
        ax.text(0.05, 0.92, f"{freq:.3f} GHz", transform=ax.transAxes,
                fontsize=6, color='white', ha='left', va='top',
                bbox=dict(facecolor='black', alpha=0.3, lw=0))
    else:
        ax.imshow(np.ones((10, 10)), cmap='gray', vmin=0, vmax=1, origin='lower', aspect='equal')
        ax.text(0.05, 0.92, f"{freq:.3f} GHz", transform=ax.transAxes,
                fontsize=6, color='gray', ha='left', va='top')

output_file = os.path.join(figdir, f"slfcaled_image_r2_{split_tag}.png")
plt.savefig(output_file, dpi=300)
plt.close()
print(f"✅ Round 2 image panel saved to: {output_file}")

#############Check DR########
import os
import numpy as np
import matplotlib.pyplot as plt
from astropy.io import fits
import glob

# === Parameters ===
rmin_pix = 30
rmax_pix = 60
base_path = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/images_slfcaled'
precal_path = '/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/images/precal'
r1_path = os.path.join(base_path, 'r1')
r2_path = os.path.join(base_path, 'r2')

# === Function to compute DR using rectangular background
def compute_dr_rect(fits_file, rmin_pix=30, rmax_pix=60):
    with fits.open(fits_file) as hdul:
        data = hdul[0].data
    if data.ndim == 4:
        data = data[0, 0]
    elif data.ndim == 2:
        pass
    else:
        raise ValueError("Unrecognized data shape")
    peak = np.nanmax(data)
    rect = data[rmin_pix:rmax_pix, rmin_pix:rmax_pix]
    rms = np.sqrt(np.mean(rect**2))
    return peak / rms

# === Collect FITS file lists
def get_sorted_fits(folder, prefix):
    return sorted(glob.glob(os.path.join(folder, f'{prefix}_*.fits')))

fits_precal = get_sorted_fits(precal_path, 'precal_112028_spw_0')
fits_r1 = get_sorted_fits(r1_path, 'slfcaled_r1_112028_spw_0')
fits_r2 = get_sorted_fits(r2_path, 'slfcaled_r2_112028_spw_0')

assert len(fits_precal) == len(fits_r1) == len(fits_r2), "Mismatch in file counts"

# === Compute DR arrays
dr_precal = np.array([compute_dr_rect(f) for f in fits_precal])
dr_r1 = np.array([compute_dr_rect(f) for f in fits_r1])
dr_r2 = np.array([compute_dr_rect(f) for f in fits_r2])

# === Compute ratios
ratio_r1 = dr_r1 / dr_precal
ratio_r2 = dr_r2 / dr_precal

# === Plotting
import matplotlib.gridspec as gridspec
fig = plt.figure(figsize=(12, 8))
gs = gridspec.GridSpec(2, 1)

# Top panel: DR absolute values
ax1 = fig.add_subplot(gs[0])
ax1.plot(dr_precal, label='Precal', lw=1)
ax1.plot(dr_r1, label='Round 1', lw=1)
ax1.plot(dr_r2, label='Round 2', lw=1)
ax1.set_ylabel("Dynamic Range")
ax1.set_title("Dynamic Range Comparison")
ax1.legend()
ax1.grid(True)

# Bottom panel: Ratio (r1/precal and r2/precal)
ax2 = fig.add_subplot(gs[1])
ax2.plot(ratio_r1, label='R1 / Precal', color='orange')
ax2.plot(ratio_r2, label='R2 / Precal', color='green')
ax2.axhline(1.0, color='gray', lw=0.5, ls='--')
ax2.set_ylabel("DR Ratio")
ax2.set_xlabel("SPW Panel Index")
ax2.set_title("DR Improvement Factor")
ax2.legend()
ax2.grid(True)

plt.tight_layout()
output_path = os.path.join(base_path, 'dynamic_range_comparison_r2.png')
plt.savefig(output_path, dpi=300)
plt.close()
print(f"✅ Saved: {output_path}")


#############Round 3########

import os
import glob
from casatools import image
from suncasa.utils import helioimage2fits as hf
import numpy as np
import sunpy.map
import matplotlib.pyplot as plt

# ===== Setup =====
roundid = 'r3'
calmode = 'ap'
niter = 10000
robust = -0.5
uvrange = ''
refantenna = 'm002'
timerange = '11:20:28~11:20:30'
split_tag = '112028'

# ===== Directories =====
mask_round_dir = os.path.join(maskdir, f'round{roundid[-1]}')
imgprefix = os.path.join(imagedir, f'{roundid}/')
caltb_round_dir = os.path.join(caltbdir, roundid)
slfcal_input = slfcaldir + '20241229.falre.r.slfcalr2.ms'
slfcal_output = slfcaldir + '20241229.falre.r.slfcalr3.ms'
imagedir_out = os.path.join(imagedir_slfcaled, roundid + '/')
if not os.path.exists(mask_round_dir): os.makedirs(mask_round_dir)
if not os.path.exists(imgprefix): os.makedirs(imgprefix)
if not os.path.exists(caltb_round_dir): os.makedirs(caltb_round_dir)
if not os.path.exists(imagedir_out): os.makedirs(imagedir_out)

# ===== 1. Create new mask using 10% peak per image =====
print(">>> Generating 10% peak masks for Round 3...")
ia = image()
image_files = sorted(glob.glob(os.path.join(imagedir_out.replace('r3','r2'), f'slfcaled_r2_{split_tag}_spw_0_*.image')))
for imfile in image_files:
    try:
        ia.open(imfile)
        shape = ia.shape()
        csys = ia.coordsys().torecord()
        data = ia.getchunk()
        peakval = data.max()
        threshold = 0.1 * peakval
        mask = (data >= threshold).astype(int)
        ia.done()

        maskname = os.path.basename(imfile).replace('.image', '.mask')
        maskpath = os.path.join(mask_round_dir, maskname)
        if os.path.exists(maskpath): os.system(f'rm -rf {maskpath}')
        ia.fromshape(maskpath, shape, csys)
        ia.putchunk(mask)
        ia.done()
        print(f"✅ Created mask: {maskpath}")
    except Exception as e:
        print(f"⚠️ Failed to create mask for {imfile}: {e}")
        ia.done()

# ===== 2. Clean model images for Round 3 =====
print(">>> Creating model images for Round 3...")
clearcal(slfcal_input)
delmod(slfcal_input)
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    imagename = os.path.join(imgprefix, f'img_{roundid}_spw_{spw_tag}')
    maskname = os.path.join(mask_round_dir, f'slfcaled_r2_{split_tag}_spw_0_{spw_tag}.mask')
    im_fits = imagename + '.fits'

    tclean(vis=slfcal_input,
           imagename=imagename,
           spw=spw,
           timerange=timerange,
           imsize=[npix, npix],
           cell=cell,
           weighting='briggs',
           robust=robust,
           niter=niter,
           interactive=False,
           usemask='user',
           mask=maskname,
           savemodel='modelcolumn',
           specmode='mfs',
           stokes='I',
           gain=0.05,
           uvrange=uvrange,
           restoringbeam='')

    try:
        hf.imreg(vis=slfcal_input,
                 msinfo=hf.read_msinfo(slfcal_input),
                 imagefile=imagename + '.image',
                 fitsfile=im_fits,
                 ephem=ephem2,
                 timerange=timerange,
                 usephacenter=False,
                 verbose=True)
    except Exception as e:
        print(f"⚠️ Registration failed: {imagename} – {e}")

# ===== 3. Gaincal for Round 3 =====
print(">>> Running gaincal for Round 3...")
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    caltable = os.path.join(caltb_round_dir, f'slfcal_r3_spw_{spw_tag}.gcal')

    gaincal(vis=slfcal_input,
            caltable=caltable,
            spw=spw,
            refant=refantenna,
            gaintable=[],
            selectdata=True,
            timerange=timerange,
            calmode=calmode,
            gaintype='G',
            solint='int',
            uvrange=uvrange,
            minsnr=2.0,
            combine='',
            parang=True,
            append=False)

# ===== 4. Applycal =====
print(">>> Applying calibration for Round 3...")
clearcal(slfcal_input)
delmod(slfcal_input)
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    caltable = os.path.join(caltb_round_dir, f'slfcal_r3_spw_{spw_tag}.gcal')

    applycal(vis=slfcal_input,
             spw=spw,
             gaintable=[caltable],
             interp='linear',
             calwt=False,
             applymode='calonly',
             flagbackup=False,
             timerange=timerange)

# ===== 5. Split to calibrated MS =====
print(">>> Splitting Round 3 calibrated MS...")
split(vis=slfcal_input, outputvis=slfcal_output, datacolumn='corrected')

# ===== 6. Imaging calibrated data =====
print(">>> Imaging Round 3 calibrated MS...")
msinfo_r3 = hf.read_msinfo(slfcal_output)
ia = image()
fits_list = []

for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'spw_0_{ch_start:04d}-{ch_end:04d}'
    imagename = os.path.join(imagedir_out, f'slfcaled_r3_{split_tag}_{spw_tag}')
    imagefile = imagename + '.image'
    im_fits = imagename + '.fits'

    tclean(vis=slfcal_output,
           imagename=imagename,
           spw=spw,
           timerange=timerange,
           imsize=[npix, npix],
           cell=cell,
           weighting='briggs',
           robust=robust,
           niter=1000,
           interactive=False,
           specmode='mfs',
           stokes='I',
           gain=0.05)

    if os.path.exists(imagefile):
        hf.imreg(vis=slfcal_output,
                 msinfo=msinfo_r3,
                 imagefile=imagefile,
                 fitsfile=im_fits,
                 ephem=ephem2,
                 timerange=timerange,
                 usephacenter=False,
                 verbose=True)
        fits_list.append(im_fits)

# ===== 7. Plotting panel image =====
print(">>> Plotting summary image panel for Round 3...")
ncols, nrows = 16, 8
figsize = (20, 12)
f_start = 0.856
f_step = 0.000208984
panel_tags = []
mid_freqs = []
for i in range(4096 // 32):
    ch_start = i * 32
    ch_end = min(ch_start + 31, 4095)
    tag = f"{ch_start:04d}-{ch_end:04d}"
    mid_ch = (ch_start + ch_end) // 2
    mid_freq = f_start + mid_ch * f_step
    panel_tags.append(tag)
    mid_freqs.append(mid_freq)

fits_dict = {}
for f in glob.glob(os.path.join(imagedir_out, f'slfcaled_r3_{split_tag}_spw_0_*.fits')):
    tag = os.path.basename(f).split('_spw_0_')[-1].replace('.fits', '')
    fits_dict[tag] = f

fig, axes = plt.subplots(nrows, ncols, figsize=figsize,
                         gridspec_kw={'wspace': 0.0, 'hspace': 0.0})

for idx, (spw_tag, freq) in enumerate(zip(panel_tags, mid_freqs)):
    row, col = divmod(idx, ncols)
    ax = axes[row][col]
    ax.set_xticks([])
    ax.set_yticks([])
    fname = fits_dict.get(spw_tag)
    plotted = False
    if fname and os.path.exists(fname):
        try:
            m = sunpy.map.Map(fname)
            ax.imshow(m.data, cmap='jet', origin='lower', aspect='equal')
            plotted = True
        except: pass
    if plotted:
        ax.text(0.05, 0.92, f"{freq:.3f} GHz", transform=ax.transAxes,
                fontsize=6, color='white', ha='left', va='top',
                bbox=dict(facecolor='black', alpha=0.3, lw=0))
    else:
        ax.imshow(np.ones((10, 10)), cmap='gray', vmin=0, vmax=1, origin='lower')
        ax.text(0.05, 0.92, f"{freq:.3f} GHz", transform=ax.transAxes,
                fontsize=6, color='gray', ha='left', va='top')

plt.savefig(os.path.join(imagedir_out, f"slfcaled_image_r3_{split_tag}.png"), dpi=300)
plt.close()
print("✅ Round 3 full image panel saved.")

###########Check DR
import os
import numpy as np
import matplotlib.pyplot as plt
import sunpy.map
import csv

# === Parameters ===
split_tag = '112028'
n_panels = 4096 // 32
base_dir = "/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/images_slfcaled"
precal_dir = "/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/images/precal"
freqs = [0.856 + ((i * 32 + 15.5) * 0.000208984) for i in range(n_panels)]
spw_tags = [f"{i*32:04d}-{i*32+31:04d}" for i in range(n_panels)]

# === DR computation function ===
def compute_dr_rect(fits_file, rmin_pix=30, rmax_pix=60):
    try:
        m = sunpy.map.Map(fits_file)
        data = m.data
        sub = data[rmin_pix:rmax_pix, rmin_pix:rmax_pix]
        rms = np.sqrt(np.mean(sub**2))
        peak = np.nanmax(data)
        return peak / rms if rms > 0 else np.nan
    except Exception as e:
        print(f"⚠️ Failed for {fits_file}: {e}")
        return np.nan

# === Load DRs ===
drs = {'precal': [], 'r1': [], 'r2': [], 'r3': []}
for tag in spw_tags:
    f0 = os.path.join(precal_dir, f"precal_{split_tag}_spw_0_{tag}.fits")
    f1 = os.path.join(base_dir, "r1", f"slfcaled_r1_{split_tag}_spw_0_{tag}.fits")
    f2 = os.path.join(base_dir, "r2", f"slfcaled_r2_{split_tag}_spw_0_{tag}.fits")
    f3 = os.path.join(base_dir, "r3", f"slfcaled_r3_{split_tag}_spw_0_{tag}.fits")

    drs['precal'].append(compute_dr_rect(f0))
    drs['r1'].append(compute_dr_rect(f1))
    drs['r2'].append(compute_dr_rect(f2))
    drs['r3'].append(compute_dr_rect(f3))

# === Convert to arrays ===
dr_precal = np.array(drs['precal'])
dr_r1 = np.array(drs['r1'])
dr_r2 = np.array(drs['r2'])
dr_r3 = np.array(drs['r3'])

# === Compute improvement ratios ===
r1_ratio = dr_r1 / dr_precal
r2_ratio = dr_r2 / dr_precal
r3_ratio = dr_r3 / dr_precal

# === Save CSV ===
csv_path = os.path.join(base_dir, 'dynamic_range_all.csv')
with open(csv_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['SPW Tag', 'Freq (GHz)', 'precal', 'r1', 'r2', 'r3', 'r1/precal', 'r2/precal', 'r3/precal'])
    for i in range(n_panels):
        writer.writerow([spw_tags[i], f"{freqs[i]:.3f}", 
                         f"{dr_precal[i]:.1f}", f"{dr_r1[i]:.1f}", f"{dr_r2[i]:.1f}", f"{dr_r3[i]:.1f}",
                         f"{r1_ratio[i]:.2f}", f"{r2_ratio[i]:.2f}", f"{r3_ratio[i]:.2f}"])
print(f"✅ CSV saved to {csv_path}")

# === Plot DR values ===
plt.figure(figsize=(12, 6))
plt.plot(freqs, dr_precal, label='precal', lw=1.2)
plt.plot(freqs, dr_r1, label='r1', lw=1.2)
plt.plot(freqs, dr_r2, label='r2', lw=1.2)
plt.plot(freqs, dr_r3, label='r3', lw=1.2)
plt.xlabel("Frequency (GHz)")
plt.ylabel("Dynamic Range")
plt.title("Dynamic Range Comparison (precal vs r1/r2/r3)")
plt.legend()
plt.grid(True)
out1 = os.path.join(base_dir, "dynamic_range_comparison_all.png")
plt.savefig(out1, dpi=300)
plt.close()
print(f"✅ DR plot saved to: {out1}")

# === Plot improvement ratios ===
plt.figure(figsize=(12, 6))
plt.plot(freqs, r1_ratio, label='r1/precal', lw=1.2)
plt.plot(freqs, r2_ratio, label='r2/precal', lw=1.2)
plt.plot(freqs, r3_ratio, label='r3/precal', lw=1.2)
plt.xlabel("Frequency (GHz)")
plt.ylabel("DR Improvement Factor")
plt.title("DR Improvement (Ratio over Precal)")
plt.grid(True)
plt.legend()
out2 = os.path.join(base_dir, "dynamic_range_ratio_all.png")
plt.savefig(out2, dpi=300)
plt.close()
print(f"✅ Ratio plot saved to: {out2}")
