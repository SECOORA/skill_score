# -*- coding: utf-8 -*-
#
# load_secoora_models.py
#
# purpose:  Compare with "load_secoora_models.m"
# author:   Filipe P. A. Fernandes
# e-mail:   ocefpaf@gmail
# web:      http://ocefpaf.github.io/
# created:  14-May-2014
# modified: Wed 14 May 2014 10:32:04 AM BRT
#
# obs: https://github.com/nctoolbox/nctoolbox/blob/master/demos/contrib
#


import iris
import numpy as np
import numpy.ma as ma
import seawater as sw
import matplotlib.pyplot as plt

variable = 'temp'  # 'salt'.
obs = dict()


# Will use dynamic field names with structures to process variable named above.

# Obs: Single glider transect.
if False:
    uri = 'http://tds.marine.rutgers.edu/thredds/dodsC/cool/glider/mab/Gridded'
    obs['url'] = '%s/20101025T000000_20101117T000000_marcoos_ru22.nc' % uri
    obs['url'] = '%s/20100402T000000_20100511T000000_cara_ru26d.nc' % uri
    obs['url'] = '%s/20130813T000000_20130826T000000_njdep_ru28.nc' % uri

uri = 'http://tds.marine.rutgers.edu:8080/thredds/dodsC/cool/glider/mab/Gridded'
obs['url'] = '%s/20130911T000000_20130920T000000_gp2013_modena.nc' % uri
obs['file'] = obs['url']
obs['temp'] = dict(name='temperature')
obs['salt'] = dict(name='salinity')
obs['lonname'] = 'longitude'
obs['latname'] = 'latitude'
obs['zname']  = 'depth'

cubes = iris.load(obs['url'])

# Load the observations.
print(nc)
print('Loading obs from "%s"' % obs['url'])
print('  Variable is %s' % obs[variable]['name'])

for cube in nc:
    if cube.name().lower() == obs[variable]['name']:
        obs['data'] = cube.data
        obs['z'] = cube.coord(obs['zname']).points
        obs['time'] = time_coord.units.num2date(time_coord.points)
        time_coord = cube.coord(axis='T')
    elif cube.name().lower() == obs['lonname']:
        obs['lon']  = cube.data
    elif cube.name().lower() == obs['latname']:
        obs['lat']  = cube.data

obs['dist'] = np.cumsum(np.r_[0, sw.dist(obs['lat'], obs['lon'], units='km')[0]])
obs[variable]['data'] = obs['data']
obs[variable]['dist'] = obs['dist']
obs[variable]['z'] = obs['z']

tstart = min(obs['time'])
tend = max(obs['time'])
print('  Time interval of obs:')
print('    %s to %s' % (tstart, tend))


# Model: Global NCOM CF-compliant aggregation.
ncom = dict()
ncom['name'] = 'global_ncom'
uri = 'http://ecowatch.ncddc.noaa.gov/thredds/dodsC/ncom/ncom_reg1_agg'
ncom['url'] = '%s/NCOM_Region_1_Aggregation_best.ncd' % uri
ncom['file'] = 'ncom.nc'
ncom['temp'] = dict(name='water_temp')
ncom['salt'] = dict(name='salinity')


# Model: US-EAST (NCOM) CF-compliant aggregation.
useast = dict()
useast['name'] = 'useast'
uri = 'http://ecowatch.ncddc.noaa.gov/thredds/dodsC/ncom_us_east_agg'
useast['url'] = '%s/US_East_Apr_05_2013_to_Current_best.ncd' % uri
useast['file'] = 'useast.nc'
useast['temp'] = dict(name='water_temp')
useast['salt'] = dict(name='salinity')


# Model: MERCATOR CF-compliant nc file extracted at myocean.eu.
# Registration and user/password authentication required.
mercator = dict()
mercator['name'] = 'mercator'
mercator['url'] = 'dataset-psy2v4-pgs-nat-myocean-bestestimate_1295878772263.nc'
mercator['file'] = mercator['url']
mercator['temp'] = dict(name='temperature')
mercator['salt'] = dict(name='salinity')


