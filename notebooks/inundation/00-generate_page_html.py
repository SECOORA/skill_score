
# coding: utf-8

# This notebook generate the map and table HTMLs for the SECOORA web-page.  The
# named notebook will be frozen with the bias example.  This one will be run
# weekly.

# In[1]:

import iris
import pyoos
import owslib

import time
start_time = time.time()


# In[2]:

import os
import sys
root = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(root)

from utilities import timeit


# ### SECOORA iundation notebook
# Based on IOOS system-test [notebook](https://github.com/ioos/system-test/tree/master/Theme_2_Extreme_Events/Scenario_2A_Coastal_Inundation/Scenario_2A_ModelDataCompare_Inundation).

# In[3]:

import pytz
from datetime import datetime, timedelta

# Choose the date range.
if False:
    kw = dict(hour=12, minute=0, second=0, microsecond=0)
    stop = datetime.utcnow().replace(**kw)
else:
    stop = datetime(2014, 8, 29, 12)

stop = stop.replace(tzinfo=pytz.utc)
start = stop - timedelta(days=7)

# SECOORA region (NC, SC GA, FL).
bbox = [-87.40, 24.25, -74.70, 36.70]


# In[4]:

directory = '{:%Y-%m-%d}'.format(stop)

if not os.path.exists(directory):
    os.makedirs(directory)


# In[5]:

import logging as log
reload(log)

log.captureWarnings(True)
LOG_FILENAME = '{:%Y-%m-%d}-{}'.format(stop, 'secoora_inundation.log')
LOG_FILENAME = os.path.join(directory, LOG_FILENAME)
log.basicConfig(filename=LOG_FILENAME,
                filemode='w',
                format='%(asctime)s %(levelname)s: %(message)s',
                datefmt='%I:%M:%S',
                level=log.INFO,
                stream=None)

log.info('Run date: {:%Y-%m-%d %H:%M:%S}'.format(datetime.utcnow()))
log.info('Download start: {:%Y-%m-%d %H:%M:%S}'.format(start))
log.info('Download stop: {:%Y-%m-%d %H:%M:%S}'.format(stop))
log.info('Bounding box: {0:3.2f}, {1:3.2f},'
         '{2:3.2f}, {3:3.2f}'.format(*bbox))
log.info('Iris version: {}'.format(iris.__version__))
log.info('owslib version: {}'.format(owslib.__version__))
log.info('pyoos version: {}'.format(pyoos.__version__))


# In[6]:

from owslib import fes
from utilities import fes_date_filter

# CF-names to look for (Sea Surface Height).
name_list = ['water level',
             'sea_surface_height',
             'sea_surface_elevation',
             'sea_surface_height_above_geoid',
             'sea_surface_height_above_sea_level',
             'water_surface_height_above_reference_datum',
             'sea_surface_height_above_reference_ellipsoid']

kw = dict(wildCard='*',
          escapeChar='\\',
          singleChar='?',
          propertyname='apiso:AnyText')

or_filt = fes.Or([fes.PropertyIsLike(literal=('*%s*' % val), **kw)
                  for val in name_list])

not_filt = fes.Not([fes.PropertyIsLike(literal='*Averages*', **kw)])

begin, end = fes_date_filter(start, stop)
filter_list = [fes.And([fes.BBox(bbox), begin, end, or_filt, not_filt])]


# In[7]:

from owslib.csw import CatalogueServiceWeb

endpoint = 'http://www.ngdc.noaa.gov/geoportal/csw'
csw = CatalogueServiceWeb(endpoint, timeout=60)
csw.getrecords2(constraints=filter_list, maxrecords=1000, esn='full')

log.info("CSW version: %s" % csw.version)
log.info("Number of datasets available: %s" % len(csw.records.keys()))


# In[8]:

from utilities import service_urls

dap_urls = service_urls(csw.records, service='odp:url')
sos_urls = service_urls(csw.records, service='sos:url')

