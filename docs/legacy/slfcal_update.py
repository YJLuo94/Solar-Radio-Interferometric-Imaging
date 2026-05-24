import sys
sys.path.append("/data/p022/Software/site-packages/") 
sys.path.append("/data/p022/Software/")
import os

# === Working Directories ===
slfcaldir = "/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/"  # Root directory for all self-calibration products
imagedir = slfcaldir + 'images/'              # Directory for intermediate self-calibration images
maskdir = slfcaldir + 'masks/'                # Directory for clean masks
imagedir_slfcaled = slfcaldir + 'images_slfcaled/'  # Directory for final self-calibrated images
caltbdir = slfcaldir + 'caltbs/'              # Directory for calibration tables

# === Create Directories if Not Exist ===
dirs = [slfcaldir, imagedir, maskdir, imagedir_slfcaled, caltbdir]
for d in dirs:
    if not os.path.exists(d):
        os.makedirs(d)

# === MS paths ===
ms0 = '/data/p022/solar_meerkat/2024_dec_29/scan4/flare/20241229.flare.cal.r.ms'
slfcal0 = slfcaldir + '20241229.flare.slfcal0.r.ms'

# === Split 10s mini MS for gain calibration ===
split(vis=ms0,outputvis=slfcal0,datacolumn='data',timerange='11:20:28~11:20:30')

# === Parameters and MS ===
split_tag = '112028'
slfcalms = slfcaldir + '20241229.flare.slfcal0.r.ms'
imagedir_precal = imagedir + 'precal/'
timerange = '11:20:28~11:20:30'
phasecenter = 'J2000 18h34m22.09 -23d12m03.0'

npix = 1024
cell = '2.5arcsec'
spws = [f'0:{i}~{i+31}' for i in range(0, 4096, 32)]

import os
import matplotlib.pyplot as plt
import sunpy.map
import numpy as np
import glob
from casatools import image as ia_tool
from suncasa.utils import helioimage2fits as hf

if not os.path.exists(imagedir_precal):
    os.makedirs(imagedir_precal)

msinfo = hf.read_msinfo(slfcalms)
ephem2 = {'time':[60673.46944444445,60673.47986111111],
          'ra':[278.58900,278.60038],
          'dec':[-23.20101,-23.20037],
          'p0':[3.1699,3.1649],
          'delta':[0.98335911187512,0.98335931555501]}

ia = ia_tool()
fits_list = []

# === Imaging per SPW ===
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
           gain=0.05,
           datacolumn='data')

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

    clnjunks = ['.flux', '.mask', '.model', '.residual', '.sumwt', '.pb']
    for ext in clnjunks:
        f = imagename + ext
        if os.path.exists(f):
            os.system('rm -rf ' + f)

    if os.path.exists(im_fits):
        fits_list.append(im_fits)

# === Plotting setup ===
ncols, nrows = 16, 8
figsize = (20, 12)
f_start = 0.856
f_step = 0.000208984

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
fits_files = glob.glob(os.path.join(imagedir_precal, f'precal_{split_tag}_spw_0_*.fits'))
for f in fits_files:
    basename = os.path.basename(f)
    parts = basename.split('_spw_0_')
    if len(parts) == 2:
        spw_tag = parts[-1].replace('.fits', '')
        fits_dict[spw_tag] = f

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

output_file = os.path.join(imagedir_precal, f"precal_image_{split_tag}.png")
plt.savefig(output_file, dpi=300)
plt.close()
print(f"✅ Final image grid saved to: {output_file}")

# =========== generate masks =========
import os
import glob
import re

# === Parse cell string robustly (e.g. '2.5 arcsec' or '2.5arcsec')
def parse_cell_arcsec(cell_str):
    try:
        return float(re.findall(r'[\d.]+', cell_str)[0])
    except:
        raise ValueError(f"❌ Failed to parse cell size from '{cell_str}'")

# === Parameters ===
cell_arcsec = parse_cell_arcsec(cell)  # cell previously defined as '2.5arcsec'
radius_arcsec = 1100.0
radius_pix = int(radius_arcsec / cell_arcsec)

imagedir_precal = imagedir + 'precal/'
mask_round_dir = os.path.join(maskdir, 'r1')
if not os.path.exists(mask_round_dir):
    os.makedirs(mask_round_dir)

image_files = sorted(glob.glob(os.path.join(imagedir_precal, f'precal_{split_tag}_spw_0_*.image')))

