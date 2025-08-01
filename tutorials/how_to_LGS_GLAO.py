# -*- coding: utf-8 -*-
"""
Created on Wed Apr 27 10:46:24 2022

@author: cheritie
"""
# commom modules
import matplotlib.pyplot as plt
import numpy             as np 
from OOPAO.Atmosphere       import Atmosphere
from OOPAO.DeformableMirror import DeformableMirror
from OOPAO.MisRegistration  import MisRegistration
from OOPAO.Telescope        import Telescope
from OOPAO.Source           import Source
# calibration modules 
from OOPAO.calibration.compute_KL_modal_basis import compute_M2C
from OOPAO.calibration.ao_calibration import ao_calibration
# display modules
from OOPAO.tools.displayTools           import displayMap

# %%
plt.ion()
# number of subaperture for the WFS
n_subaperture = 20


#%% -----------------------     TELESCOPE   ----------------------------------
from OOPAO.Telescope import Telescope

# create the Telescope object
tel = Telescope(resolution           = 8*n_subaperture,                          # resolution of the telescope in [pix]
                diameter             = 8,                                        # diameter in [m]        
                samplingTime         = 1/1000,                                   # Sampling time in [s] of the AO loop
                centralObstruction   = 0.1,                                      # Central obstruction in [%] of a diameter 
                display_optical_path = False,                                    # Flag to display optical path
                fov                  = 40 )                                     # field of view in [arcsec]. If set to 0 (default) this speeds up the computation of the phase screens but is uncompatible with off-axis targets


#%% -----------------------     NGS   ----------------------------------
# create the Source object
ngs=Source(optBand   = 'I',\
           magnitude = 5,)
    
    
#%% -----------------------     LGS   ----------------------------------
n_lgs = 4
# angular position of the LLT and of the asterism on sky
theta = np.linspace(0,360, n_lgs,endpoint=False) #deg
# zenith radius fot the asterism
zenith = 20 # arcsec
# fwhm of the LGS spots up
fwhm_spot = 1.5 # arcsec

# Na Profile
n = 11 # sampling of the Na Profile
Na_profile = np.zeros([2,n])
Na_profile[0,:] = np.linspace(80000,100000,n) # altitude in m of the Na layer
Na_profile[1,:] = 1/n # Na density profile, here considered to be uniform


# list of sources to be considered
list_source = []
# first source is the NGS
# list_source.append(ngs)
# the rest are LGS sources
for i_theta in theta:
    lgs = Source(optBand   ='Na',\
           magnitude = 0,
           laser_coordinates=[np.cos(np.deg2rad(i_theta))*tel.D/2,np.sin(np.deg2rad(i_theta))*tel.D/2], 
           Na_profile=Na_profile,
           FWHM_spot_up= fwhm_spot,
           coordinates = [zenith,i_theta])
    list_source.append(lgs)

# create the Asterism object from the list of sources:
    
from OOPAO.Asterism import Asterism
ast = Asterism(list_src=list_source)

# This only works after ast*atm
# ast*tel

# display the asterism geometry
ast.display_asterism()


#%% -----------------------     ATMOSPHERE   ----------------------------------

# create the Atmosphere object
atm=Atmosphere(telescope     = tel,
               r0            = 0.15,
               L0            = 25,
               windSpeed     = [10,20],
               fractionalR0  = [0.75,0.25], # to test the GLAO like config, try to set to [1,0]
               windDirection = [0,90],
               altitude      = [0,10000])# initialize atmosphere
atm.initializeAtmosphere(tel)


ast**atm*tel

# This is still not working well before the first propagation because the atm has no sources
atm.display_atm_layers()

#%% -----------------------     DEFORMABLE MIRROR   ----------------------------------
# mis-registrations object
misReg = MisRegistration()
# if no coordinates specified, create a cartesian dm
dm=DeformableMirror(telescope    = tel,\
                    nSubap       = n_subaperture,\
                    mechCoupling = 0.45,\
                    misReg       = misReg)

#%%

# Same DM in altitude (illustration of )
dm_altitude=DeformableMirror(telescope    = tel,\
                    nSubap       = n_subaperture,\
                    mechCoupling = 0.45,\
                    misReg       = misReg,
                    altitude=10000)# in m

#%% -----------------------     SH WFS   ----------------------------------

from OOPAO.ShackHartmann import ShackHartmann

plt.close('all')

