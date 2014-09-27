
# coding: utf-8

# In[1]:

get_ipython().magic('matplotlib inline')

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

from utilities import css_styles, timeit
css_styles('../style.css')


# ### SECOORA Currents notebook
# Based on IOOS system-test [notebook](http://nbviewer.ipython.org/github/ioos/system-test/blob/master/Theme_2_Extreme_Events/Scenario_2A/ModelDataCompare_Currents/Model_Obs_Compare_Currents.ipynb).
# 
# 

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
start = stop - timedelta(hours=24)

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
LOG_FILENAME = '{:%Y-%m-%d}-{}'.format(stop, 'secoora_currents.log')
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
from utilities import fes_date_filter, CF_names

name_list = CF_names['currents']

begin, end = fes_date_filter(start, stop)

kw = dict(wildCard='*',
          escapeChar='\\',
          singleChar='?',
          propertyname='apiso:AnyText')


or_filt = fes.Or([fes.PropertyIsLike(literal=('*%s*' % val), **kw) for
                  val in name_list])

not_filt = fes.Not([fes.PropertyIsLike(literal='*Averages*', **kw)])


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


# <div class="success"><strong>Get list of stations</strong>
# - we get a list of the available stations from COOPS/NDBC</div>

# In[9]:

from pyoos.collectors.coops.coops_sos import CoopsSos

sos_name = 'Currents'

sos = CoopsSos()
sos.end_time = stop
sos.start_time = start
sos.variables = [sos_name]
sos.server.identification.title

ofrs = sos.server.offerings
title = sos.server.identification.title
log.info('{}: {} offerings'.format(title, len(ofrs)))


# In[10]:

from pyoos.collectors.ndbc.ndbc_sos import NdbcSos

ndbc = NdbcSos()

ndbc.end_time = stop
ndbc.start_time = start
ndbc.variables = [sos_name]
ndbc.server.identification.title

ofrs = sos.server.offerings
title = sos.server.identification.title
log.info('{}: {} offerings'.format(title, len(ofrs)))


# In[11]:

from pandas import read_csv
from utilities import sos_request, get_coops_longname, to_html

params = dict(bin='1',
              observedProperty=sos_name,
              featureOfInterest='BBOX:{0},{1},{2},{3}'.format(*bbox))

uri = 'http://opendap.co-ops.nos.noaa.gov/ioos-dif-sos/SOS'
url = sos_request(uri, **params)
log.info('sos_request: {}'.format(url))

obs_sos = read_csv(url)
obs_sos.drop_duplicates(subset='station_id', inplace=True)

# Clean the dataframe.
drop = ['bin (count)',
        'orientation',
        'bin_size (m)',
        'number_of_bins',
        'bin_distance (m)',
        'processing_level',
        'sensor_depth (m)',
        'sampling_rate (Hz)',
        'first_bin_center (m)',
        'reporting_interval (s)',
        'sea_water_speed (cm/s)',
        'sea_water_temperature (C)',
        'platform_roll_angle (degree)',
        'platform_orientation (degree)',
        'platform_pitch_angle (degree)',
        'direction_of_sea_water_velocity (degree)']

rename = {'sensor_id': 'sensor',
          'station_id': 'station',
          'latitude (degree)': 'lat',
          'longitude (degree)': 'lon'}

obs_sos.drop(drop, axis=1, inplace=True)
obs_sos.rename(columns=rename, inplace=True)

obs_sos['sensor'] = [s.split(':')[-1] for s in obs_sos['sensor']]
obs_sos['station'] = [s.split(':')[-1] for s in obs_sos['station']]
obs_sos['name'] = [get_coops_longname(s) for s in obs_sos['station']]

obs_sos.set_index('name', inplace=True)
to_html(obs_sos)


# In[12]:

from utilities import get_ndbc_longname

params = dict(offering='urn:ioos:network:noaa.nws.ndbc:all',
              observedProperty=sos_name,
              featureOfInterest='BBOX:{0},{1},{2},{3}'.format(*bbox))

uri = 'http://sdf.ndbc.noaa.gov/sos/server.php'
url = sos_request(uri, **params)
log.info('sos_request: {}'.format(url))