# Model: COAWST CF-compliant ROMS aggregation.
coawst = dict()
coawst['name'] = 'coawst'
uri = 'http://geoport.whoi.edu/thredds/dodsC'
if tend <= datetime(2012, 6, 25):
    coawst['u# FIXME:rl'] = '%s/coawst_2_2/fmrc/coawst_2_2_best.ncd' % uri
else:
    coawst['url'] = '%s/coawst_4/use/fmrc/coawst_4_use_best.ncd' % uri

coawst['file'] = 'coawst.nc'
coawst['temp'] = dict(name='temp')
coawst['salt'] = dict(name='salt')


# Model: ESPreSSO CF-compliant ROMS aggregation.
espresso = dict()
espresso['name'] = 'espresso'
uri = 'http://tds.marine.rutgers.edu:8080/thredds/dodsC'
espresso['url'] = '%s/roms/espresso/2009_da/his' % uri
espresso['file'] = 'espresso.nc'
espresso['temp'] = dict(name='temp')
espresso['salt'] = dict(name='salt')


# Model: SABGOM CF-compliant ROMS aggregation.
sabgom = dict()
sabgom['name'] = 'sabgom'
uri = 'http://omgsrv1.meas.ncsu.edu:8080/thredds/dodsC/fmrc/sabgom'
sabgom['url'] = '%s/SABGOM_Forecast_Model_Run_Collection_best.ncd' % uri
sabgom['file'] = 'sabgom.nc'
sabgom['temp'] = dict(name='temp')
sabgom['salt'] = dict(name='salt')


# Model: AMSEAS CF-compliant NCOM aggregation
amseas = dict()
amseas['name'] = 'amseas'
uri = 'http://edac-dap3.northerngulfinstitute.org/thredds/dodsC'
amseas['url'] = '%s/ncom_amseas_agg/AmSeas_Aggregation_best.ncd' % uri
amseas['file'] = 'amseas.nc'
amseas['temp'] = dict(name='water_temp')
amseas['salt'] = dict(name='salinity')


# Model: Global HYCOM RTOFS (HYCOM) Region 1.
hycom = dict()
hycom['name'] = 'hycom'
uri = 'http://ecowatch.ncddc.noaa.gov/thredds/dodsC/hycom/hycom_reg1_agg'
hycom['url'] = '%s/HYCOM_Region_1_Aggregation_best.ncd' % uri
hycom['file'] = 'hycom.nc'
hycom['temp'] = dict(name='water_temp')
hycom['salt'] = dict(name='salinity')

# Models to compare with data.
# model_list = {'USEAST', 'ESPreSSO', 'HYCOM'}  # MARACOOS.
model_list = ['USEAST', 'SABGOM', 'HYCOM']  # SECOORA.


ncks = False
for m = 1:length(model_list)
    mname = char(model_list{m})

    # Work with a temporary structure named 'model'.
    # FIXME:
    eval(['model = ' lower(mname)])

    if ncks:
        string = nc_genslice(model['url'], model[variable]['name'],
                             obs['lon'], obs['lat'], obs['time'], 'ncks')
        print(['%s  %s.nc' % (string, model['name']))

    # TODO: Develop `nc_genslice` using iris!
    Tvar, Tdis, Tzed = nc_genslice(model['url'], model[variable]['name'],
                                   obs['lon'], obs['lat'], obs['time'],
                                   'verbose')

    if ~isempty(findstr(model['url'], 'myocean')) && strcmp(variable, 'temp')
        # FIXME: cube.convert_units('celsius')
        Tvar = Tvar - 272.15

    model[variable]['data'] = Tvar
    model[variable]['dist'] = Tdis
    model[variable]['z'] = Tzed

    # Copy 'model' back to the original named strucutre for this model.
    # FIXME:
    eval([model.name ' = model'])


#save secoora_models.mat