wfs_ngs = ShackHartmann(2, tel, lightRatio=0.1,shannon_sampling=True) # 2x2 NGS WFS

wfs_lgs = ShackHartmann(n_subaperture, tel, lightRatio=0.1,pixel_scale=1.5) #  LGS WFS

# geometric SH for the calibration
wfs_geo = ShackHartmann(n_subaperture, tel, lightRatio=0.1,pixel_scale=1.5,is_geometric=True) #  LGS WFS


#%% Propagation and interaction with OOPAO objects
plt.close('all')

# poking on both DM to show the optical propagation
poke = np.zeros(dm_altitude.nValidAct)
poke[140] = 3e-6
dm_altitude.coefs = poke

poke = np.zeros(dm.nValidAct)
poke[140] = 3e-6
dm.coefs = -poke

# propagating through the whole system
ast**atm*tel*dm*dm_altitude*wfs_lgs
ngs**atm*tel*dm*dm_altitude*wfs_ngs

# plt.figure(10)

plt.figure(10, figsize=(30, 20))


count = 0

count+=1

plt.subplot(4, len(ast.src)+1, count)
plt.imshow(ngs.OPD)
plt.title(f'OPD {str(count)} seen by WFS NGS')

plt.subplot(4, len(ast.src)+1, count + (len(ast.src)+1))
plt.imshow(wfs_ngs.signal_2D[0])
plt.title(f'Signal# {str(count)} from WFS NGS')

plt.subplot(4, len(ast.src)+1, count + (len(ast.src)+1) * 2)
plt.imshow(wfs_ngs.frames[0])
plt.title(f'Detector# {str(count)} from WFS')



for i_src in range(len(ast.src)):
    count+=1
    plt.figure(10, figsize=(30, 20))

    plt.subplot(4,(len(ast.src)+1),count)
    plt.imshow(ast.OPD[i_src])
    plt.title(f'OPD# {str(count)} seen by WFS')

    plt.subplot(4, len(ast.src)+1, count + (len(ast.src)+1))
    plt.imshow(wfs_lgs.signal_2D[i_src])
    plt.title(f'Signal# {str(count)} from WFS')

    plt.subplot(4,len(ast.src)+1,count+(len(ast.src)+1)*2)
    plt.imshow(wfs_lgs.frames[i_src])
    plt.title(f'Detector# {str(count)} from WFS')


plt.subplot(4,len(ast.src)+1,count+2+(len(ast.src)+1)*2)
plt.imshow(dm.OPD,extent=[-dm.D/2,dm.D/2,-dm.D/2,dm.D/2])
plt.title('OPD DM@0 m')
plt.xlabel('[m]')
plt.ylabel('[m]')

plt.subplot(4,len(ast.src)+1,count+3+(len(ast.src)+1)*2)
plt.imshow(dm_altitude.OPD,extent=[-dm_altitude.D/2,dm_altitude.D/2,-dm_altitude.D/2,dm_altitude.D/2])
plt.title('OPD Altitude DM@'+str(dm_altitude.altitude)+'m')
plt.xlabel('[m]')
plt.ylabel('[m]')



#%% Modal Basis:
ngs**tel
from OOPAO.calibration.compute_KL_modal_basis import compute_KL_basis
# use the default definition of the KL modes with forced Tip and Tilt. For more complex KL modes, consider the use of the compute_KL_basis function. 
M2C_KL = compute_KL_basis(ngs,tel,atm,dm,lim = 1e-2) # matrix to apply modes on the DM

# apply the 10 first KL modes
dm.coefs = M2C_KL[:,:10]
# propagate through the DM
ngs**tel*dm
# show the first 10 KL modes applied on the DM
displayMap(ngs.OPD)

#%% Calibration
from OOPAO.calibration.InteractionMatrix import InteractionMatrix

# amplitude of the modes in m
stroke=1e-9
# zonal Interaction Matrix
M2C_zonal = np.eye(dm.nValidAct)

# modal Interaction Matrix for 300 modes
M2C_modal = M2C_KL[:,:300]

# zonal interaction matrix
calib_HO = InteractionMatrix(ngs            = ngs,
                                atm            = atm,
                                tel            = tel,
                                dm             = dm,
                                wfs            = wfs_geo,   
                                M2C            = M2C_modal, # M2C matrix used 
                                stroke         = stroke,    # stroke for the push/pull in M2C units
                                nMeasurements  = 12,        # number of simultaneous measurements
                                noise          = 'off',     # disable wfs.cam noise 
                                display        = True,      # display the time using tqdm
                                single_pass    = True)      # only push to compute the interaction matrix instead of push-pull

