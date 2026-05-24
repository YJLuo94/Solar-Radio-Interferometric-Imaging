############This is the script for calibration and imaging: execfile 'meerkat_proc_1229_scan4_point.py'

###Switch: on which steps you want to do
doinfo = True ##give information of the measurement set
do_partition = True ##split and average, also create mms file for the parallel processing
do_flag1 = True  ##Do first round flag
calc_ref = False ##Calclulate the reference antenna after flagging
do_setjy = True ##Set flux model for calibrator
do_crosscal1 = True ##Do first round of cross-calibrationn
do_applycal1 = True ##Do first round of apply calibrationn
do_flag2 = True  ##Do second round flag; after calibration
do_split1 = True  ##split the calibrated and flagged dataset, for check and quick redo -- now set to True otherwise some bugs.
do_crosscal2 = True ##Do second round of cross-calibrationn
do_applycal2 = True ##Do second round of apply calibrationn
do_split = True ##Split the calibrated dataset
do_qlimg = True ##Make quick look image
do_sciimg = True ##Make science image
#do_slfcal = False ##Do selfcalibartion --  will add later

###Parameters you may want to change accordingly

###For general information: better manually input
ncpus = 4 ##number of parallel threads
solar_burst = False ## for the scans including solar bursts, many parameters may need to adjust
orims = "/data/p022/dec2024_meerkat/1735466915_sdp_l0.ms/"##Original visbility
outputcalvis = '20241229.scan4.cal.ms'##Calibrated output visibility
workfolder = "/data/p022/solar_meerkat/2024_dec_29/scan4/pipe_new/" ##Working folder
dopol = False ##if do polarization, no need here
doparallel = True ##Do parallel processing, remember use casampi
domms = True ## if do parallel is Ture, should also set this to be Ture
channelbin = 1# Number of channels to average before calibration (during partition)
specavg = 1# Number of channels to (further) average after calibration (during split)
timeavg = '0s'# Time interval to average after calibration (during split),0s means no average
spw_s = '' ##frequency select
timeran = '' ##Time want to select
scans = '10,11,12,13' ##scan want to select -- can just select good calibration scan
badants = [] # List of bad antenna numbers (to flag)
badfreqranges = ['935~947MHz', '1160~1310MHz', '1476~1611MHz', '1670~1700MHz']# List of bad frequency ranges (to flag) -- this is for Lband
refantant = 'm002'  ##Refant antenna

###This is for you to manually select the field to use; 
bpfield = 'J1939-6342' #same as fluxfield
phasefield = 'J1830-3602' #phase and amp field; also the kcorrfield
tarfield = 'Pointing_4'
gainfields = str(bpfield) + ',' + str(phasefield)
calfields = str(bpfield) + ',' + str(phasefield) ##if no extra fields


###For control the crosscal
minbaselines = 4 # Minimum number of baselines to use while calibrating, no need to change

##Quicklook image parameters
#Parameters  you want to change
timerange1 = '11:17:00 ~ 11:30:30' #timerange
spw1 = '*:0.88~0.92 GHz' #frequency range
#Other Parameters set as default -- see lines 501-509 for reference

##Science image parameters
timerange2 = '11:17:00 ~ 11:30:30' #timerange
spw2 = '*:0.88~0.92 GHz' #frequency range
dopb_cor = True ##do primary beam correction based on katbeam
pbband = 'LBand' ##"LBand" "SBand" or "UHF"
deconvolver = 'multiscale' ## can also use 'mtmfs' for wide frewuency range
multiscale = [0, 5, 10, 15]
nterms = 2 # Number of taylor terms
gridder = 'wproject' ##better use this for wider field of view
wprojplanes = 512
niter = 50000
cell = '1.5arcsec'
robust = -0.5
imsize = [6144, 6144]
threshold = '0.01 mJy' ## S/N value if >= 1.0 and rmsmap != '', otherwise Jy
stokes = 'I'
restoringbeam = ''
pbthreshold = 0.1                 # Threshold below which to mask the PB for PB correction
#Other Parameters set as default -- see lines 539-560 for reference



##############################The following are running script ####################