for rec, item in csw.records.items():
    log.info('CSW: {}'.format(item.title))

for url in dap_urls:
    log.info('DAP: {}.html'.format(url))

for url in sos_urls:
    log.info('SOS: {}'.format(url))


# In[9]:

from pyoos.collectors.coops.coops_sos import CoopsSos

collector = CoopsSos()
sos_name = 'water_surface_height_above_reference_datum'

datum = 'NAVD'
collector.set_datum(datum)
collector.end_time = stop
collector.start_time = start
collector.variables = [sos_name]

ofrs = collector.server.offerings
title = collector.server.identification.title
log.info('{}: {} offerings'.format(title, len(ofrs)))


# In[10]:

from pandas import read_csv
from utilities import sos_request

params = dict(observedProperty=sos_name,
              eventTime=start.strftime('%Y-%m-%dT%H:%M:%SZ'),
              featureOfInterest='BBOX:{0},{1},{2},{3}'.format(*bbox),
              offering='urn:ioos:network:NOAA.NOS.CO-OPS:WaterLevelActive')

uri = 'http://opendap.co-ops.nos.noaa.gov/ioos-dif-sos/SOS'
url = sos_request(uri, **params)
observations = read_csv(url)

log.info('sos_request'.format(url))


# #### Clean the dataframe (visualization purpose only)

# In[11]:

from utilities import get_coops_longname, to_html

columns = {'datum_id': 'datum',
           'sensor_id': 'sensor',
           'station_id': 'station',
           'latitude (degree)': 'lat',
           'longitude (degree)': 'lon',
           'vertical_position (m)': 'height',
           'water_surface_height_above_reference_datum (m)': 'ssh above datum'}

observations.rename(columns=columns, inplace=True)

observations['datum'] = [s.split(':')[-1] for s in observations['datum']]
observations['sensor'] = [s.split(':')[-1] for s in observations['sensor']]
observations['station'] = [s.split(':')[-1] for s in observations['station']]
observations['name'] = [get_coops_longname(s) for s in observations['station']]

observations.set_index('name', inplace=True)
to_html(observations.head())


# #### Generate a uniform 6-min time base for model/data comparison

# In[12]:

import iris
from pandas import DataFrame
from iris.pandas import as_data_frame
from owslib.ows import ExceptionReport
from utilities import coops2df, save_timeseries_cube

iris.FUTURE.netcdf_promote = True

# Saving allows for re-run with without downloading the
# data again.  Note that it will not download new
# dicovered station and will keep stations that might
# have disapeared!
fname = '{:%Y-%m-%d}-OBS_DATA.nc'.format(stop)
fname = os.path.join(directory, fname)
if not os.path.isfile(fname):
    log.info('Downloading observation to file {}.'.format(fname))
    data = dict()
    bad_datum = []
    for station in observations.station:
        try:
            df = coops2df(collector, station, sos_name)
            col = 'water_surface_height_above_reference_datum (m)'
            data.update({station: df[col]})
        except ExceptionReport as e:
            bad_datum.append(station)
            name = get_coops_longname(station)
            log.warning("[%s] %s:\n%s" % (station, name, e))
    obs_data = DataFrame.from_dict(data)

    # Split good and bad vertical datum stations.
    pattern = '|'.join(bad_datum)
    if pattern:
        non_navd = observations.station.str.contains(pattern)
        bad_datum = observations[non_navd]
        observations = observations[~non_navd]

    comment = "Several stations from http://opendap.co-ops.nos.noaa.gov"
    kw = dict(longitude=observations.lon,
              latitude=observations.lat,
              station_attr=dict(cf_role="timeseries_id"),
              cube_attr=dict(featureType='timeSeries',
                             Conventions='CF-1.6',
                             standard_name_vocabulary='CF-1.6',
                             cdm_data_type="Station",
                             comment=comment,
                             datum=datum,
                             url=url))

    save_timeseries_cube(obs_data, outfile=fname, **kw)
