# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

# Standard Library.
import os
import warnings
warnings.filterwarnings("ignore")
from datetime import datetime, timedelta

# Scientific stack.
import iris
from iris.pandas import as_series
from iris.exceptions import CoordinateNotFoundError

iris.FUTURE.netcdf_promote = True

import folium
import vincent
import numpy as np
import matplotlib.pyplot as plt

from pandas import Series, DataFrame, read_csv, concat

# Custom IOOS/ASA modules (available at PyPI).
from owslib import fes
from owslib.csw import CatalogueServiceWeb
from pyoos.collectors.coops.coops_sos import CoopsSos

# Local imports
# Local imports
from utilities import (dateRange, get_coops_longname, coops2df,
                       service_urls, inline_map, get_coordinates,
                       get_cube, make_tree, get_nearest_water, get_model_name)

# <codecell>

now = datetime(2014, 7, 5, 12, 0, 0, 0)

start = now - timedelta(days=3)
stop = now + timedelta(days=3)

start_date = start.strftime('%Y-%m-%d %H:00')
stop_date = stop.strftime('%Y-%m-%d %H:00')

jd_start = datetime.strptime(start_date, '%Y-%m-%d %H:%M')
jd_stop = datetime.strptime(stop_date, '%Y-%m-%d %H:%M')

print('%s to %s' % (start_date, stop_date))

# <codecell>

name_list = ['water level',
             'sea_surface_height',
             'sea_surface_elevation',
             'sea_surface_height_above_geoid',
             'sea_surface_height_above_sea_level',
             'water_surface_height_above_reference_datum',
             'sea_surface_height_above_reference_ellipsoid']

bounding_box_type = "box"
bounding_box = [[-87.4, 24.25],
                [-74.7, 36.70]]  # SECOORA: NC, SC GA, FL

box = []
box.append(bounding_box[0][0])
box.append(bounding_box[0][1])
box.append(bounding_box[1][0])
box.append(bounding_box[1][1])

start, stop = dateRange(start_date, stop_date)
bbox = fes.BBox(box)

or_filt = fes.Or([fes.PropertyIsLike(propertyname='apiso:AnyText',
                                     literal=('*%s*' % val),
                                     escapeChar='\\',
                                     wildCard='*',
                                     singleChar='?') for val in name_list])

val = 'Averages'
not_filt = fes.Not([fes.PropertyIsLike(propertyname='apiso:AnyText',
                                       literal=('*%s*' % val),
                                       escapeChar='\\',
                                       wildCard='*',
                                       singleChar='?')])

filter_list = [fes.And([bbox, start, stop, or_filt, not_filt])]

# <codecell>

endpoint = 'http://www.ngdc.noaa.gov/geoportal/csw'
csw = CatalogueServiceWeb(endpoint, timeout=60)
csw.getrecords2(constraints=filter_list, maxrecords=1000, esn='full')

if True:
    print("CSW version: %s" % csw.version)
    print("Number of datasets available: %s" % len(csw.records.keys()))

# <codecell>

dap_urls = service_urls(csw.records, service='odp:url')
sos_urls = service_urls(csw.records, service='sos:url')

if True:
    print("CSW:")
    for rec, item in csw.records.items():
        print(item.title)
    print("\nDAP:")
    print("\n".join(dap_urls))
    print("\nSOS:")
    print("\n".join(sos_urls))

# <codecell>

sos_name = 'water_surface_height_above_reference_datum'

collector = CoopsSos()

collector.set_datum('NAVD')
collector.server.identification.title
collector.start_time = jd_start
collector.end_time = jd_stop
collector.variables = [sos_name]

ofrs = collector.server.offerings
if True:
    print(len(ofrs))

# <codecell>

iso_start = jd_start.strftime('%Y-%m-%dT%H:%M:%SZ')
iso_stop = jd_stop.strftime('%Y-%m-%dT%H:%M:%SZ')
box_str = ','.join(str(e) for e in box)

print("Date: %s to %s" % (iso_start, iso_stop))
print("Lat/Lon Box: %s" % box_str)

# <codecell>

url = ('http://opendap.co-ops.nos.noaa.gov/ioos-dif-sos/SOS?'
       'service=SOS&request=GetObservation&version=1.0.0&'
       'observedProperty=%s&offering=urn:ioos:network:NOAA.NOS.CO-OPS:'
       'WaterLevelActive&featureOfInterest=BBOX:%s&responseFormat='
       'text/csv&eventTime=%s' % (sos_name, box_str, iso_start))

print(url)

observations = read_csv(url)

# <codecell>

# Clean the dataframe.
columns = {'station_id': 'station',
           'sensor_id': 'sensor',
           'datum_id': 'datum',
           'latitude (degree)': 'lat',
           'longitude (degree)': 'lon',
           'vertical_position (m)': 'height',
           'water_surface_height_above_reference_datum (m)': 'ssh above datum'}

observations.rename(columns=columns, inplace=True)

