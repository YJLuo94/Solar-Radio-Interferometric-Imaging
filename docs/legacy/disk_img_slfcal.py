######## Make the full disk image
### === Full-Disk Imaging Script for Science Purpose === ###
import sys
sys.path.append("/data/p022/Software/site-packages/")
sys.path.append("/data/p022/Software/")
import os
import shutil
import numpy as np
from astropy.time import Time
from astropy.coordinates import SkyCoord
from suncasa.utils import helioimage2fits as hf
from casatools import msmetadata



def do_pb_corr_shifted_center_katbeam(inpimage, shifted_ra_deg=0, shifted_dec_deg=0,
                                      pb_minval=1e-6, nan_to_one=False, pbband='LBand'):
    from casatools import image
    from katbeam import JimBeam
    from astropy.wcs import WCS
    import numpy as np
    import shutil
    ia = image()
    PBeam = JimBeam('MKAT-AA-L-JIM-2020' if pbband == 'LBand' else
                    'MKAT-AA-S-JIM-2020' if pbband == 'SBand' else
                    'MKAT-AA-UHF-JIM-2020')
    ia.open(inpimage)
    csys = ia.coordsys().torecord()
    imgdata = ia.getchunk()
    shape = imgdata.shape
    ia.close()

    try:
        freq = csys['spectral1']['wcs']['crval'] / 1e6
    except KeyError:
        freq = csys['spectral2']['wcs']['crval'] / 1e6

    cdelt = np.abs(csys['direction0']['cdelt'][0])
    unit = csys['direction0']['units'][0]
    if unit == 'rad':
        cdelt = np.rad2deg(cdelt)
    elif unit == "'":
        cdelt /= 60.

    cx, cy = shape[0] // 2, shape[1] // 2
    x = np.linspace(-cx, cx - 1, shape[0])
    y = np.linspace(-cy, cy - 1, shape[1])
    xx, yy = np.meshgrid(x, y)
    xx = xx.T * cdelt + shifted_ra_deg
    yy = yy.T * cdelt + shifted_dec_deg

    beam_I = PBeam.I(xx, yy, freq)
    beam_I = beam_I[:, :, None, None]

    if pb_minval is not None:
        beam_I = np.where(beam_I < pb_minval, pb_minval, beam_I)

    pbcor_imgdata = imgdata / beam_I if nan_to_one else np.where(np.isnan(beam_I), np.nan, imgdata / beam_I)

    pbimage = inpimage.replace('.image', '.katbeam.pb')
    if os.path.exists(pbimage): 
        shutil.rmtree(pbimage)
    shutil.copytree(inpimage, pbimage)
    ia.open(pbimage)
    ia.putchunk(beam_I)
    ia.done()

    pbcorimage = inpimage.replace('.image', '.katbeam_pbcor.image')
    if os.path.exists(pbcorimage):
        shutil.rmtree(pbcorimage)
    shutil.copytree(inpimage, pbcorimage)
    ia.open(pbcorimage)
    ia.putchunk(pbcor_imgdata)
    ia.done()