for imfile in image_files:
    try:
        ia.open(imfile)
        shape = ia.shape()
        nx, ny = shape[0], shape[1]
        cx, cy = nx // 2, ny // 2
        csys = ia.coordsys().torecord()
        ia.done()

        # Output mask path
        maskname = os.path.basename(imfile).replace('.image', '.mask')
        maskpath = os.path.join(mask_round_dir, maskname)
        if os.path.exists(maskpath):
            os.system(f'rm -rf {maskpath}')

        # Create mask with full-disk circular region
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


# =========== First round of self-calibration =========

import os
from suncasa.utils import helioimage2fits as hf

# === Round 1 self-calibration parameters ===
calprefix = caltbdir + 'slf' + 'r1'
imgprefix = imagedir + 'r1/'
refantenna = 'm002'
niter = 2000
robust = 1.0
calmode = 'p'
uvrange = ''
slfcalms = slfcaldir + '20241229.flare.slfcal0.r.ms'
split_tag = '112028'

# === Prepare output directory ===
if not os.path.exists(imgprefix):
    os.makedirs(imgprefix)

# === Clear any existing calibration and model columns ===
clearcal(slfcalms)
delmod(slfcalms)

# === Imaging model per SPW ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    imagename = f'{imgprefix}img_r1_spw_{spw_tag}'
    maskname = os.path.join(maskdir, 'r1', f'precal_{split_tag}_spw_0_{spw_tag}.mask')
    im_fits = imagename + '.fits'
    msinfo = hf.read_msinfo(slfcalms)

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
           restoringbeam='',
           datacolumn='data')

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

    # === Cleanup intermediate CASA files ===
    clnjunks = ['.flux', '.mask', '.model', '.psf', '.residual', '.sumwt', '.pb']
    for ext in clnjunks:
        f = imagename + ext
        if os.path.exists(f):
            os.system(f'rm -rf ' + f)


####Generate the self-calibration table
# === Define Round 1 calibration folder ===
calround = 'r1'
caltb_round_dir = os.path.join(caltbdir, calround)
if not os.path.exists(caltb_round_dir):
    os.makedirs(caltb_round_dir)

# === Measurement Set ===
slfcalms = slfcaldir + '20241229.flare.slfcal0.r.ms'
refantenna = 'm002'
calmode = 'p'
uvrange = ''
timerange = '11:20:28~11:20:30'

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
                timerange=timerange,
                calmode=calmode,
                gaintype='G',
                solint='int',
                uvrange=uvrange,
                minsnr=3.0,
                combine='',
                parang=True,
                append=False)
        print(f"✅ Gaincal completed for SPW {spw_tag}")
    except Exception as e:
        print(f"⚠️ Gaincal failed for SPW {spw_tag}: {e}")

##### Applycal ######
print(">>> Starting safe applycal for Round 1 (per SPW)")

# Step 0: Clear previous calibration and model
clearcal(slfcalms)
delmod(slfcalms)
print("🧹 Cleared previous calibration (clearcal) and model (delmod) from MS.")

# Step 1: Apply calibration one SPW at a time (entire time range)
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
                 flagbackup=False)  # ← timerange removed
        print(f"✅ Calibration applied for SPW {spw}")
    except Exception as e:
        print(f"❌ Applycal failed for SPW {spw_tag}: {e}")

# === Split out corrected data ===
print(">>> Splitting calibrated data into new MS for Round 1")

slfcaledms = slfcaldir + '20241229.flare.slfcalr1.r.ms'
split(vis=slfcalms,
      outputvis=slfcaledms,
      datacolumn='corrected')

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
slfcaledms = slfcaldir + '20241229.flare.slfcalr1.r.ms'
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
           gain=0.05,
           datacolumn='data')

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
            os.system(f'rm -rf ' + f)

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

#######Check DR range
import os
import numpy as np
import matplotlib.pyplot as plt
import sunpy.map

# === Input directories ===
precal_dir = imagedir + 'precal/'
r1_dir = imagedir_slfcaled + 'r1/'
figdir = slfcaldir + 'figures/'
split_tag = '112028'

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

# === DR calculation using rectangular background region ===
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



#######################Round 2 ###########
import os
from suncasa.utils import helioimage2fits as hf

# === Parameters ===
calround = 'r2'
imgprefix = imagedir + calround + '/'
refantenna = 'm002'
niter = 5000
robust = 0.5
calmode = 'p'
uvrange = ''
split_tag = '112028'
slfcalms = slfcaldir + '20241229.flare.slfcalr1.r.ms'