import sys
sys.path.append("/data/p022/Software/site-packages/") ##Remember to use the sitepackages from Linux system
sys.path.append("/data/p022/Software/")
sys.path.append("/data/p022/Software/processMeerKAT/")
sys.path.append("/data/p022/Software/processMeerKAT/aux_scripts/")
sys.path.append("/data/p022/Software/processMeerKAT/crosscal_scripts/")
sys.path.append("/data/p022/Software/processMeerKAT/selfcal_scripts/")

import os
import numpy as np
import shutil
from pathlib import Path
import matplotlib.pyplot as plt
import time
start_time = time.time()


if os.path.exists(workfolder):
    os.chdir(workfolder)
else:
    os.makedirs(workfolder)
    os.chdir(workfolder)

with open("Log.txt", "w") as file:
    file.write("This is the Log file.\n")

visname = Path(orims).name
calprefix='cal/callib'
if os.path.exists(workfolder+'cal'):
    shutil.rmtree(workfolder+'cal')
    os.makedirs(workfolder+'cal')
else:
    os.makedirs(workfolder+'cal')
## information step##
if doinfo:
###### MS information  ######
#### listobs ####
    listobs(vis=orims,listfile=visname+'.listobs',overwrite=True)
#### plotants ####
    figfile=visname+'.ants.png'
    plotants(vis=orims,figfile=figfile)
    plt.close()
####write log
    with open("Log.txt", "a") as file:
        file.write("###################\n")
        file.write("Do infomation step.\n")
        file.write("Listobs file: {}\n".format(visname+'.listobs'))
        file.write("Antenna position Image: {}\n".format(visname+'.ants.png'))
        file.write("Information step completed\n")

###partition: split and average; provide the information ====  create the mms file
if do_partition:
    ##Split and average
    outputvis = visname.replace('.ms','.cal0.ms')
    chanaverage = True if channelbin > 1 else False
    correlation = '' if dopol else 'XX,YY'
    msmd.open(orims)
    nscans=msmd.nscans()
    msmd.done()
    if not domms:
        nscan = 1
    elif scans == '':
        nscan = nscans
    else:
        scanelements = scans.split(',')
        nscan = len(scanelements)
    mstransform(vis=orims, outputvis=outputvis, spw=spw_s, createmms=domms, datacolumn='DATA', chanaverage=chanaverage, chanbin=channelbin,\
        scan=scans, numsubms=nscan, separationaxis='scan', keepflags=True, usewtspectrum=True, nthreads=ncpus, correlation=correlation)
    ####write log
    with open("Log.txt", "a") as file:
        file.write("###################\n")
        file.write("Do Partition step.\n")
        file.write("Splited and averaged ms file: {}\n".format(outputvis))
        file.write("Partition step completed\n")


