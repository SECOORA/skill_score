#!/usr/bin/env python

# conda execute
# env:
#   - iris ==1.9.2
#   - mpld3 ==0.2
#   - pyoos ==0.7.0
#   - pyyaml ==3.11
#   - folium ==0.2.1
#   - seaborn ==0.7.0
#   - geojson ==1.3.2
#   - oceans ==0.2.5
#   - mplleaflet ==0.0.5
#   - scikit-learn ==0.17.1
# channels:
#    - conda-forge
# run_with: python

"""
Fetch time-series data from the sea surface.

This notebook fetches weekly time-series of all the SECOORA observations and
models available in the **NGDC** and **SECOORA THREDDS** catalogs.

call: 00-fetch_data.py sss/config.yaml

"""

import os
import sys
import time
from datetime import datetime, timedelta

import iris
import pandas as pd

start_time = time.time()

iris.FUTURE.netcdf_promote = True
iris.FUTURE.netcdf_no_unlimited = True
iris.FUTURE.cell_datetime_objects = True


# Setup.
def start_log(save_dir):
    import shutil
    import logging as log
    if os.path.exists(save_dir):
        shutil.rmtree(save_dir)
    os.makedirs(save_dir)

    log.captureWarnings(True)
    LOG_FILENAME = 'log.txt'
    LOG_FILENAME = os.path.join(save_dir, LOG_FILENAME)
    formatter = '%(asctime)s %(levelname)s: %(message)s'
    log.basicConfig(filename=LOG_FILENAME,
                    filemode='w',
                    format=formatter,
                    datefmt='%I:%M:%S',
                    level=log.INFO,
                    stream=None)

    # Writes log.INFO messages (or higher) to the sys.stderr.
    console = log.StreamHandler()
    console.setLevel(log.INFO)
    formatter = log.Formatter(formatter)
    console.setFormatter(formatter)
    log.getLogger('').addHandler(console)
    return log


from pytools.ioos import parse_config

config_file = os.path.abspath(sys.argv[1])
config = parse_config(config_file)

save_dir = os.path.join(os.path.abspath(os.path.dirname(config_file)),
                        config['run_name'])

log = start_log(save_dir)
fmt = '{:*^64}'.format
log.info(fmt('Saving data inside directory {}'.format(save_dir)))
log.info(fmt(' Run information '))
log.info('Run date: {:%Y-%m-%d %H:%M:%S}'.format(datetime.utcnow()))
log.info('Start: {:%Y-%m-%d %H:%M:%S}'.format(config['date']['start']))
log.info('Stop: {:%Y-%m-%d %H:%M:%S}'.format(config['date']['stop']))
log.info('Bounding box: {0:3.2f}, {1:3.2f},'
         '{2:3.2f}, {3:3.2f}'.format(*config['region']['bbox']))


# CSW search.
def make_filter(config):
    from owslib import fes
    from pytools.ioos import fes_date_filter
    kw = dict(wildCard='*', escapeChar='\\',
              singleChar='?', propertyname='apiso:AnyText')

    or_filt = fes.Or([fes.PropertyIsLike(literal=('*%s*' % val), **kw)
                      for val in config['cf_names']])

    # Exclude ROMS Averages and History files.
    not_filt = fes.Not([fes.PropertyIsLike(literal='*Averages*', **kw)])

    begin, end = fes_date_filter(config['date']['start'],
                                 config['date']['stop'])
    bbox_crs = fes.BBox(config['region']['bbox'],
                        crs=config['region']['crs'])
    return [fes.And([bbox_crs, begin, end, or_filt, not_filt])]

filter_list = make_filter(config)

from pytools.ioos import service_urls
from owslib.csw import CatalogueServiceWeb

log.info(fmt(' Catalog information '))
log.info(fmt(' CSW '))

# http://data.ioos.us/csw is too old and does not support CRS.
endpoints = ['http://www.ngdc.noaa.gov/geoportal/csw',
             'http://geoport.whoi.edu/csw']

# For the all strings see:
# https://raw.githubusercontent.com/OSGeo/Cat-Interop/master/LinkPropertyLookupTable.csv
opendap = ['OPeNDAP:OPeNDAP',
           'urn:x-esri:specification:ServiceType:odp:url']
sos = ['urn:x-esri:specification:ServiceType:sos:url']