if not os.path.exists(imgprefix):
    os.makedirs(imgprefix)

# === Clear model & calibration before building new one ===
clearcal(slfcalms)
delmod(slfcalms)

# === Loop over SPWs to generate model ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    imagename = f'{imgprefix}img_r2_spw_{spw_tag}'
    maskname = os.path.join(maskdir, 'r1', f'precal_{split_tag}_spw_0_{spw_tag}.mask')
    im_fits = imagename + '.fits'
    msinfo = hf.read_msinfo(slfcalms)

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
           restoringbeam='',
           datacolumn='data')

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

    clnjunks = ['.flux', '.mask', '.model', '.psf', '.residual', '.sumwt', '.pb']
    for ext in clnjunks:
        f = imagename + ext
        if os.path.exists(f):
            os.system('rm -rf ' + f)


#############
import os

# === Setup paths and parameters ===
calround = 'r2'
caltb_round_dir = os.path.join(caltbdir, calround)
if not os.path.exists(caltb_round_dir):
    os.makedirs(caltb_round_dir)

slfcalms = slfcaldir + '20241229.flare.slfcalr1.r.ms'
refantenna = 'm002'
calmode = 'p'
uvrange = ''
timerange = '11:20:28~11:20:30'

# === Loop over SPWs and run gaincal ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    caltable = os.path.join(caltb_round_dir, f'slfcal_r2_spw_{spw_tag}.gcal')

    print(f"📡 Running gaincal for SPW {spw} → {caltable}")

    try:
        gaincal(vis=slfcalms,
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
                minsnr=3.0,
                combine='',
                parang=True,
                append=False)
        print(f"✅ Gaincal completed for SPW {spw_tag}")
    except Exception as e:
        print(f"❌ Gaincal failed for SPW {spw_tag}: {e}")

######################
print(">>> Applying gaincal tables to entire MS (Round 2)")

# === Paths ===
slfcalms = slfcaldir + '20241229.flare.slfcalr1.r.ms'
slfcaledms = slfcaldir + '20241229.flare.slfcalr2.r.ms'
caltb_round_dir = os.path.join(caltbdir, 'r2')

# === Clear previous corrections (if any) ===
clearcal(slfcalms)
delmod(slfcalms)

# === Apply gaincal for each SPW ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    caltable = os.path.join(caltb_round_dir, f'slfcal_r2_spw_{spw_tag}.gcal')

    if not os.path.exists(caltable):
        print(f"⚠️ Calibration table missing: {caltable}")
        continue

    print(f"📡 Applying calibration for SPW {spw}")
    try:
        applycal(vis=slfcalms,
                 spw=spw,
                 gaintable=[caltable],
                 interp='linear',
                 calwt=False,
                 applymode='calonly',
                 flagbackup=False)
        print(f"✅ Calibration applied for SPW {spw_tag}")
    except Exception as e:
        print(f"❌ Applycal failed for SPW {spw_tag}: {e}")

# === Split calibrated MS to new file ===
print(">>> Splitting calibrated MS to: ", slfcaledms)
split(vis=slfcalms,
      outputvis=slfcaledms,
      datacolumn='corrected')

print(f"✅ Calibrated MS saved to: {slfcaledms}")

######################
print(">>> Starting imaging of self-calibrated MS (Round 2)")

import os
import matplotlib.pyplot as plt
import sunpy.map
import numpy as np
import glob
from suncasa.utils import helioimage2fits as hf

# === Paths and setup ===
imagedir_r2 = imagedir_slfcaled + 'r2/'
if not os.path.exists(imagedir_r2):
    os.makedirs(imagedir_r2)

split_tag = '112028'
timerange = '11:20:28~11:20:30'
slfcaledms = slfcaldir + '20241229.flare.slfcalr2.r.ms'
msinfo_r2 = hf.read_msinfo(slfcaledms)

fits_list = []