###Flag step: flag round 1
if do_flag1:
    msvis0 = visname.replace('.ms','.cal0.ms')
    ##### Data Flagging #####
    ##Can check flag information in the logger file [log.txt can only record a little]
    ## Bad frequencies ## --RFI channels
    if len(badfreqranges):
        badspw = '*:' + ',*:'.join(badfreqranges)
        flagdata(vis=msvis0, mode='manual', spw=badspw)
    ## Bad antennas ##
    if len(badants):
        badants = ",".join([str(bb) for bb in badants])
        flagdata(vis=msvis0, mode='manual', antenna=badants)
    ##flag auto-correlation
    flagdata(vis=msvis0, mode='manual', autocorr=True, action='apply',
        flagbackup=True, savepars=False, writeflags=True)
    ##Clip Zero-amp conponent: for scans without solar bursts, also set a maximum
    if solar_burst:
        flagdata(vis=msvis0, mode='clip', clipzeros=True)
    else:
        clip = [0., 50.]
        flagdata(vis=msvis0, mode="clip",clipminmax=clip ,clipoutside=True, clipzeros=True)
    ## Apply flag in tfcrop algorithm
    flagdata(vis=msvis0, mode='summary', datacolumn='DATA',name='flagr1.before_tfcrop.summary')
    ## calibration fields
    flagdata(vis=msvis0, mode='tfcrop', field=calfields,
        ntime='scan', timecutoff=5.0, freqcutoff=5.0, timefit='line',
        freqfit='line', extendflags=False, timedevscale=5., freqdevscale=5.,
        extendpols=True, growaround=False, action='apply', flagbackup=True,
        overwrite=True, writeflags=True, datacolumn='DATA')
    ## target fields -- pass if want to save solar bursts or only do very conservatively
    if solar_burst:
        pass
    else:
        flagdata(vis=msvis0, mode='tfcrop', field=tarfield,
            ntime='scan', timecutoff=6.0, freqcutoff=6.0, timefit='poly',
            freqfit='poly', extendflags=False, timedevscale=5., freqdevscale=5.,
            extendpols=True, growaround=False, action='apply', flagbackup=True,
            overwrite=True, writeflags=True, datacolumn='DATA')
    ## Conservatively extend flags
    flagdata(vis=msvis0, mode='summary', datacolumn='DATA',name='flagr1.before_extend.summary')
    ## calibration fields
    flagdata(vis=msvis0, mode='extend', field=calfields,
        datacolumn='data', clipzeros=True, ntime='scan', extendflags=False,
        extendpols=True, growtime=80., growfreq=80., growaround=False,
        flagneartime=False, flagnearfreq=False, action='apply',
        flagbackup=True, overwrite=True, writeflags=True)
    ## target fields -- pass if want to save solar bursts or only do very conservatively
    if solar_burst:
        pass
    else:
        flagdata(vis=msvis0, mode='extend', field=tarfield,
            datacolumn='data', clipzeros=True, ntime='scan', extendflags=False,
            extendpols=True, growtime=80., growfreq=80., growaround=False,
            flagneartime=False, flagnearfreq=False, action='apply',
            flagbackup=True, overwrite=True, writeflags=True)
    ## Summary
    flagdata(vis=msvis0, mode='summary', datacolumn='DATA', name='flagr1.after_extend.summary')
    ####write log
    with open("Log.txt", "a") as file:
        file.write("###################\n")
        file.write("Do Flag round 1 step.\n")
        file.write("flag bad frequency channels, bad antennas; did auto-correlation flagging;\n")
        file.write("Did clip flagging, do flag on tfcrop and extend algorithm.\n")
        file.write("Can check the logger file for detailed information (not this log)\n")
        file.write("Flag round 1 step completed\n")

###Calculate reference antenna step
if calc_ref:
    import calc_refant
    refantant, badants = calc_refant.get_ref_ant(visname = msvis0, fluxfield = bpfield)
    #calc_refant.get_ref_ant(visname = msvis0, fluxfield = phasefield)
    with open("Log.txt", "a") as file:
        file.write("###################\n")
        file.write("Do Calculate reference antenna step.\n")
        file.write("Set reference antenna: {}; find bad antennas: {}\n".format(refantant,badants))
        file.write("Calculate reference antenna completed\n")

##Set flux model for calibrator
if do_setjy:
    if dopol:
        print('Not going to do polarization for now')
    delmod(vis=msvis0) ##clear the possible previous calibration
    ##Then check if we are using J0408-6545
    mfluxlist = ["J0408-6545", "0408-6545", ""]
    if bpfield in mfluxlist:
        do_manual = True
    else:
        do_manual = False
    if do_manual:
        smodel = [17.066, 0.0, 0.0, 0.0]
        spix = [-1.179]
        reffreq = "1284MHz"
        setjy(vis=msvis0, field=bpfield, scalebychan=True, standard="manual",fluxdensity=smodel,spix=spix,reffreq=reffreq,ismms=domms)
    else:
        setjy(vis=msvis0, field=bpfield, spw=spw_s, scalebychan=True, standard='Stevens-Reynolds 2016',ismms=domms)
    with open("Log.txt", "a") as file:
        file.write("###################\n")
        file.write("Do Flux calibration step.\n")
        file.write("Flux calibration step completed\n")

##First round of cross-cal
if do_crosscal1:
    calprefix1=calprefix+'r1'
    ##Delay calibration: use phasecal field; 
    spwd = '' #all spw
    gaincal(vis=msvis0, caltable = calprefix1+'.delay', field = phasefield,\
        refant = refantant, spw = spwd, minblperant = minbaselines, gaintype = 'K',\
        gaintable = [], gainfield = [], combine = '', solint = 'inf',\
        minsnr = 3, solmode = '', solnorm = False, parang = False, append = False)
    #listcal(vis=msvis0,caltable=calprefix1+'.delay')
    ##Bandpass calibration: 
    spwbp=''
    bandpass(vis=msvis0, caltable = calprefix1+'.bp', field = bpfield,\
        refant = refantant, spw = spwbp, bandtype = 'B', minblperant = minbaselines,\
        fillgaps = 8, gaintable = [calprefix1+'.delay'], gainfield=[phasefield],\
        combine = 'scan', solnorm = False,  solint = 'inf', parang = False, append = False)