dap_urls = []
sos_urls = []
for endpoint in endpoints:
    log.info("URL: {}".format(endpoint))

    csw = CatalogueServiceWeb(endpoint, timeout=60)
    csw.getrecords2(constraints=filter_list, maxrecords=1000, esn='full')
    dap_urls.extend(service_urls(csw.records, services=opendap))
    sos_urls.extend(service_urls(csw.records, services=sos))

    log.info("CSW version: {}".format(csw.version))
    log.info("Datasets available: {}".format(len(csw.records.keys())))

    for rec, item in csw.records.items():
        log.info('{}'.format(item.title))
    log.info(fmt(' SOS '))
    for url in sos_urls:
        log.info('{}'.format(url))
    log.info(fmt(' DAP '))
    for url in dap_urls:
        log.info('{}.html'.format(url))

# Get only unique endpoints.
dap_urls = list(set(dap_urls))
sos_urls = list(set(sos_urls))


from pytools.ioos import is_station

# Filter out some observations (stations) endpoints from the models list.
non_stations = []
for url in dap_urls:
    try:
        if not is_station(url):
            non_stations.append(url)
    except RuntimeError as e:
        log.warn("Could not access URL {}. {!r}".format(url, e))

dap_urls = non_stations

log.info(fmt(' Filtered DAP '))
for url in dap_urls:
    log.info('{}.html'.format(url))


# Add SECOORA models and observations.
for secoora_model in config['secoora_models']:
    if config['models_urls'][secoora_model] not in dap_urls:
        log.warning('{} not in the catalog csw'.format(secoora_model))
        dap_urls.append(config['models_urls'][secoora_model])


def fix_url(start, url):
    """
    NOTE: USEAST is not archived at the moment!
    See: https://github.com/ioos/secoora/issues/173
    """
    import pytz
    diff = (datetime.utcnow().replace(tzinfo=pytz.utc)) - start
    if diff > timedelta(days=30):
        url = url.replace('omgsrv1', 'omgarch1')
    return url


dap_urls = [fix_url(config['date']['start'], url) if
            'SABGOM' in url else url for url in dap_urls]


from iris.exceptions import CoordinateNotFoundError, ConstraintMismatchError

from pytools.ioos import TimeoutException, url_lister
from pytools.tardis import quick_load_cubes, proc_cube


def secoora_buoys():
    thredds = "http://129.252.139.124/thredds/catalog_platforms.html"
    urls = url_lister(thredds)
    base_url = "http://129.252.139.124/thredds/dodsC"
    for buoy in urls:
        if (("?dataset=" in buoy) and
           ('archive' not in buoy) and
           ('usf.c12.weatherpak' not in buoy) and
           ('cormp.ocp1.buoy' not in buoy)):
            try:
                buoy = buoy.split('id_')[1]
            except IndexError:
                buoy = buoy.split('=')[1]
            if buoy.endswith('.nc'):
                buoy = buoy[:-3]
            url = '{}/{}.nc'.format(base_url, buoy)
            yield url

urls = list(secoora_buoys())
buoys = dict()
if not urls:
    raise ValueError("Did not find any SECOORA buoys!")

for url in urls:
    try:
        kw = dict(bbox=config['region']['bbox'],
                  time=(config['date']['start'], config['date']['stop']),
                  units=config['units'])
        cubes = quick_load_cubes(url, config['cf_names'])
        cubes = [proc_cube(cube, **kw) for cube in cubes]
        buoy = url.split('/')[-1].split('.nc')[0]
        if len(cubes) == 1:
            buoys.update({buoy: cubes[0]})
        else:
            # [buoys.update({'{}_{}'.format(buoy, k): cube}) for
            # k, cube in list(enumerate(cubes))]
            # FIXME: For now I am choosing the first sensor.
            buoys.update({buoy: cubes[0]})
    except (IOError, RuntimeError, ValueError, TimeoutException,
            ConstraintMismatchError, CoordinateNotFoundError) as e:
        log.warning('Cannot get cube for: {}\n{}'.format(url, e))


# Collect observations.
from pyoos.collectors.coops.coops_sos import CoopsSos

collector = CoopsSos()

collector.end_time = config['date']['stop']
collector.start_time = config['date']['start']
collector.variables = [config['sos_name']]

ofrs = collector.server.offerings
title = collector.server.identification.title
log.info(fmt(' Collector offerings '))
log.info('{}: {} offerings'.format(title, len(ofrs)))

from pandas import read_csv
from pytools.ioos import sos_request

params = dict(
    observedProperty=config['sos_name'],
    eventTime=config['date']['start'].strftime('%Y-%m-%dT%H:%M:%SZ'),
    featureOfInterest='BBOX:{0},{1},{2},{3}'.format(*config['region']['bbox']),
    offering='urn:ioos:network:NOAA.NOS.CO-OPS:MetActive'
)