obs_ndbc = read_csv(url)
obs_ndbc.drop_duplicates(subset='station_id', inplace=True)

# Clean the dataframe.
drop = ['depth (m)',
        'bin (count)',
        'pct_bad (%)',
        'quality_flags',
        'pct_rejected (%)',
        'pct_good_3_beam (%)',
        'pct_good_4_beam (%)',
        'error_velocity (cm/s)',
        'sea_water_speed (cm/s)',
        'sea_water_temperature (C)',
        'platform_roll_angle (degree)',
        'echo_intensity_beam1 (count)',
        'echo_intensity_beam2 (count)',
        'echo_intensity_beam3 (count)',
        'echo_intensity_beam4 (count)',
        'platform_pitch_angle (degree)',
        'platform_orientation (degree)',
        'upward_sea_water_velocity (cm/s)',
        'correlation_magnitude_beam1 (count)',
        'correlation_magnitude_beam2 (count)',
        'correlation_magnitude_beam3 (count)',
        'correlation_magnitude_beam4 (count)',
        'direction_of_sea_water_velocity (degree)']

rename = {'sensor_id': 'sensor',
          'station_id': 'station',
          'latitude (degree)': 'lat',
          'longitude (degree)': 'lon'}

obs_ndbc.drop(drop, axis=1, inplace=True)
obs_ndbc.rename(columns=rename, inplace=True)

obs_ndbc['sensor'] = [s.split(':')[-1] for s in obs_ndbc['sensor']]
obs_ndbc['station'] = [s.split(':')[-1] for s in obs_ndbc['station']]
obs_ndbc['name'] = [get_ndbc_longname(s) for s in obs_ndbc['station']]

obs_ndbc.set_index('name', inplace=True)
to_html(obs_ndbc)


# In[13]:

import numpy as np
from pandas import Panel, DataFrame

def df2xt(df):
    """Enter a coops2df `currents` and return a distance by time df."""
    num_bins = np.unique(df['number_of_bins'])
    if num_bins.size == 1:
        num_bins = num_bins[0]
    else:
        raise ValueError('Expect unique num_bins.  Got {!r}'.format(num_bins))
    shape = df.shape
    num_time = shape[0] // num_bins
    depths = depth = df['bin_distance (m)'].iloc[:num_bins].values
    times = df.index.values.reshape(-1, num_bins)[:, 0]
    kw = dict(index=times, columns=depths)
    ang = df['direction_of_sea_water_velocity (degree)']
    spd = df['sea_water_speed (cm/s)']
    tmp = df['sea_water_temperature (C)']
    panel = dict(ang=DataFrame(ang.reshape(-1, num_bins), **kw),
                 spd=DataFrame(spd.reshape(-1, num_bins), **kw),
                 tmp=DataFrame(tmp.reshape(-1, num_bins), **kw))
    panel = Panel.fromDict(panel)
    panel.name = df.name
    return panel


# In[14]:

import iris
from pandas import DataFrame
from iris.pandas import as_data_frame
from owslib.ows import ExceptionReport
from utilities import coops2df, save_timeseries

iris.FUTURE.netcdf_promote = True

# Saving allows for re-run with without downloading the
# data again.  Note that it will not download new
# discovered station and will keep stations that might
# have disappeared!
fname = '{:%Y-%m-%d}-SOS_DATA.nc'.format(stop)
fname = os.path.join(directory, fname)
if not os.path.isfile(fname):
    #log.info('Downloading observation to file {}.'.format(fname))
    print('Downloading observation to file {}.'.format(fname))
    data = dict()
    bad_data = []
    for station in obs_sos.station:
        try:
            df = coops2df(sos, station)
            p = df2xt(df)
            df = p.swapaxes(0, 1).swapaxes(1, 2).to_frame()
            data.update({station: df})
        except Exception as e:
            #log.warning(e)
            print(e)
            bad_data.append(station)
            name = get_coops_longname(station)
            log.warning("[%s] %s:\n%s" % (station, name, e))


# In[15]:

#    obs_data = DataFrame.from_dict(data)

    # Split good and bad_data.
#    pattern = '|'.join(bad_data)
#    if pattern:
#        mask = obs_sos.station.str.contains(pattern)
#        bad_data = obs_sos[mask]
#        obs_sos = obs_sos[~mask]