#    plotbandpass(caltable=calprefix1+'.bp',spw='',xaxis='freq',yaxis='phase',\
#             subplot=42,markersize=6,interactive=True,plotrange=[0,0,-50,50])
#    plotbandpass(caltable=calprefix1+'.bp',spw='',xaxis='freq',yaxis='amp',\
#                 subplot=42,markersize=6,interactive=True,plotrange=[0,0,0,0])
    ##Gain calibration
    spwg=''
    gaincal(vis=msvis0, caltable = calprefix1+'.gain_ap', field = gainfields,\
        refant = refantant, spw = spwg, minblperant = minbaselines, gaintype = 'G',\
        calmode='ap', solint = 'inf', solnorm = False, combine = '',\
        gaintable=[calprefix1+'.delay', calprefix1+'.bp'],\
        gainfield=[phasefield, bpfield],\
        parang = False, append = False)
    #listcal(vis=msvis0,caltable=calprefix1+'.gain_ap')
    ##flux scale bootstrap
    if len(gainfields.split(',')) > 1:
        fluxscale(vis=msvis0, caltable=calprefix1+'.gain_ap',
            reference=[bpfield], transfer='',
            fluxtable=calprefix1+'.flux', append=False, display=False,
            listfile = calprefix1+'.fluxscale.txt')
        #listcal(vis=msvis0,caltable=calprefix1+'.flux')
    with open("Log.txt", "a") as file:
        file.write("###################\n")
        file.write("Do First round of cross-cal.\n")
        file.write("Complete delay, bandpass, and gain calibration.\n")
        file.write("Delay calibration table: {}\n".format(calprefix1+'.delay'))
        file.write("Bandpass calibration table: {}\n".format(calprefix1+'.bp'))
        file.write("Gain calibration table: {}\n".format(calprefix1+'.gain_ap'))
        file.write("First round of cross-cal completed\n")

####First round of Applycal
if do_applycal1:
    if len(gainfields.split(',')) > 1:
        fluxfile = calprefix1+'.flux'
    else:
        fluxfile = calprefix1+'.gain_ap'
    ##First for bpfield -  not using gaincal result
    applycal(vis=msvis0, field=bpfield, calwt=False, gaintable=[calprefix1+'.delay', calprefix1+'.bp', fluxfile],\
        gainfield=[phasefield, bpfield , bpfield], parang=False, interp='linear,linearflag')
    ##For phasefield
    applycal(vis=msvis0, field=phasefield, calwt=False,\
        gaintable=[calprefix1+'.delay', calprefix1+'.bp',fluxfile],\
        gainfield=[phasefield, bpfield, phasefield], parang=False, interp='linear,linearflag')
    ##For target
    applycal(vis=msvis0, field=tarfield, calwt=False,\
        gaintable=[calprefix1+'.delay', calprefix1+'.bp',fluxfile],\
        gainfield=[phasefield, bpfield, phasefield], parang=False, interp='linear,linearflag')
    with open("Log.txt", "a") as file:
        file.write("###################\n")
        file.write("Do First round of Applycal.\n")
        file.write("Delay calibration table: {}\n".format(calprefix1+'.delay'))
        file.write("Bandpass calibration table: {}\n".format(calprefix1+'.bp'))
        file.write("Gain/bootstrap calibration table: {}\n".format(fluxfile))
        file.write("Apply delay, bandpass, and gain calibration on {}.\n".format(msvis0))
        file.write("First round of Applycal completed\n")