# === Imaging ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'spw_0_{ch_start:04d}-{ch_end:04d}'
    imagename = imagedir_r2 + f'slfcaled_r2_{split_tag}_{spw_tag}'
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
           gain=0.05,
           datacolumn='data')

    if not os.path.exists(imagefile):
        print(f"⚠️ Skipping {spw_tag}: .image not created.")
        continue

    print(f">>> Registering image {imagefile} to {im_fits}")
    hf.imreg(vis=slfcaledms,
             msinfo=msinfo_r2,
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
print(">>> Plotting image grid for self-calibrated MS (Round 2)")

ncols, nrows = 16, 8
figsize = (20, 12)
f_start = 0.856
f_step = 0.000208984

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
fits_files = glob.glob(os.path.join(imagedir_r2, f'slfcaled_r2_{split_tag}_spw_0_*.fits'))
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

output_file = os.path.join(imagedir_r2, f"slfcaled_image_r2_{split_tag}.png")
plt.savefig(output_file, dpi=300)
plt.close()

print(f"✅ Final frequency-labeled Round 2 image grid saved to: {output_file}")

############################
import os
import numpy as np
import matplotlib.pyplot as plt
import sunpy.map

# === Input directories ===
precal_dir = imagedir + 'precal/'
r1_dir = imagedir_slfcaled + 'r1/'
r2_dir = imagedir_slfcaled + 'r2/'
figdir = slfcaldir + 'figures/'
split_tag = '112028'

if not os.path.exists(figdir):
    os.makedirs(figdir)

# === Frequency info ===
f_start = 0.856
f_step = 0.000208984
n_spws = 4096 // 32

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

# === Compute DRs ===
dr_precal, dr_r1, dr_r2 = [], [], []

for tag in panel_tags:
    f_precal = os.path.join(precal_dir, f'precal_{split_tag}_spw_0_{tag}.fits')
    f_r1 = os.path.join(r1_dir, f'slfcaled_r1_{split_tag}_spw_0_{tag}.fits')
    f_r2 = os.path.join(r2_dir, f'slfcaled_r2_{split_tag}_spw_0_{tag}.fits')

    dr0 = compute_dr_rect(f_precal) if os.path.exists(f_precal) else np.nan
    dr1 = compute_dr_rect(f_r1) if os.path.exists(f_r1) else np.nan
    dr2 = compute_dr_rect(f_r2) if os.path.exists(f_r2) else np.nan

    dr_precal.append(dr0)
    dr_r1.append(dr1)
    dr_r2.append(dr2)

# === Plot 1: DR comparison (Precal vs R1 vs R2) ===
fig, ax = plt.subplots(figsize=(14, 6), constrained_layout=True)
ax.plot(mid_freqs, dr_precal, 'o-', label='Precal')
ax.plot(mid_freqs, dr_r1, 's-', label='Selfcal R1')
ax.plot(mid_freqs, dr_r2, 'd-', label='Selfcal R2')
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("Dynamic Range (Peak / RMS)")
ax.set_title("Dynamic Range Comparison: Precal vs R1 vs R2")
ax.legend()
ax.grid(True)
outfile1 = os.path.join(figdir, 'dynamic_range_comparison_r2.png')
fig.savefig(outfile1, dpi=300, bbox_inches='tight')
plt.close(fig)
print(f"✅ Saved: {outfile1}")

# === Plot 2: DR improvement factor (R1 / Precal) ===
dr_ratio_r1 = np.array(dr_r1) / np.array(dr_precal)
fig, ax = plt.subplots(figsize=(14, 4), constrained_layout=True)
ax.plot(mid_freqs, dr_ratio_r1, 'd-', color='green')
ax.axhline(1.0, color='gray', linestyle='--')
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("DR Ratio (R1 / Precal)")
ax.set_title("DR Improvement Factor: R1 / Precal")
ax.grid(True)
outfile2 = os.path.join(figdir, 'dynamic_range_ratio_r1.png')
fig.savefig(outfile2, dpi=300, bbox_inches='tight')
plt.close(fig)
print(f"✅ Saved: {outfile2}")

# === Plot 3: DR improvement factor (R2 / R1) ===
dr_ratio_r2_r1 = np.array(dr_r2) / np.array(dr_r1)
fig, ax = plt.subplots(figsize=(14, 4), constrained_layout=True)
ax.plot(mid_freqs, dr_ratio_r2_r1, 'o-', color='purple')
ax.axhline(1.0, color='gray', linestyle='--')
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("DR Ratio (R2 / R1)")
ax.set_title("DR Improvement Factor: R2 / R1")
ax.grid(True)
outfile3 = os.path.join(figdir, 'dynamic_range_ratio_r2_vs_r1.png')
fig.savefig(outfile3, dpi=300, bbox_inches='tight')
plt.close(fig)
print(f"✅ Saved: {outfile3}")


###############round 3
import os
from suncasa.utils import helioimage2fits as hf

# === Parameters ===
calround = 'r3'
imgprefix = imagedir + calround + '/'
refantenna = 'm002'
niter = 5000
robust = 0.0
calmode = 'a'
uvrange = ''
split_tag = '112028'
slfcalms = slfcaldir + '20241229.flare.slfcalr2.r.ms'

if not os.path.exists(imgprefix):
    os.makedirs(imgprefix)

# === Clear model & calibration before building new one ===
clearcal(slfcalms)
delmod(slfcalms)

# === Loop over SPWs to generate model ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    imagename = f'{imgprefix}img_r3_spw_{spw_tag}'
    maskname = os.path.join(maskdir, 'r1', f'precal_{split_tag}_spw_0_{spw_tag}.mask')
    im_fits = imagename + '.fits'
    msinfo = hf.read_msinfo(slfcalms)

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
           restoringbeam='',
           datacolumn='data')

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

    clnjunks = ['.flux', '.mask', '.model', '.psf', '.residual', '.sumwt', '.pb']
    for ext in clnjunks:
        f = imagename + ext
        if os.path.exists(f):
            os.system('rm -rf ' + f)