def do_pb_corr_shifted_center_holo(inpimage, shifted_ra_deg=0, shifted_dec_deg=0,
                                   pb_minval=1e-6, nan_to_one=False):
    import numpy as np
    from scipy.interpolate import RegularGridInterpolator
    from casatools import image
    import numpy as np
    from astropy.io import fits
    from astropy.wcs import WCS
    import shutil

    beam_file = "/data/p022/solar_meerkat/PB/MeerKAT_Lband_beam_StokesIV.npz"
    beam_data = np.load(beam_file)
    beam_I = beam_data["beam"][0]
    freqs = beam_data["freq_MHz"]
    offsets = beam_data["offsets"]

    interpolators = []
    for i in range(len(freqs)):
        log_beam = np.log10(np.abs(beam_I[i]) + 1e-6)
        interp = RegularGridInterpolator((offsets, offsets), log_beam, bounds_error=False, fill_value=np.nan)
        interpolators.append(interp)

    ia = image()
    ia.open(inpimage)
    csys = ia.coordsys().torecord()
    imgdata = ia.getchunk()
    shape = imgdata.shape
    ia.close()

    try:
        freq = csys['spectral1']['wcs']['crval'] / 1e6
    except KeyError:
        freq = csys['spectral2']['wcs']['crval'] / 1e6

    cdelt = np.abs(csys['direction0']['cdelt'][0])
    unit = csys['direction0']['units'][0]
    if unit == 'rad':
        cdelt = np.rad2deg(cdelt)
    elif unit == "'":
        cdelt /= 60.

    cx, cy = shape[0] // 2, shape[1] // 2
    x = np.linspace(-cx, cx - 1, shape[0])
    y = np.linspace(-cy, cy - 1, shape[1])
    xx, yy = np.meshgrid(x, y)
    xx = xx.T * cdelt + shifted_ra_deg
    yy = yy.T * cdelt + shifted_dec_deg

    idx = np.argmin(np.abs(freqs - freq))
    interp = interpolators[idx]
    points = np.stack([yy.ravel(), xx.ravel()], axis=-1)
    logpb = interp(points).reshape(shape[0], shape[1])
    pb = 10 ** logpb
    pb = pb[:, :, None, None]

    if pb_minval is not None:
        pb = np.where(pb < pb_minval, pb_minval, pb)

    pbcor_imgdata = imgdata / pb if nan_to_one else np.where(np.isnan(pb), np.nan, imgdata / pb)

    pbimage = inpimage.replace('.image', '.holopb')
    shutil.copytree(inpimage, pbimage)
    ia.open(pbimage)
    ia.putchunk(pb)
    ia.done()

    pbcorimage = inpimage.replace('.image', '.holo_pbcor.image')
    shutil.copytree(inpimage, pbcorimage)
    ia.open(pbcorimage)
    ia.putchunk(pbcor_imgdata)
    ia.done()


# === Paths ===
mspath = "/data/p022/solar_meerkat/2024_dec_29/scan4/full_disk_img_n/"
os.makedirs(mspath, exist_ok=True)
os.chdir(mspath)
msvis = "/data/p022/solar_meerkat/2024_dec_29/scan4/slfcal/20241229.flare.cal.r.slfcaled.ms/"
fits_root = os.path.join(mspath, 'fits')
tbf_root = os.path.join(mspath, 'fitstb')
fits_corr_holo_root = os.path.join(mspath, 'fits_corr_holo')
tbf_corr_holo_root = os.path.join(mspath, 'fitstb_corr_holo')
fits_corr_kat_root = os.path.join(mspath, 'fits_corr_katbeam')
tbf_corr_kat_root = os.path.join(mspath, 'fitstb_corr_katbeam')

for d in [fits_root, tbf_root, fits_corr_holo_root, tbf_corr_holo_root, fits_corr_kat_root, tbf_corr_kat_root]:
    os.makedirs(d, exist_ok=True)

# === Solar info ===
msinfo = hf.read_msinfo(msvis)
ephem2 = {'time':[60673.46944444445,60673.47986111111],'ra':[278.58900,278.60038],
          'dec':[-23.20101,-23.20037],'p0':[3.1699,3.1649],'delta':[0.98335911187512,0.98335931555501]}
c_pointing4 = SkyCoord('18h31m53.22s', '-20d34m14.7s')
c_sun4 = SkyCoord('18h34m22.09s', '-23d12m03.0s')
shifted_ra_deg = c_sun4.ra.value - c_pointing4.ra.value
shifted_dec_deg = c_sun4.dec.value - c_pointing4.dec.value

# === Parameters ===
spws = [f'0:{i}~{i+15}' for i in range(0, 4096, 16)]
imsize = [2048, 2048]
cell = '1.5arcsec'
phasecenter = 'J2000 18h34m22.09 -23d12m03.0'
specmode = 'mfs'
pblimit = 0.1
restoringbeam = []
niter = 50000
gain = 0.05
interactive = False
weighting = 'briggs'
robust = -0.5
gridder = 'standard'
pb_minval = 1e-8

# === timerange ===
trangelist = []
for i in range(50):
    ti = Time(Time('2024-12-29 11:19:40') + i * 2 / 3600 / 24, format='datetime')
    te = Time(Time('2024-12-29 11:19:42') + i * 2 / 3600 / 24, format='datetime')
    trange = ti.iso.replace('-', '/').replace(' ', '/') + '~' + te.iso.replace('-', '/').replace(' ', '/')
    trangelist.append(trange)