else:
    log.info('Loading observation from file {}.'.format(fname))
    cube = iris.load_cube(fname)
    cube.remove_coord('longitude')
    cube.remove_coord('latitude')
    obs_data = as_data_frame(cube)

to_html(obs_data.head())


# #### Loop discovered models and save the nearest time-series

# In[13]:

import numpy as np
from iris.pandas import as_series
from iris.exceptions import (CoordinateNotFoundError, ConstraintMismatchError,
                             MergeError)

from utilities import (standardize_fill_value, plt_grid, get_cube,
                       get_model_name, make_tree, get_nearest_water,
                       add_station, ensure_timeseries)

for k, url in enumerate(dap_urls):
    with timeit(log):
        log.info('\n[Reading url {}/{}]: {}'.format(k+1, len(dap_urls), url))
        if 'NECOFS' in url:  # FIXME: NECOFS has cartesian coordinates.
            continue
        try:
            cube = get_cube(url, name_list=name_list, bbox=bbox,
                            time=(start, stop), units=iris.unit.Unit('meters'))
            if cube.ndim == 1:  # We Need a better way to identify model data.
                log.warning('url {} is probably a timeSeries!'.format(url))
                continue
        except (RuntimeError, ValueError, MergeError,
                ConstraintMismatchError) as e:
            log.warning('Cannot get cube for: %s\n%s' % (url, e))
            continue

        mod_name, model_full_name = get_model_name(cube, url)

        fname = '{:%Y-%m-%d}-{}.nc'.format(stop, mod_name)
        fname = os.path.join(directory, fname)
        log.info('Downloading model series to file {}.'.format(fname))
        if not os.path.isfile(fname):
            try:  # Make tree.
                tree, lon, lat = make_tree(cube)
                fig, ax = plt_grid(lon, lat)
            except CoordinateNotFoundError as e:
                log.warning('Cannot make KDTree for: %s' % mod_name)
                continue
            # Get model series at observed locations.
            raw_series = dict()
            for station, obs in observations.iterrows():
                a = obs_data[obs['station']]
                try:
                    kw = dict(k=10, max_dist=0.04, min_var=0.01)
                    args = cube, tree, obs.lon, obs.lat
                    series, dist, idx = get_nearest_water(*args, **kw)
                # RuntimeError may occurs, but you should run it again!
                except ValueError as e:
                    log.warning(e)
                    continue
                if not series:
                    status = "Found Land"
                else:
                    raw_series.update({obs['station']: series})
                    series = as_series(series)
                    status = "Found Water"
                    ax.plot(lon[idx], lat[idx], 'g.')

                log.info('[%s] %s' % (status, obs.name))

            if raw_series:  # Save cube.
                for station, cube in raw_series.items():
                    cube = standardize_fill_value(cube)
                    cube = add_station(cube, station)
                try:
                    cube = iris.cube.CubeList(raw_series.values()).merge_cube()
                except MergeError as e:
                    log.warning(e)

                ensure_timeseries(cube)
                iris.save(cube, fname)
                del cube

            size = len(raw_series)
            ax.set_title('%s: Points found %s' % (mod_name, size))
            ax.plot(observations.lon, observations.lat, 'ro',
                    zorder=1, label='Observation', alpha=0.25)
            ax.set_extent([bbox[0], bbox[2], bbox[1], bbox[3]])

        log.info('[{}]: {}'.format(mod_name, url))


# #### Load saved files and interpolate to the observations time interval

# In[14]:

from glob import glob
from pandas import Panel
from utilities import nc2df

fname = '{}-OBS_DATA.nc'.format(directory)
fname = os.path.join(directory, fname)
OBS_DATA = nc2df(fname)
index = OBS_DATA.index

dfs = dict(OBS_DATA=OBS_DATA)
for fname in glob(os.path.join(directory, "*.nc")):
    if 'OBS_DATA' in fname:
        pass
    else:
        model = fname.split('.')[0].split('-')[-1]
        df = nc2df(fname)
        kw = dict(method='time', limit=30)
        df = df.reindex(index).interpolate(**kw).ix[index]
        dfs.update({model: df})