wfs_ngs.is_geometric=True
# zonal interaction matrix
calib_LO = InteractionMatrix(ngs            = ngs,
                                atm            = atm,
                                tel            = tel,
                                dm             = dm,
                                wfs            = wfs_ngs,
                                M2C            = M2C_modal[:,:2], # M2C matrix used 
                                stroke         = stroke,    # stroke for the push/pull in M2C units
                                nMeasurements  = 12,        # number of simultaneous measurements
                                noise          = 'off',     # disable wfs.cam noise 
                                display        = True,      # display the time using tqdm
                                single_pass    = True)      # only push to compute the interaction matrix instead of push-pull

wfs_ngs.is_geometric=False


#%% setup of the Weighted cOg for the NGS WFS based on the atmosphere properties

# tel+atm
# typical spot size from atmosphere: 
r0_ngs_wvl, seeing_ngs_wvl = atm.print_atm_at_wavelength(ast.src[0].wavelength)

wfs_ngs.set_weighted_centroiding_map(is_lgs=False,is_gaussian=True,fwhm_factor=5)

ast**atm*tel*wfs_lgs
ngs**atm*tel*wfs_ngs

plt.figure()
plt.subplot(1,2,1)
plt.imshow(wfs_ngs.merge_data_cube(wfs_ngs.weighting_map))
plt.subplot(1,2,2)
plt.imshow(wfs_ngs.cam.frame)


#%% setup of the Weighted cOg for the LGS WFS based on the LGS elongation profile
for i_src in range(len(ast.src)):
    wfs_lgs.set_weighted_centroiding_map(is_lgs=True,
                                       is_gaussian=True,
                                       fwhm_factor=1.2) # use assymetric gaussian maps with a FWHM twice larger than the FWHM of the LGS spots in each direction
    plt.figure()
    plt.subplot(1,2,1)
    plt.imshow(wfs_lgs.merge_data_cube(wfs_lgs.weighting_map))
    plt.subplot(1,2,2)
    plt.imshow(wfs_lgs.frames[0])



#%% calibrate the LGS WFS gains due to the spot elongation and potential wCog

ast**tel*wfs_lgs
wfs_lgs.slopes_units = 1

for i in range(1):
    dm.coefs = M2C_KL[:, 0] * 1e-9
    ast ** tel * dm * wfs_lgs
    signal_ngs_wfs = wfs_lgs.signal
    signal_lgs_wfs = np.vstack(wfs_lgs.signal)
    rec = (calib_HO.M @ np.mean(signal_lgs_wfs, axis=0))[0]

    wfs_lgs.slopes_units = rec / 1e-9





#%% Define instrument and WFS path detectors
from OOPAO.Detector import Detector
import time
from OOPAO.tools.displayTools import cl_plot

src=Source(optBand   = 'K',\
           magnitude = 4,)
src**atm*tel
# instrument path
src_cam = Detector(tel.resolution)
src_cam.psf_sampling = 4
src_cam.integrationTime = tel.samplingTime*10

# initialize Telescope DM commands
src.resetOPD()
dm.coefs=0

# Update the r0 parameter, generate a new phase screen for the atmosphere and combine it with the Telescope
atm.generateNewPhaseScreen(seed = 10)

ast**atm*tel*wfs_lgs

plt.close('all')

nLoop = 500
# allocate memory to save data
SR_NGS                      = np.zeros(nLoop)
SR_SRC                      = np.zeros(nLoop)
total                       = np.zeros(nLoop)
residual_SRC                = np.zeros(nLoop)
residual_NGS                = np.zeros(nLoop)

wfsSignal_LO               = np.arange(0,wfs_ngs.nSignal)*0
wfsSignal_HO               = np.arange(0,wfs_geo.nSignal)*0

src**atm*tel

tel.computePSF()