####Flag after first round of calibration
if do_flag2:
    ##Flag with 'tfcrop' algorithm for bpfield and phasecal field --- tight flagging
    flagdata(vis=msvis0, mode='summary', datacolumn='corrected',name='flagr2.before_tfcrop.summary')
    flagdata(vis=msvis0, mode='tfcrop', datacolumn='corrected',\
        field=calfields, ntime="scan", timecutoff=6.0,\
        freqcutoff=5.0, timefit="line", freqfit="line",\
        flagdimension="freqtime", extendflags=False, timedevscale=5.0,\
        freqdevscale=5.0, extendpols=False, growaround=False,\
        action="apply", flagbackup=True, overwrite=True, writeflags=True)
    ##Flag with 'rflag' algorithm for bpfield and phasecal field --- tight flagging
    flagdata(vis=msvis0, mode='summary', datacolumn='corrected',name='flagr2.after_tfcrop.summary')
    flagdata(vis=msvis0, mode="rflag", datacolumn="corrected",\
        field=calfields, timecutoff=5.0, freqcutoff=5.0,\
        timefit="poly", freqfit="line", flagdimension="freqtime",\
        extendflags=False, timedevscale=4.0, freqdevscale=4.0,\
        spectralmax=500.0, extendpols=False, growaround=False,\
        flagneartime=False, flagnearfreq=False, action="apply",\
        flagbackup=True, overwrite=True, writeflags=True)
    ##Extend the flags (70% more means full flag, change if required)
    flagdata(vis=msvis0, mode='summary', datacolumn='corrected',name='flagr2.after_rflag.summary')
    flagdata(vis=msvis0, mode="extend", field=calfields,\
        datacolumn="corrected", clipzeros=True, ntime="scan",\
        extendflags=False, extendpols=False, growtime=90.0, growfreq=90.0,\
        growaround=False, flagneartime=False, flagnearfreq=False,\
        action="apply", flagbackup=True, overwrite=True, writeflags=True)
    flagdata(vis=msvis0, mode='summary', datacolumn='corrected',name='flagr2.after_extend.summary')
    ##For target - moderate flagging, more careful flag can be done in self-cal
    if solar_burst:
        pass
    else:
        flagdata(vis=msvis0, mode="tfcrop", datacolumn="corrected",\
            field=tarfield, ntime="scan", timecutoff=6.0, freqcutoff=5.0,\
            timefit="poly", freqfit="line", flagdimension="freqtime",\
            extendflags=False, timedevscale=5.0, freqdevscale=5.0,\
            extendpols=False, growaround=False, action="apply", flagbackup=True,\
            overwrite=True, writeflags=True)
        flagdata(vis=msvis0, field = tarfield,mode='summary', datacolumn='corrected',name='flagr2.after_tfcrop_tar.summary')

    if solar_burst:
        pass
    else:
        flagdata(vis=msvis0, mode="rflag", datacolumn="corrected",\
            field=tarfield, timecutoff=5.0, freqcutoff=5.0, timefit="poly",\
            freqfit="poly", flagdimension="freqtime", extendflags=False,\
            timedevscale=5.0, freqdevscale=5.0, spectralmax=500.0,\
            extendpols=False, growaround=False, flagneartime=False,\
            flagnearfreq=False, action="apply", flagbackup=True, overwrite=True,\
            writeflags=True)
        flagdata(vis=msvis0, field = tarfield, mode='summary', datacolumn='corrected',name='flagr2.after_rflag_tar.summary')
    ####write log
    with open("Log.txt", "a") as file:
        file.write("###################\n")
        file.write("Do Flag after first round of calibration.\n")
        file.write("Using Flag algorithm tfcrop, rflag, extend on {};\n".format(calfields))
        file.write("Using Flag algorithm tfcrop, rflag on {};\n".format(tarfield))
        file.write("Flag after first round of calibration completed\n")

##Split the calibrated and flagged measurement set
if do_split1:
    msvisr1 = visname.replace('.ms','.calr1.ms')
    split(vis=msvis0, outputvis=msvisr1, datacolumn='corrected')
    ####write log
    with open("Log.txt", "a") as file:
        file.write("###################\n")
        file.write("Do Split the calibrated and flagged measurement set.\n")
        file.write("Splited calibrated round 1 dataset {};\n".format(msvisr1))
        file.write("Split the calibrated and flagged measurement set completed\n")

####Second round of cross-cal
if do_crosscal2:
    calprefix2=calprefix+'r2'
    msvisr1 = visname.replace('.ms','.calr1.ms')
    ##Delay calibration: use phasecal field; 
    spwd = '' #all spw
    gaincal(vis=msvisr1, caltable = calprefix2+'.delay', field = phasefield,\
        refant = refantant, spw = spwd, minblperant = minbaselines, gaintype = 'K',\
        gaintable = [], gainfield = [], combine = '', solint = 'inf',\
        minsnr = 3, solmode = '', solnorm = False, parang = False, append = False)
    #listcal(vis=msvisr1,caltable=calprefix2+'.delay')
    ##Bandpass calibration: 
    spwbp=''
    bandpass(vis=msvisr1, caltable = calprefix2+'.bp', field = bpfield,\
        refant = refantant, spw = spwbp, bandtype = 'B', minblperant = minbaselines,\
        fillgaps = 8, gaintable = [calprefix2+'.delay'], gainfield=[phasefield],\
        combine = 'scan', solnorm = False,  solint = 'inf', parang = False, append = False)