dfs = Panel.fromDict(dfs).swapaxes(0, 2)


# In[15]:

import folium
import vincent
from utilities import get_coordinates, inline_map

lon_center, lat_center = np.array(bbox).reshape(2, 2).mean(axis=0)
inundation_map = folium.Map(location=[lat_center, lon_center], zoom_start=5)

# Create the map and add the bounding box line.
kw = dict(line_color='#FF0000', line_weight=2)
inundation_map.line(get_coordinates(bbox), **kw)

for station in dfs:
    sta_name = get_coops_longname(station)
    df = dfs[station].dropna(axis=1, how='all')
    # FIXME: This is bad!  But I cannot represent NaN with Vega!
    df.fillna(value='null', inplace=True)
    vis = vincent.Line(df, width=500, height=150)
    vis.axis_titles(x='Time', y='Sea surface height (m)')
    vis.legend(title=sta_name)
    vis.name = sta_name
    json = 'station_{}.json'.format(station)
    vis.to_json(os.path.join(directory, json))
    obs = observations[observations['station'] == station].squeeze()
    popup = (vis, json)
    kw = dict(popup=popup, marker_color="green", marker_icon="ok")
    inundation_map.simple_marker(location=[obs['lat'], obs['lon']], **kw)

if isinstance(bad_datum, DataFrame):
    for station, obs in bad_datum.iterrows():
        popup = '<b>Station:</b> {}<br><b>Datum:</b> {}<br>'
        popup = popup.format(station, obs['datum'])
        kw = dict(popup=popup, marker_color="red", marker_icon="remove")
        inundation_map.simple_marker(location=[obs['lat'], obs['lon']], **kw)

inundation_map.create_map(path=os.path.join(directory, 'inundation_map.html'))
inline_map(os.path.join(directory, 'inundation_map.html'))


# In[16]:

elapsed = time.time() - start_time
log.info(elapsed)
log.info('EOF')


# ### Compute bias

# In[17]:

import os
import sys
root = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(root)

from utilities import nc2df


# In[18]:

fname = '{}-OBS_DATA.nc'.format(directory)
fname = os.path.join(directory, fname)

OBS_DATA = nc2df(fname)
index = OBS_DATA.index


# In[19]:

from glob import glob
from pandas import Panel

dfs = dict(OBS_DATA=OBS_DATA)
for fname in glob(os.path.join(directory, "*.nc")):
    if 'OBS_DATA' in fname:
        pass
    else:
        model = fname.split('.')[0].split('-')[-1]
        df = nc2df(fname)
        if False:
            kw = dict(method='time')
            df = df.reindex(index).interpolate(**kw).ix[index]
        dfs.update({model: df})

dfs = Panel.fromDict(dfs).swapaxes(0, 2)


# In[20]:

from pandas import DataFrame

means = dict()
for station, df in dfs.iteritems():
    df.dropna(axis=1, how='all', inplace=True)
    mean = df.mean()
    df = df - mean + mean['OBS_DATA']
    means.update({station: mean['OBS_DATA'] - mean.drop('OBS_DATA')})

bias = DataFrame.from_dict(means).dropna(axis=1, how='all')
bias = bias.applymap('{:.2f}'.format).replace('nan', '--')

columns = dict()
[columns.update({station: get_coops_longname(station)}) for
 station in bias.columns.values]

bias.rename(columns=columns, inplace=True)


# In[21]:

fname = os.path.join(directory, 'table.html'.format(directory))

with open('../style.css', 'r') as f:
    style = """<style>{}</style>""".format(f.read())
    table = dict(style=style, table=bias.T.to_html())
    table = '{style}<div class="datagrid">{table}</div>'.format(**table)

with open(fname, 'w') as f:
    f.writelines(table)

to_html(bias.T)