#################
import os

# === Setup paths and parameters ===
calround = 'r3'
caltb_round_dir = os.path.join(caltbdir, calround)
if not os.path.exists(caltb_round_dir):
    os.makedirs(caltb_round_dir)

slfcalms = slfcaldir + '20241229.flare.slfcalr2.r.ms'
refantenna = 'm002'
calmode = 'a'
uvrange = ''
timerange = '11:20:28~11:20:30'

# === Loop over SPWs and run gaincal ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    caltable = os.path.join(caltb_round_dir, f'slfcal_r3_spw_{spw_tag}.gcal')

    print(f"📡 Running gaincal for SPW {spw} → {caltable}")

    try:
        gaincal(vis=slfcalms,
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
                minsnr=3.0,
                combine='',
                parang=True,
                append=False)
        print(f"✅ Gaincal completed for SPW {spw_tag}")
    except Exception as e:
        print(f"❌ Gaincal failed for SPW {spw_tag}: {e}")


#####################
print(">>> Applying gaincal tables to entire MS (Round 3)")

# === Paths ===
slfcalms = slfcaldir + '20241229.flare.slfcalr2.r.ms'
slfcaledms = slfcaldir + '20241229.flare.slfcalr3.r.ms'
caltb_round_dir = os.path.join(caltbdir, 'r3')

# === Clear previous corrections (if any) ===
clearcal(slfcalms)
delmod(slfcalms)

# === Apply gaincal for each SPW ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'
    caltable = os.path.join(caltb_round_dir, f'slfcal_r3_spw_{spw_tag}.gcal')

    if not os.path.exists(caltable):
        print(f"⚠️ Calibration table missing: {caltable}")
        continue

    print(f"📡 Applying calibration for SPW {spw}")
    try:
        applycal(vis=slfcalms,
                 spw=spw,
                 gaintable=[caltable],
                 interp='linear',
                 calwt=False,
                 applymode='calonly',
                 flagbackup=False)
        print(f"✅ Calibration applied for SPW {spw_tag}")
    except Exception as e:
        print(f"❌ Applycal failed for SPW {spw_tag}: {e}")

# === Split calibrated MS to new file ===
print(">>> Splitting calibrated MS to: ", slfcaledms)
split(vis=slfcalms,
      outputvis=slfcaledms,
      datacolumn='corrected')

print(f"✅ Calibrated MS saved to: {slfcaledms}")

########################
print(">>> Starting imaging of self-calibrated MS (Round 3)")

import os
import matplotlib.pyplot as plt
import sunpy.map
import numpy as np
import glob
from suncasa.utils import helioimage2fits as hf

# === Paths and setup ===
imagedir_r3 = imagedir_slfcaled + 'r3/'
if not os.path.exists(imagedir_r3):
    os.makedirs(imagedir_r3)

split_tag = '112028'
timerange = '11:20:28~11:20:30'
slfcaledms = slfcaldir + '20241229.flare.slfcalr3.r.ms'
msinfo_r3 = hf.read_msinfo(slfcaledms)

fits_list = []