#    plotbandpass(caltable=calprefix2+'.bp',spw='',xaxis='freq',yaxis='phase',\
#             subplot=42,markersize=6,interactive=True,plotrange=[0,0,-50,50])
#    plotbandpass(caltable=calprefix2+'.bp',spw='',xaxis='freq',yaxis='amp',\
#                 subplot=42,markersize=6,interactive=True,plotrange=[0,0,0,0])
    ##Gain calibration
    spwg=''
    gaincal(vis=msvisr1, caltable = calprefix2+'.gain_ap', field = gainfields,\
        refant = refantant, spw = spwg, minblperant = minbaselines, gaintype = 'G',\
        calmode='ap', solint = 'inf', solnorm = False, combine = '',\
        gaintable=[calprefix2+'.delay', calprefix2+'.bp'],\
        gainfield=[phasefield, bpfield],\
        parang = False, append = False)
    #listcal(vis=msvisr1,caltable=calprefix2+'.gain_ap')
    ##flux scale bootstrap
    if len(gainfields.split(',')) > 1:
        fluxscale(vis=msvisr1, caltable=calprefix2+'.gain_ap',
            reference=[bpfield], transfer='',
            fluxtable=calprefix2+'.flux', append=False, display=False,
            listfile = calprefix2+'.fluxscale.txt')
        #listcal(vis=msvisr1,caltable=calprefix2+'.flux')
    with open("Log.txt", "a") as file:
        file.write("###################\n")
        file.write("Do Second round of cross-cal.\n")
        file.write("Complete delay, bandpass, and gain calibration.\n")
        file.write("Delay calibration table: {}\n".format(calprefix2+'.delay'))
        file.write("Bandpass calibration table: {}\n".format(calprefix2+'.bp'))
        file.write("Gain calibration table: {}\n".format(calprefix2+'.gain_ap'))
        file.write("Second round of cross-cal completed\n")

####Second round of Applycal
if do_applycal2:
    if len(gainfields.split(',')) > 1:
        fluxfile = calprefix2+'.flux'
    else:
        fluxfile = calprefix2+'.gain_ap'
    ##First for bpfield
    applycal(vis=msvisr1, field=bpfield, calwt=False, gaintable=[calprefix2+'.delay', calprefix2+'.bp', fluxfile],\
        gainfield=[phasefield, bpfield , bpfield], parang=False, interp='linear,linearflag')
    ##For phasefield
    applycal(vis=msvisr1, field=phasefield, calwt=False,\
        gaintable=[calprefix2+'.delay', calprefix2+'.bp',fluxfile],\
        gainfield=[phasefield, bpfield, phasefield], parang=False, interp='linear,linearflag')
    ##For target
    applycal(vis=msvisr1, field=tarfield, calwt=False,\
        gaintable=[calprefix2+'.delay', calprefix2+'.bp',fluxfile],\
        gainfield=[phasefield, bpfield, phasefield], parang=False, interp='linear,linearflag')
    with open("Log.txt", "a") as file:
        file.write("###################\n")
        file.write("Do Second round of Applycal.\n")
        file.write("Delay calibration table: {}\n".format(calprefix2+'.delay'))
        file.write("Bandpass calibration table: {}\n".format(calprefix2+'.bp'))
        file.write("Gain/bootstrap calibration table: {}\n".format(fluxfile))
        file.write("Apply delay, bandpass, and gain calibration on {}.\n".format(msvisr1))
        file.write("Second round of Applycal completed\n")