# === main loop ===
success_log = []
for trange in trangelist[40:41]:
    time_subfolder = trange[11:19].replace(':', '_')
    timpath = os.path.join(mspath, time_subfolder)  # temp processing folder
    os.makedirs(timpath, exist_ok=True)
    for d in [fits_root, tbf_root, fits_corr_holo_root, tbf_corr_holo_root, fits_corr_kat_root, tbf_corr_kat_root]:
        os.makedirs(os.path.join(d, time_subfolder), exist_ok=True)

    os.chdir(timpath)

    success_log_t = []
    for i, spw in enumerate(spws):
        spw_tag = f'{i:04d}'
        split_tag = time_subfolder
        chn_result = {'chn': i}
        msmd = msmetadata()
        msmd.open(msvis)

        # Always use spw=0 (since only one SPW), extract freqs of selected channels
        start_chan = int(spw.split(':')[1].split('~')[0])
        end_chan = int(spw.split(':')[1].split('~')[1]) + 1  # python slice is exclusive

        freqs_Hz = msmd.chanfreqs(0)[start_chan:end_chan]
        msmd.close()

        midfreq_MHz = np.mean(freqs_Hz) / 1e6
        freq_tag = f'{int(round(midfreq_MHz)):04d}MHz'

        for stokes in ['I', 'V']:
            imagename = f'chn_{split_tag}_{spw_tag}_{freq_tag}_{stokes}'
            try:
                tclean(vis=msvis, imagename=imagename, spw=spw, timerange=trange,
                       datacolumn='data', imsize=imsize, cell=cell, phasecenter=phasecenter,
                       stokes=stokes, specmode=specmode, niter=niter, pblimit=pblimit,
                       interactive=interactive, restoringbeam=restoringbeam, weighting=weighting,
                       robust=robust, gridder=gridder)

                # clear
                for ext in ['.flux', '.mask', '.model', '.residual', '.sumwt', '.pb', '.psf']:
                    os.system(f'rm -rf {imagename}{ext}')

                inpimage = imagename + '.image'

                # === Holography PB correction ===
                do_pb_corr_shifted_center_holo(inpimage, shifted_ra_deg, shifted_dec_deg,
                                      pb_minval=1e-6, nan_to_one=False)
                hf.imreg(vis=msvis, msinfo=msinfo,
                         imagefile=imagename + '.holo_pbcor.image',
                         fitsfile=os.path.join(fits_corr_holo_root, time_subfolder, imagename + '.fits'),
                         timerange=trange, ephem=ephem2, usephacenter=False)
                hf.imreg(vis=msvis, msinfo=msinfo,
                         imagefile=imagename + '.holo_pbcor.image',
                         fitsfile=os.path.join(tbf_corr_holo_root, time_subfolder, imagename + '.tb.fits'),
                         timerange=trange, ephem=ephem2, usephacenter=False, toTb=True)

                # === Katbeam PB correction ===
                do_pb_corr_shifted_center_katbeam(inpimage, shifted_ra_deg, shifted_dec_deg,
                                   pb_minval=1e-6, nan_to_one=False, pbband='LBand')
                hf.imreg(vis=msvis, msinfo=msinfo,
                         imagefile=imagename + '.katbeam_pbcor.image',
                         fitsfile=os.path.join(fits_corr_kat_root, time_subfolder, imagename + '.fits'),
                         timerange=trange, ephem=ephem2, usephacenter=False)
                hf.imreg(vis=msvis, msinfo=msinfo,
                         imagefile=imagename + '.katbeam_pbcor.image',
                         fitsfile=os.path.join(tbf_corr_kat_root, time_subfolder, imagename + '.tb.fits'),
                         timerange=trange, ephem=ephem2, usephacenter=False, toTb=True)

                # === original FITS and TB ===
                hf.imreg(vis=msvis, msinfo=msinfo,
                         imagefile=inpimage,
                         fitsfile=os.path.join(fits_root, time_subfolder, imagename + '.fits'),
                         timerange=trange, ephem=ephem2, usephacenter=False)
                hf.imreg(vis=msvis, msinfo=msinfo,
                         imagefile=inpimage,
                         fitsfile=os.path.join(tbf_root, time_subfolder, imagename + '.tb.fits'),
                         timerange=trange, ephem=ephem2, usephacenter=False, toTb=True)

                chn_result[stokes] = True
            except Exception as e:
                print(f"❌ Failed: {imagename} | Time: {trange} | Error: {e}")
                chn_result[stokes] = False

        success_log_t.append(chn_result)
    success_log.append(success_log_t)

# === keep log ===
#np.savez(os.path.join(mspath, f'success_log.npz'), status=success_log)
#print(f"✅ Imaging done for. Log saved.")