# === Imaging ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'spw_0_{ch_start:04d}-{ch_end:04d}'
    imagename = imagedir_r3 + f'slfcaled_r3_{split_tag}_{spw_tag}'
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
           gain=0.05,
           datacolumn='data')

    if not os.path.exists(imagefile):
        print(f"⚠️ Skipping {spw_tag}: .image not created.")
        continue

    print(f">>> Registering image {imagefile} to {im_fits}")
    hf.imreg(vis=slfcaledms,
             msinfo=msinfo_r3,
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
print(">>> Plotting image grid for self-calibrated MS (Round 3)")

ncols, nrows = 16, 8
figsize = (20, 12)
f_start = 0.856
f_step = 0.000208984

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
fits_files = glob.glob(os.path.join(imagedir_r3, f'slfcaled_r3_{split_tag}_spw_0_*.fits'))
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

output_file = os.path.join(imagedir_r3, f"slfcaled_image_r3_{split_tag}.png")
plt.savefig(output_file, dpi=300)
plt.close()

print(f"✅ Final frequency-labeled Round 3 image grid saved to: {output_file}")


#################
import os
import numpy as np
import matplotlib.pyplot as plt
import sunpy.map

# === Directories ===
precal_dir = imagedir + 'precal/'
r1_dir = imagedir_slfcaled + 'r1/'
r2_dir = imagedir_slfcaled + 'r2/'
r3_dir = imagedir_slfcaled + 'r3/'
figdir = slfcaldir + 'figures/'
split_tag = '112028'

if not os.path.exists(figdir):
    os.makedirs(figdir)

# === Frequency and SPW tag setup ===
f_start = 0.856
f_step = 0.000208984
n_spws = 4096 // 32

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

# === Compute DR values ===
dr_precal, dr_r1, dr_r2, dr_r3 = [], [], [], []

for tag in panel_tags:
    f_precal = os.path.join(precal_dir, f'precal_{split_tag}_spw_0_{tag}.fits')
    f_r1 = os.path.join(r1_dir, f'slfcaled_r1_{split_tag}_spw_0_{tag}.fits')
    f_r2 = os.path.join(r2_dir, f'slfcaled_r2_{split_tag}_spw_0_{tag}.fits')
    f_r3 = os.path.join(r3_dir, f'slfcaled_r3_{split_tag}_spw_0_{tag}.fits')

    dr0 = compute_dr_rect(f_precal) if os.path.exists(f_precal) else np.nan
    dr1 = compute_dr_rect(f_r1) if os.path.exists(f_r1) else np.nan
    dr2 = compute_dr_rect(f_r2) if os.path.exists(f_r2) else np.nan
    dr3 = compute_dr_rect(f_r3) if os.path.exists(f_r3) else np.nan

    dr_precal.append(dr0)
    dr_r1.append(dr1)
    dr_r2.append(dr2)
    dr_r3.append(dr3)

# === Plot 1: DR Comparison ===
fig, ax = plt.subplots(figsize=(14, 6), constrained_layout=True)
ax.plot(mid_freqs, dr_precal, 'o-', label='Precal')
ax.plot(mid_freqs, dr_r1, 's-', label='Selfcal R1')
ax.plot(mid_freqs, dr_r2, 'd-', label='Selfcal R2')
ax.plot(mid_freqs, dr_r3, '^-', label='Selfcal R3')
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("Dynamic Range (Peak / RMS)")
ax.set_title("Dynamic Range Comparison: Precal vs R1 vs R2 vs R3")
ax.legend()
ax.grid(True)
outfile1 = os.path.join(figdir, 'dynamic_range_comparison_r3.png')
fig.savefig(outfile1, dpi=300, bbox_inches='tight')
plt.close()
print(f"✅ Saved: {outfile1}")

# === Plot 2: R1 / Precal ===
dr_ratio_r1 = np.array(dr_r1) / np.array(dr_precal)
fig, ax = plt.subplots(figsize=(14, 4), constrained_layout=True)
ax.plot(mid_freqs, dr_ratio_r1, 'd-', color='green')
ax.axhline(1.0, color='gray', linestyle='--')
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("DR Ratio (R1 / Precal)")
ax.set_title("DR Improvement Factor: R1 / Precal")
ax.grid(True)
outfile2 = os.path.join(figdir, 'dynamic_range_ratio_r1.png')
fig.savefig(outfile2, dpi=300, bbox_inches='tight')
plt.close(fig)
print(f"✅ Saved: {outfile2}")

# === Plot 3: R2 / Precal ===
dr_ratio_r2 = np.array(dr_r2) / np.array(dr_precal)
fig, ax = plt.subplots(figsize=(14, 4), constrained_layout=True)
ax.plot(mid_freqs, dr_ratio_r2, 's-', color='blue')
ax.axhline(1.0, color='gray', linestyle='--')
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("DR Ratio (R2 / Precal)")
ax.set_title("DR Improvement Factor: R2 / Precal")
ax.grid(True)
outfile3 = os.path.join(figdir, 'dynamic_range_ratio_r2.png')
fig.savefig(outfile3, dpi=300, bbox_inches='tight')
plt.close(fig)
print(f"✅ Saved: {outfile3}")

# === Plot 4: R3 / Precal ===
dr_ratio_r3 = np.array(dr_r3) / np.array(dr_precal)
fig, ax = plt.subplots(figsize=(14, 4), constrained_layout=True)
ax.plot(mid_freqs, dr_ratio_r3, '^-', color='purple')
ax.axhline(1.0, color='gray', linestyle='--')
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("DR Ratio (R3 / Precal)")
ax.set_title("DR Improvement Factor: R3 / Precal")
ax.grid(True)
outfile4 = os.path.join(figdir, 'dynamic_range_ratio_r3.png')
fig.savefig(outfile4, dpi=300, bbox_inches='tight')
plt.close(fig)
print(f"✅ Saved: {outfile4}")

# === Plot 5: R3 / R2 ===
dr_ratio_r3_vs_r2 = np.array(dr_r3) / np.array(dr_r2)
fig, ax = plt.subplots(figsize=(14, 4), constrained_layout=True)
ax.plot(mid_freqs, dr_ratio_r3_vs_r2, 'o-', color='orange')
ax.axhline(1.0, color='gray', linestyle='--')
ax.set_xlabel("Frequency (GHz)")
ax.set_ylabel("DR Ratio (R3 / R2)")
ax.set_title("DR Improvement Factor: R3 / R2")
ax.grid(True)
outfile5 = os.path.join(figdir, 'dynamic_range_ratio_r3_vs_r2.png')
fig.savefig(outfile5, dpi=300, bbox_inches='tight')
plt.close(fig)
print(f"✅ Saved: {outfile5}")



#############################applycal to all
import os

# === Setup paths ===
ms0 = '/data/p022/solar_meerkat/2024_dec_29/scan4/flare/20241229.flare.cal.r.ms'
ms_working_copy = os.path.join(slfcaldir, '20241229.flare.cal.r.ms')
split_output = os.path.join(slfcaldir, '20241229.flare.cal.r.slfcaled.ms')
caltb_rounds = ['r1', 'r2', 'r3']

# === Copy original MS as working MS ===
if not os.path.exists(ms_working_copy):
    os.system(f'cp -r {ms0} {ms_working_copy}')
    print(f"✅ Copied {ms0} → {ms_working_copy}")
else:
    print(f"ℹ️ Working MS already exists: {ms_working_copy}")

# === Clear previous calibration (if any) ===
clearcal(ms_working_copy)
delmod(ms_working_copy)
print("🧹 Cleared calibration and model from working MS")

# === Applycal per SPW with all three gaintables ===
for spw in spws:
    ch_start, ch_end = map(int, spw.split(':')[1].split('~'))
    spw_tag = f'{ch_start:04d}-{ch_end:04d}'

    gaintables = [
        os.path.join(caltbdir, r, f'slfcal_{r}_spw_{spw_tag}.gcal')
        for r in caltb_rounds
    ]

    if not all(os.path.exists(g) for g in gaintables):
        print(f"⚠️ Missing gaintables for SPW {spw_tag}. Skipping.")
        continue

    print(f"📡 Applying R1+R2+R3 calibration to SPW {spw_tag}")
    try:
        applycal(vis=ms_working_copy,
                 spw=spw,
                 gaintable=gaintables,
                 interp='linear',
                 calwt=False,
                 applymode='calonly',
                 flagbackup=False)
        print(f"✅ Applied calibration to SPW {spw_tag}")
    except Exception as e:
        print(f"❌ Applycal failed for SPW {spw_tag}: {e}")

# === Final split to produce calibrated full MS ===
print(f"🔄 Splitting calibrated MS to {split_output}")
split(vis=ms_working_copy,
      outputvis=split_output,
      datacolumn='corrected')

print(f"✅ Final calibrated full MS saved to: {split_output}")





