##Split the calibrated dataset
if do_split:
    ##Doesn't matter if keep mms, as tclean can handle the common ms in parallel mode
    ##Only split the target scan
    if outputcalvis =='':
        outputcalvis = visname.replace('.ms','.cal.ms')
    split(vis=msvisr1, outputvis=outputcalvis, datacolumn='corrected', field=tarfield, keepflags=True,\
        width=specavg, timebin=timeavg)
    with open("Log.txt", "a") as file:
        file.write("###################\n")
        file.write("Do Split the calibrated dataset.\n")
        file.write("Split the calibrated dataset for target field: {}\n".format(tarfield))
        file.write("Average the channels in : {}\n".format(specavg))
        file.write("Average the time in: {}\n".format(timeavg))
        file.write("Output calibrated data set: {}.\n".format(outputcalvis))
        file.write("Split the calibrated dataset completed\n")

##Make quick look image
if do_qlimg:
    if os.path.exists(workfolder+'qlimg'):
        shutil.rmtree(workfolder+'qlimg')
        os.makedirs(workfolder+'qlimg')
    else:
        os.makedirs(workfolder+'qlimg')
    
    msvis = outputcalvis
    spwql = spw1
    timerangeql = timerange1
    imagenameql = 'qlimg/qlimage'
    ###parameters used as default
    imsizeql = [2048,2048]
    cellql = '2arcsec'
    stokesql = 'I'
    niterql = 2000
    thresholdql = 0
    robustql = 0
    gridderql = 'standard'
    phasecenterql = ''
    outlierfileql = ''
    try:
        tclean(vis=msvis, datacolumn='corrected', imagename=imagenameql,timerange = timerangeql, spw=spwql,\
            imsize=imsizeql, cell=cellql, stokes=stokesql, gridder=gridderql, specmode='mfs',phasecenter = phasecenterql,\
            weighting='briggs', robust = robustql, niter=niterql,\
            threshold=thresholdql, calcpsf=True, outlierfile=outlierfileql,\
            pblimit=0, restoringbeam='', parallel = doparallel)
        print('Image completed')
        with open("Log.txt", "a") as file:
            file.write("###################\n")
            file.write("Do quicklook image.\n")
            file.write("Timeraange: {}\n".format(timerangeql))
            file.write("Frequency range : {}\n".format(spwql))
            file.write("Successfully make quicklook image: {}.\n".format(imagenameql))
            file.write("Quicklook image completed\n")
    except:
        print(imagename+' failed, see log for reason')
        with open("Log.txt", "a") as file:
            file.write("###################\n")
            file.write("Do quicklook image.\n")
            file.write("Quicklook image failed, see logger file for reason")

##Make science image
if do_sciimg:
    if os.path.exists(workfolder+'sciimg'):
        shutil.rmtree(workfolder+'sciimg')
        os.makedirs(workfolder+'sciimg')
    else:
        os.makedirs(workfolder+'sciimg')
    
    msvis = outputcalvis
    spwsci = spw2
    timerangesci = timerange2
    imagenamesci = 'sciimg/sciimg'
    cellsci = cell
    imsizesci = imsize
    stokessci = stokes
    griddersci = gridder
    wprojplanessci = wprojplanes
    deconvolversci = deconvolver
    robustsci = robust
    nitersci = niter
    multiscalesci = multiscale
    thresholdsci = threshold
    ntermssci = nterms
    restoringbeamsci = restoringbeam
    pbthresholdsci = pbthreshold
    ###parameters used as default
    masksci = ''
    outlierfilesci = ''
    rmsmapsci = ''
    phasecentersci = ''
    try:
        tclean(vis=msvis, datacolumn='corrected', imagename=imagenamesci,timerange = timerangesci, spw=spwsci,\
            imsize=imsizesci, cell=cellsci, stokes=stokessci, gridder=griddersci, specmode='mfs',phasecenter = phasecentersci,\
            wprojplanes = wprojplanessci, deconvolver = deconvolversci, restoration=True,\
            weighting='briggs', robust = robustsci, niter=nitersci, scales=multiscalesci,\
            threshold=thresholdsci, nterms=ntermssci, calcpsf=True, mask=masksci, outlierfile=outlierfilesci,\
            pblimit=pbthresholdsci, restoringbeam=restoringbeamsci, parallel = doparallel)
        print('Image completed')
        with open("Log.txt", "a") as file:
            file.write("###################\n")
            file.write("Do science image.\n")
            file.write("Timeraange: {}\n".format(timerangesci))
            file.write("Frequency range : {}\n".format(spwsci))
            file.write("Successfully make science image: {}.\n".format(imagenamesci))
            file.write("Science image completed\n")
    except:
        print(imagename+' failed, see log for reason')
        with open("Log.txt", "a") as file:
            file.write("###################\n")
            file.write("Do science image.\n")
            file.write("Science image failed, see logger file for reason")