observations['station'] = [s.split(':')[-1] for s in observations['station']]
observations['sensor'] = [s.split(':')[-1] for s in observations['sensor']]
observations['datum'] = [s.split(':')[-1] for s in observations['datum']]
observations['name'] = [get_coops_longname(s) for s in observations['station']]

observations.set_index('name', inplace=True)

# <codecell>

observations.head()

# <markdowncell>

# ### Generate a uniform 6-min time base for model/data comparison:

# <codecell>

from owslib.ows import ExceptionReport

fname = 'OBS_DATA.csv'
if not os.path.isfile(fname):
    data = dict()
    for s in observations.station:
        try:
            b = coops2df(collector, s, sos_name)
            b = b['water_surface_height_above_reference_datum (m)']
            data.update({s: b})
        except ExceptionReport as e:
            print("Station %s:\n%s" % (s, e))
            
    obs_data = DataFrame.from_dict(data)
    obs_data.to_csv(fname)
else:
    obs_data = read_csv(fname, parse_dates=True, index_col=0)

obs_data.head()

# <codecell>

diff = set(observations['station'].values).difference(obs_data.columns)
non_navd = [c not in diff for c in observations['station']]
observations = observations[non_navd]

# <markdowncell>

# ### Get model output from OPeNDAP URLS

# <codecell>

name_in_list = lambda cube: cube.standard_name in name_list
constraint = iris.Constraint(cube_func=name_in_list)

# <codecell>

# Use only data where the standard deviation of the time series exceeds 0.01 m
# (1 cm) this eliminates flat line model time series that come from land
# points that should have had missing values.
min_var = 0.01

# Use only data within 0.04 degrees (about 4 km).
max_dist = 0.04

# <markdowncell>

# ### Loop the models and save a csv series at each station.

# <codecell>

for url in dap_urls:
    try:  # Download cube.
        cube = get_cube(url, constraint, jd_start, jd_stop)
        print(cube.attributes['title'])
    except RuntimeError as e:
        print('Cannot get cube for: %s' % url)
        print(e)
        continue

    mod_name, model_full_name = get_model_name(cube, url)
    print('\n%s:\n%s\n' % (mod_name, url))
    fname = '%s.csv' % mod_name

    if not os.path.isfile(fname):
        try:  # Make tree.
            tree, lon, lat = make_tree(cube)
        except CoordinateNotFoundError as e:
            # FIXME: NECOFS_GOM3_WAVE use in meters instead of lon, lat.
            print('Cannot make KDTree for: %s' % mod_name)
            print(e)
            continue
        # Get model series at observed locations.
        model = dict()
        for station, obs in observations.iterrows():
            kw = dict(shape=lon.shape, k=100)
            a = obs_data[obs['station']]
            try:
                model_data = get_nearest_water(cube, tree, obs.lon, obs.lat, **kw)
                model_data = as_series(model_data)
            except (ValueError, AttributeError) as e:
                print('No data found for *%s*' % obs.name)
                model_data = Series(np.empty_like(a) * np.NaN, index=a.index)
            model_data.name = mod_name

            kw = dict(method='time')
            model_data = model_data.reindex(a.index).interpolate(**kw).ix[a.index]
            model.update({obs['station']: model_data})

        model = DataFrame.from_dict(model)
        model.to_csv(fname)

# <codecell>

from glob import glob
from pandas import Panel

dfs = dict()
kw = dict(parse_dates=True, index_col=0)
for fname in glob('*.csv'):
    df = read_csv(fname, **kw)
    dfs.update({fname[:-4]: df})
    
dfs = Panel.fromDict(dfs)
dfs = dfs.swapaxes(0, 2)

# <codecell>

m = folium.Map(location=[np.mean(bounding_box, axis=0)[1],
                         np.mean(bounding_box, axis=0)[0]],
               zoom_start=5)

# Create the map and add the bounding box line.
m.line(get_coordinates(bounding_box, bounding_box_type),
       line_color='#FF0000', line_weight=2)

html = '<b>Station:</b><br>%s<br><b>Long Name:</b><br>%s'

for station in dfs:
    sta_name = get_coops_longname(station)
    df = dfs[station].dropna(axis=1, how='all')
    df.fillna(value=0, inplace=True)  # FIXME: This is bad!  But I cannot represent NaN with Vega!
    vis = vincent.Line(df, width=400, height=200)
    vis.axis_titles(x='Time', y='Sea surface height (m)')
    vis.legend(title=sta_name)
    json = 'station_%s.json' % station
    vis.to_json(json)
    obs = observations[observations['station'] == station]
    m.simple_marker(location=[obs['lat'].values[0], obs['lon'].values[0]], popup=(vis, json))
    m.create_map(path='inundation.html')

inline_map(m)

# <markdowncell>

# ```python
# for station in dfs:
#     ax = dfs[station].dropna(axis=1, how='all').plot()
#     ax.set_title(get_coops_longname(station))
#     ax.set_ylim(-1, 1)
# ```