uri = 'http://opendap.co-ops.nos.noaa.gov/ioos-dif-sos/SOS'
url = sos_request(uri, **params)
observations = read_csv(url)

log.info('SOS URL request: {}'.format(url))


# Clean the DataFrame.
from pytools.ioos import get_coops_metadata

col = dict(salinity='sea_water_salinity (psu)',
           sea_water_temperature='sea_water_temperature (C)',
           water_surface_height_above_reference_datum='water_surface_height_above_reference_datum (m)',  # noqa
           )

columns = {'sensor_id': 'sensor',
           'station_id': 'station',
           'latitude (degree)': 'lat',
           'longitude (degree)': 'lon',
           col[config['sos_name']]: config['sos_name']}

if config['sos_name'] == 'water_surface_height_above_reference_datum':
    columns.update({'datum_id': 'datum',
                    'vertical_position (m)': 'height'})

observations.rename(columns=columns, inplace=True)

observations['sensor'] = [s.split(':')[-1] for s in observations['sensor']]
observations['station'] = [s.split(':')[-1] for s in observations['station']]
observations['name'] = [get_coops_metadata(s)[0] for
                        s in observations['station']]

observations.set_index('name', inplace=True)
# Remove duplicate index values.
observations = observations.groupby(observations.index).first()

from pytools.ioos import secoora2df

if buoys:
    secoora_observations = secoora2df(buoys, config['sos_name'])
else:
    secoora_observations = pd.DataFrame()


from pandas import concat

all_obs = concat([observations, secoora_observations], axis=0)


# Uniform 6-min time base for model/data comparison.
from owslib.ows import ExceptionReport
from pytools.ioos import pyoos2df
from pytools.tardis import save_timeseries

iris.FUTURE.netcdf_promote = True

log.info(fmt(' Observations '))
outfile = '{:%Y-%m-%d}-OBS_DATA.nc'.format(config['date']['stop'])
outfile = os.path.join(save_dir, outfile)

log.info(fmt(' Downloading to file {} '.format(outfile)))
data, bad_station = dict(), []
col = 'sea_water_salinity (psu)'
for station in observations.index:
    station_code = observations['station'][station]
    try:
        df = pyoos2df(collector, station_code, df_name=station)
        data.update({station_code: df[col]})
    except ExceptionReport as e:
        bad_station.append(station_code)
        log.warning("[{}] {}:\n{}".format(station_code, station, e))
obs_data = pd.DataFrame.from_dict(data)


# Split good and bad stations.
pattern = '|'.join(bad_station)
if pattern:
    all_obs['bad_station'] = all_obs.station.str.contains(pattern)
    observations = observations[~observations.station.str.contains(pattern)]
else:
    all_obs['bad_station'] = ~all_obs.station.str.contains(pattern)

# Save updated `all_obs.csv`.
fname = '{}-all_obs.csv'.format(config['run_name'])
fname = os.path.join(save_dir, fname)
all_obs.to_csv(fname)

log.info(fmt(' Downloading to file {} '.format(outfile)))
comment = "Several stations from http://opendap.co-ops.nos.noaa.gov"
kw = dict(longitude=observations.lon,
          latitude=observations.lat,
          station_attr=dict(cf_role="timeseries_id"),
          cube_attr=dict(featureType='timeSeries',
                         Conventions='CF-1.6',
                         standard_name_vocabulary='CF-1.6',
                         cdm_data_type="Station",
                         comment=comment,
                         url=url))

save_timeseries(obs_data, outfile=outfile,
                standard_name=config['sos_name'], **kw)


# SECOORA Observations.
from pandas import DataFrame


def extract_series(cube, station):
    time = cube.coord(axis='T')
    date_time = time.units.num2date(cube.coord(axis='T').points)
    data = cube.data
    return DataFrame(data, columns=[station], index=date_time)


if buoys:
    secoora_obs_data = []
    for station, cube in list(buoys.items()):
        df = extract_series(cube, station)
        secoora_obs_data.append(df)
    # Some series have duplicated times!
    kw = dict(subset='index', keep='last')
    secoora_obs_data = [obs.reset_index().drop_duplicates(**kw).set_index('index') for  # noqa
                        obs in secoora_obs_data]
    secoora_obs_data = concat(secoora_obs_data, axis=1)
else:
    secoora_obs_data = DataFrame()