#    comment = "Several stations from http://opendap.co-ops.nos.noaa.gov"
#    kw = dict(longitude=obs_sos.lon,
#              latitude=obs_sos.lat,
#              station_attr=dict(cf_role="timeseries_id"),
#              cube_attr=dict(featureType='timeSeries',
#                             Conventions='CF-1.6',
#                             standard_name_vocabulary='CF-1.6',
#                             cdm_data_type="Station",
#                             comment=comment,
#                             url=url))
#    save_timeseries_cube(obs_data, outfile=fname, **kw)
#else:
#    log.info('Loading observation from file {}.'.format(fname))
#    cube = iris.load_cube(fname)
#    cube.remove_coord('longitude')
#    cube.remove_coord('latitude')
#    obs_data = as_data_frame(cube)

#df_html(obs_data.head())


# <div class="error"><strong>Test: </strong>
# The following cells are just to check if the data makes sense.
# It will be removed from future versions of this notebook!</div>

# In[16]:

from utilities import coops2df

df = coops2df(sos, 'jx0101')


# In[17]:

for station_name, obs in obs_ndbc.iterrows():
    try:
        ndbc2df(ndbc, obs['station'])
    except Exception as e:
        log.warning(e)


# In[18]:

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
plt.style.use('ggplot')

p = df2xt(df)
depth = -p['spd'].columns.values
index = p['spd'].index.to_pydatetime()

fig, ax = plt.subplots(figsize=(7, 2.75))
cs = ax.pcolormesh(index, depth, p['spd'].values.T, cmap=plt.cm.RdBu_r)
_ = ax.set_title(p.name)
fig.tight_layout()


# In[19]:

import mpl_toolkits.axisartist as AA
from mpl_toolkits.axes_grid1 import host_subplot

fig = plt.figure(figsize=(7, 2.75))
ax0 = host_subplot(111, axes_class=AA.Axes)
ax1 = ax0.twinx()
ax2 = ax0.twinx()

offset = 60
new_fixed_axis = ax2.get_grid_helper().new_fixed_axis
ax2.axis["right"] = new_fixed_axis(loc="right", axes=ax2,
                                   offset=(offset, 0))

ax2.axis["right"].toggle(all=True)

# Only plot the first bin.
kw = dict(linewidth=1.0, zorder=1)

p0, = ax0.plot(index, p['spd'].icol(0), color='blue', **kw)
ax0.set_ylabel('Current Speed (cm/s)')
ax0.axis["left"].label.set_color(p0.get_color())

color = 'green'
p1, = ax1.plot(index, p['ang'].icol(0), color=color, **kw)
ax1.set_ylabel('Current Direction (degrees)')
ax1.axis["right"].label.set_color(p1.get_color())

color = 'red'
p2, = ax2.plot(index, p['tmp'].icol(0), color=color, **kw)
ax2.set_ylabel('sea_water_temperature (C)')
ax2.axis["right"].label.set_color(p2.get_color())

ax0.grid(False)


# In[20]:

import folium
from utilities import get_coordinates, inline_map

lon_center, lat_center = np.array(bbox).reshape(2, 2).mean(axis=0)
currents = folium.Map(location=[lat_center, lon_center], zoom_start=5)

# Create the map and add the bounding box line.
kw = dict(line_color='#FF0000', line_weight=2)
currents.line(get_coordinates(bbox), **kw)

for station, obs in obs_sos.iterrows():
    popup = '<b>SOS:</b> {}'
    popup = popup.format(station)
    kw = dict(popup=popup, marker_color="green", marker_icon="ok")
    currents.simple_marker(location=[obs['lat'], obs['lon']], **kw)
    
for station, obs in obs_ndbc.iterrows():
    popup = '<b>NDBC:</b> {}'
    popup = popup.format(station)
    kw = dict(popup=popup, marker_color="red", marker_icon="remove")
    currents.simple_marker(location=[obs['lat'], obs['lon']], **kw)

currents.create_map(path='currents.html')
currents.render_iframe = True
inline_map(currents)


# In[21]:

elapsed = time.time() - start_time
log.info(elapsed)
log.info('EOF')

