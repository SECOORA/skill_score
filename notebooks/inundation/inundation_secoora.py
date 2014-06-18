# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

# Standard Library.
from warnings import warn
from datetime import datetime, timedelta

# Scientific stack.
import iris
iris.FUTURE.netcdf_promote = True
import folium
import numpy as np
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, Point, LineString
from pandas import DataFrame, date_range, read_csv, concat
from iris.exceptions import CoordinateNotFoundError, ConstraintMismatchError

# Custom IOOS/ASA modules (available at PyPI).
from owslib import fes
from owslib.csw import CatalogueServiceWeb
from pyoos.collectors.coops.coops_sos import CoopsSos

# Local imports
from utilities import name_list, sos_name
from utilities import (find_timevar, find_ij, nearxy,
                       dateRange, get_coops_longname, coops2df, 
                       mod_df, service_urls, inline_map, get_coordinates, get_nearest)

# <codecell>

name_list

# <codecell>

now = datetime.utcnow()

if False:
    start = now - timedelta(days=3)
    stop = now + timedelta(days=3)
else:
    start = datetime(2014, 5, 30)
    stop = datetime(2014, 6, 3)

start_date = start.strftime('%Y-%m-%d %H:00')
stop_date = stop.strftime('%Y-%m-%d %H:00')

jd_start = datetime.strptime(start_date, '%Y-%m-%d %H:%M')
jd_stop = datetime.strptime(stop_date, '%Y-%m-%d %H:%M')

print('%s to %s' % (start_date, stop_date))

# <codecell>

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

# Is SABGOM there?
if True:
    print("CSW:")
    for rec, item in csw.records.items():
        print(item.title)
    print("\nDAP:")
    print("\n".join(dap_urls))
    print("\nSOS:")
    print("\n".join(sos_urls))

# <codecell>

found = None
for url in dap_urls:
    if 'sabgom' in url.lower():
        found = url
if not found:
    print('SABGOM not found!')

# <markdowncell>

# # The datum should be NAVD! But all the data found find are MLLW.

# <codecell>

collector = CoopsSos()

collector.set_datum('MLLW')
collector.server.identification.title
collector.start_time = jd_start
collector.end_time = jd_stop
collector.variables = [sos_name]

ofrs = collector.server.offerings
if False:
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

observations = read_csv(url)
if True:
    print(url)

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

observations['station'] = [sta.split(':')[-1] for sta in observations['station']]
observations['sensor'] = [sta.split(':')[-1] for sta in observations['sensor']]
observations['datum'] = [sta.split(':')[-1] for sta in observations['datum']]
observations['name'] = [get_coops_longname(sta) for sta in observations['station']]

observations.set_index('name', inplace=True)

# <codecell>

observations.head()

# <markdowncell>

# Generate a uniform 6-min time base for model/data comparison:

# <codecell>

data = dict()

for sta in observations.station:
    b = coops2df(collector, sta, sos_name)['water_surface_height_above_reference_datum (m)']
    data.update({sta: b})

obs_data = DataFrame.from_dict(data)

# <codecell>

obs_data.head()

# <codecell>

m = folium.Map(location=[np.mean(bounding_box, axis=0)[1],
                         np.mean(bounding_box, axis=0)[0]],
               zoom_start=5)

# Create the map and add the bounding box line.
m.line(get_coordinates(bounding_box, bounding_box_type),
       line_color='#FF0000', line_weight=2)

for station, row in observations.iterrows():
    if row['datum'] == 'NADV':
        popup_string = '<b>Station:</b><br>%s<br><b>Long Name:</b><br>%s' % (station, row['name'])
        m.simple_marker(location=[row['lat'], row['lon']], popup=popup_string)
    else:
        popup_string = '<b>Not NAVD</b><br><b>Station:</b><br>%s<br><b>Long Name:</b><br>%s' % (station, row.name)
        m.circle_marker(location=[row['lat'], row['lon']], popup=popup_string,
                        fill_color='#ff0000', radius=10000, line_color='#ff0000')
if False:
    for model, row in models.iterrows():
        popup_string = '<b>Station:</b><br>%s<br><b>Long Name:</b><br>%s' % (station, row['name'])
        m.simple_marker(location=[row['lat'], row['lon']], popup=popup_string)

inline_map(m)

# <markdowncell>

# ### Get model output from OPeNDAP URLS

# <codecell>

print('\n'.join(name_list))

name_in_list = lambda cube: cube.standard_name in name_list
constraint = iris.Constraint(cube_func=name_in_list)

# <codecell>

# Use only data where the standard deviation of the time series exceeds 0.01 m
# (1 cm) this eliminates flat line model time series that come from land
# points that should have had missing values.
min_var = 0.01

# Use only data within 0.04 degrees (about 4 km).
max_dist = 0.04

# <codecell>

def get_cube(url, constraint):
    cube = iris.load_cube(url, constraint)
    # Convert to units of meters:
    # cube.convert_units('m')  # TODO: Isn't working for unstructured data.
    mod_name = cube.attributes['title']
    timevar = find_timevar(cube)
    lat = cube.coord(axis='Y').points
    lon = cube.coord(axis='X').points
    start = timevar.units.date2num(jd_start)
    istart = timevar.nearest_neighbour_index(start)
    stop = timevar.units.date2num(jd_stop)
    istop = timevar.nearest_neighbour_index(stop)
    return cube, timevar, lon, lat, istart, istop, mod_name

# <codecell>

url = dap_urls[0]
packed = get_cube(url, constraint)
cube, timevar, lon, lat, istart, istop, mod_name = packed
print(mod_name, url)

dist, i, j = get_nearest(cube, observations.lon, observations.lat)
for x in zip(cube.coord(axis='X').points[i, j], cube.coord(axis='Y').points[i, j], observations.lon, observations.lat):
    print(x)

# <codecell>

if istart != istop:  # Only proceed if we have data in the range requested.
    nsta = len(observations.lon)
    if len(cube.shape) == 3:
        print('[Structured grid model]: %s' % url)
        data = cube[0, ...].data
        # Find the closest non-land point from a structured grid model.
        if len(lon.shape) == 1:
            lon, lat = np.meshgrid(lon, lat)
        j, i, d = find_ij(lon, lat, data, observations.lon,
                          observations.lat)
        for n in range(nsta):
            # Only use if model cell is within 0.1 degree of requested
            # location.
            if d[n] <= max_dist:
                arr = cube[istart:istop, j[n], i[n]].data
                if arr.std() >= min_var:
                    print(observations.ix[n])
    elif len(cube.shape) == 1:
        print('[Data]:', url)