# These buoys need some QA/QC before saving.
from pytools.qaqc import filter_spikes, threshold_series

if buoys:
    secoora_obs_data.apply(threshold_series, args=(0, 40))
    secoora_obs_data.apply(filter_spikes)

    # Interpolate to the same index as SOS.
    index = obs_data.index
    kw = dict(method='time', limit=30)
    secoora_obs_data = secoora_obs_data.reindex(index).interpolate(**kw).ix[index]  # noqa

    log.info(fmt(' SECOORA Observations '))
    fname = '{:%Y-%m-%d}-SECOORA_OBS_DATA.nc'.format(config['date']['stop'])
    fname = os.path.join(save_dir, fname)

    log.info(fmt(' Downloading to file {} '.format(fname)))

    url = "http://129.252.139.124/thredds/catalog_platforms.html"
    comment = "Several stations {}".format(url)
    kw = dict(longitude=secoora_observations.lon,
              latitude=secoora_observations.lat,
              station_attr=dict(cf_role="timeseries_id"),
              cube_attr=dict(featureType='timeSeries',
                             Conventions='CF-1.6',
                             standard_name_vocabulary='CF-1.6',
                             cdm_data_type="Station",
                             comment=comment,
                             url=url))

    save_timeseries(secoora_obs_data, outfile=fname,
                    standard_name=config['sos_name'], **kw)


# Loop discovered models and save the nearest time-series.
from iris.exceptions import (CoordinateNotFoundError, ConstraintMismatchError,
                             MergeError)

from pytools.ioos import time_limit, get_model_name
from pytools.tardis import is_model, get_surface


log.info(fmt(' Models '))
cubes = dict()

for k, url in enumerate(dap_urls):
    log.info('\n[Reading url {}/{}]: {}'.format(k+1, len(dap_urls), url))
    try:
        with time_limit(60*5):
            cube = quick_load_cubes(url, config['cf_names'], strict=True)
            if is_model(cube):
                cube = proc_cube(cube, bbox=config['region']['bbox'],
                                 time=(config['date']['start'],
                                       config['date']['stop']),
                                 units=config['units'])
            else:
                log.warning("[Not model data]: {}".format(url))
                continue
            cube = get_surface(cube)
            mod_name, model_full_name = get_model_name(cube, url,
                                                       config['models_urls'])
            cubes.update({mod_name: cube})
    except (TimeoutException, ConstraintMismatchError, CoordinateNotFoundError,
            RuntimeError, ValueError, IOError, IndexError) as e:
        log.warning('Cannot get cube for: {}\n{}'.format(url, e))


from iris.pandas import as_series
from pytools.tardis import (make_tree, get_nearest_water,
                            add_station, ensure_timeseries, remove_ssh)

for mod_name, cube in cubes.items():
    fname = '{:%Y-%m-%d}-{}.nc'.format(config['date']['stop'], mod_name)
    fname = os.path.join(save_dir, fname)
    log.info(fmt(' Downloading to file {} '.format(fname)))
    try:
        tree, lon, lat = make_tree(cube)
    except CoordinateNotFoundError as e:
        log.warning('Cannot make KDTree for: {}'.format(mod_name))
        continue
    # Get model series at observed locations.
    raw_series = dict()
    for station, obs in all_obs.iterrows():
        try:
            kw = dict(k=10, max_dist=0.04, min_var=0.01)
            args = cube, tree, obs.lon, obs.lat
            series, dist, idx = get_nearest_water(*args, **kw)
        except ValueError as e:
            status = "No Data"
            log.info('[{}] {}'.format(status, obs.name))
            continue
        except RuntimeError as e:
            status = "Failed"
            log.info('[{}] {}. ({})'.format(status, obs.name, e.message))
            continue
        if not series:
            status = "Land   "
        else:
            raw_series.update({obs['station']: series})
            series = as_series(series)
            status = "Water  "

        log.info('[{}] {}'.format(status, obs.name))

    if raw_series:  # Save cube.
        for station, cube in raw_series.items():
            cube = add_station(cube, station)
            cube = remove_ssh(cube)
        try:
            cube = iris.cube.CubeList(raw_series.values()).merge_cube()
        except MergeError as e:
            log.warning(e)

        ensure_timeseries(cube)
        iris.save(cube, fname)
        del cube

    log.info(fmt(' Finished processing {} '.format(mod_name)))


elapsed = time.time() - start_time
log.info('{:.2f} minutes'.format(elapsed/60.))
log.info('EOF')