##Do primary beam correction
from katbeam import JimBeam
from casatools import image
ia = image()

def do_pb_corr(inpimage, pbthreshold=0, pbband='LBand'):
    """
    Given the input CASA image, outputs a katbeam corrected image, optionally
    cutoff at a specified threshold.

    Inputs:
    inpimage        Input CASA image name, str
    pbthreshold     Cutoff threshold to mask the PB, float
    pbband          Band at which to generate the PB

    Outputs:
    None
    """

    pbcorimage = inpimage.replace('.image', '.katbeam_pbcor.image')
    pbimage = inpimage.replace('.image', '.katbeam.pb')

    ia.open(inpimage)
    csys = ia.coordsys().torecord()
    imgdata = ia.getchunk()
    shape = ia.shape()
    ia.close()

    cx, cy = shape[0]//2, shape[1]//2

    # Size of each pixel
    cdelt = np.abs(csys['direction0']['cdelt'][0])
    unit = csys['direction0']['units'][0]

    if unit == 'rad':
        cdelt = np.rad2deg(cdelt)
    elif unit == "'": #arcmin
        cdelt /= 60.

    # Frequency of image, convert from Hz to MHz
    try:
        freq = csys['spectral1']['wcs']['crval']/1e6
    except KeyError:
        freq = csys['spectral2']['wcs']['crval']/1e6

    if pbband == 'LBand':
        PBeam = JimBeam('MKAT-AA-L-JIM-2020')
    elif pbband == 'SBand':
        PBeam = JimBeam('MKAT-AA-S-JIM-2020')
    elif pbband == 'UHF':
        PBeam = JimBeam('MKAT-AA-UHF-JIM-2020')
    else:
        logger.error('Input pbband not recognized. Must be one of LBand, SBand or UHF. Defaulting to LBand.')
        PBeam = JimBeam('MKAT-AA-L-JIM-2020')

    x = np.linspace(-cx, cx+1, shape[0])
    y = np.linspace(-cy, cy+1, shape[1])

    xx, yy = np.meshgrid(x, y)

    # Convert pixels into separation in degrees
    xx *= cdelt
    yy *= cdelt

    # Generate the 2D PB image
    beam_I = PBeam.I(xx, yy, freq)

    # Match shape with image data for PB correction
    if len(shape) == 4:
        beam_I = beam_I[:, :, None, None]

    pbcor_imgdata = imgdata/beam_I

    # Mask below the threshold
    if pbthreshold > 0:
        pbcor_imgdata[beam_I < pbthreshold] = np.nan
        #beam_I[beam_I < pbthreshold] = np.nan

    shutil.copytree(inpimage, pbimage)
    ia.open(pbimage)
    ia.putchunk(beam_I)
    ia.close()

    shutil.copytree(inpimage, pbcorimage)
    ia.open(pbcorimage)
    ia.putchunk(pbcor_imgdata)
    ia.close()

if dopb_cor:
    imagenamesci = 'sciimg/sciimg'
    if deconvolver == 'mtmfs':
        imagefile = imagenamesci + '.image.tt0'
    else:
        imagefile = imagenamesci + '.image'
    try:
        do_pb_corr(imagefile, pbthreshold, pbband)
        print('primary beam correctted image : {}'.format(imagefile.replace('.image', '.katbeam_pbcor.image')))
        with open("Log.txt", "a") as file:
            file.write("###################\n")
            file.write("Do Primary Beam correction.\n")
            file.write("primary beam correctted image : {}.\n".format(imagefile.replace('.image', '.katbeam_pbcor.image')))
            file.write("Primary Beam correction completed\n")
    except:
        print('primary beam correctted failed')
        with open("Log.txt", "a") as file:
            file.write("###################\n")
            file.write("Primary Beam correction failed\n")

end_time = time.time()
total_minutes = (end_time - start_time) / 60
with open("Log.txt", "a") as file:
    file.write("###################\n")
    file.write(f"All tasks completed in {total_minutes:.2f} minutes.\n")
print(f"All tasks completed in {total_minutes:.2f} minutes.")