plot_obj = cl_plot(list_fig          = [atm.OPD,
                                        src.OPD,
                                        [[0,0],[0,0]],
                                        np.log10(tel.PSF),
                                        dm.OPD,
                                        wfs_ngs.frames[0],
                                        wfs_lgs.frames[0],
                                        wfs_lgs.frames[1],
                                        wfs_lgs.frames[2],
                                        wfs_lgs.frames[3]],
                    type_fig          = ['imshow',
                                        'imshow',
                                        'plot',
                                        'imshow',
                                        'imshow',
                                        'imshow',
                                        'imshow',
                                        'imshow',
                                        'imshow',
                                        'imshow'],
                    list_title        = ['Turbulence [nm]',
                                        'SRC residual [m]',
                                         'WFE',
                                         'SRC PSF',
                                         'DM OPD',
                                         None,
                                         None,
                                         None,
                                         None,
                                         None],
                    list_legend       = [None,
                                         None,
                                         None,
                                         ['SRC@'+str(src.coordinates[0])+'"'],
                                         None,
                                         None,
                                         None,
                                         None,
                                         None,
                                         None],
                    list_label        = [None,
                                         None,
                                         ['Loop Iteration','WFE'],
                                         None,
                                         None,
                                         ['NGS WFS',''],
                                         ['LGS WFS 1',''],
                                         ['LGS WFS 2',''],
                                         ['LGS WFS 3',''],
                                         ['LGS WFS 4','']],
                    n_subplot         = [5,2],
                    list_display_axis = [None,
                                         None,
                                         True,
                                         None,
                                         None,
                                         None,
                                         None,
                                         None,
                                         None,
                                         None],
                    list_ratio        = [[0.95,0.95,0.1],[0.95,0.95,0.95,0.95,0.95]], s=20)

#
# loop parameters
gainCL                  = 0.4
display                 = True
frame_delay             = 2
display = True
for i in range(nLoop):
    a=time.time()
    # update phase screens => overwrite tel.OPD and consequently tel.src.phase
    atm.update()

    src**atm*tel

    # save phase variance
    total[i]=np.std(src.OPD[np.where(tel.pupil>0)])*1e9

    # propagate light from the SRC through the atmosphere, telescope, DM to the Instrument camera
    ast**atm*tel*dm*wfs_lgs
    ngs**atm*tel*dm*wfs_ngs
    signal_ngs_wfs = wfs_ngs.signal[0]
    signal_lgs_wfs = np.vstack(wfs_lgs.signal)
    
    src**atm*tel*dm*src_cam
    OPD_SRC = src.OPD.copy()
    # save residuals corresponding to the NGS
    residual_SRC[i] = np.std(src.OPD[np.where(tel.pupil>0)])*1e9
    if frame_delay ==1:        
        wfsSignal_HO=np.mean(signal_lgs_wfs,axis=0) # GLAO like 
        wfsSignal_LO=signal_ngs_wfs 

    modes_LGS = calib_HO.M@wfsSignal_HO
    modes_LO = calib_LO.M@wfsSignal_LO
    modes_LGS[:2] = modes_LO
    
    
    # apply the commands on the DM
    dm.coefs=dm.coefs-gainCL*np.matmul(M2C_KL,modes_LGS)
    
    # store the slopes after computing the commands => 2 frames delay
    if frame_delay ==2:        
        wfsSignal_HO=np.mean(signal_lgs_wfs,axis=0) # GLAO like 
        wfsSignal_LO=signal_ngs_wfs # GLAO like 
    
    print('Elapsed time: ' + str(time.time()-a) +' s')
    
    # update displays if required
    if display==True and i>1:        
        SRC_PSF = np.log10(np.abs(src_cam.frame))
        # update range for PSF images
        plot_obj.list_lim = [None,None,None,[SRC_PSF.max()-6, SRC_PSF.max()],None,None,None,None,None,None]        
        # update title
        plot_obj.list_title = ['Turbulence '+str(np.round(total[i]))+'[nm]',
                                'SRC residual '+str(np.round(residual_SRC[i]))+'[nm]',
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                                None,
                                None]

        cl_plot(list_fig   = [1e9*atm.OPD,
                              1e9*OPD_SRC,
                              [np.arange(i+1),residual_SRC[:i+1]],
                              SRC_PSF,                                       
                              dm.OPD,
                              wfs_ngs.frames[0],
                              wfs_lgs.frames[0],
                              wfs_lgs.frames[1],
                              wfs_lgs.frames[2],
                              wfs_lgs.frames[3]],
                                plt_obj = plot_obj)
        plt.draw()
        plt.pause(0.01)
        if plot_obj.keep_going is False:
            break
    print('Loop'+str(i)+'/'+str(nLoop)+' -- SRC WFE :' +str(residual_SRC[i])+' - SRC SR '+str(np.exp(-np.var(src.phase[np.where(tel.pupil==1)]))) +'\n')