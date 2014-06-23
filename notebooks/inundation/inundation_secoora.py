# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

# Standard Library.
import warnings
warnings.filterwarnings("ignore")
from datetime import datetime, timedelta

# Scientific stack.
import iris
iris.FUTURE.netcdf_promote = True
import folium
import numpy as np
import matplotlib.pyplot as plt

from pandas import DataFrame, read_csv, concat

# Custom IOOS/ASA modules (available at PyPI).
from owslib import fes
from owslib.csw import CatalogueServiceWeb
from pyoos.collectors.coops.coops_sos import CoopsSos

# Local imports
from utilities import (dateRange, get_coops_longname, coops2df,
                       service_urls, inline_map, get_coordinates,
                       get_cube, make_tree, get_nearest_water)

# <codecell>

now = datetime.utcnow()

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

# <markdowncell>

# # The datum should be NAVD! But all the data found find are MLLW.

# <codecell>

sos_name = 'water_surface_height_above_reference_datum'

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

observations['station'] = [s.split(':')[-1] for s in observations['station']]
observations['sensor'] = [s.split(':')[-1] for s in observations['sensor']]
observations['datum'] = [s.split(':')[-1] for s in observations['datum']]
observations['name'] = [get_coops_longname(s) for s in observations['station']]

observations.set_index('name', inplace=True)

# <codecell>

observations.head()

# <markdowncell>

# Generate a uniform 6-min time base for model/data comparison:

# <codecell>

data = dict()

for s in observations.station:
    b = coops2df(collector, s, sos_name)
    b = b['water_surface_height_above_reference_datum (m)']
    data.update({s: b})

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
    if row['datum'] == 'NAVD':
        html = '<b>Station:</b><br>%s<br><b>Long Name:</b><br>%s'
        popup_string = html % (station, row['name'])
        m.simple_marker(location=[row['lat'], row['lon']], popup=popup_string)
    else:
        html = '<b>%s</b><br><b>Station:</b><br>%s<br><b>Long Name:</b><br>%s'
        popup_string = html % (row['datum'], station, row.name)
        m.circle_marker(location=[row['lat'], row['lon']], popup=popup_string,
                        fill_color='#ff0000', radius=1e4, line_color='#ff0000')

inline_map(m)

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

# <codecell>

import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


def plt_grid(lon, lat, i, j):
    fig, ax = plt.subplots(figsize=(6, 6),
                           subplot_kw=dict(projection=ccrs.PlateCarree()))
    ax.coastlines('10m', color='k', zorder=3)
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=1.5, color='gray', alpha=0.5, linestyle='--')
    gl.xlabels_top = gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    if (lon.ndim == 1) and (lon.size != lat.size):
        lon, lat = np.meshgrid(lon, lat)
    ax.plot(lon, lat, '.', color='gray', alpha=0.25, zorder=0,
            label='Model')
    ax.plot(observations.lon, observations.lat, 'ro', zorder=1,
            label='Observation')
    if cube.ndim == 3:
        ax.plot(lon[i, j], lat[i, j], 'g.', zorder=2, label='Model@Obs')
    else:
        ax.plot(lon[i], lat[i], 'g.', label='Model@Obs')
    ax.set_title(mod_name)
    return fig, ax

# <codecell>

url = dap_urls[0]  # Plotting SABGOM only for now to avoid a big output.

cube = get_cube(url, constraint, jd_start, jd_stop)
# Cube metadata.
mod_name = cube.attributes['title']
lat = cube.coord(axis='Y').points
lon = cube.coord(axis='X').points
print('%s:\n%s\n' % (mod_name, url))
# Find the closest non-land point from a structured grid model.
tree, lon, lat = make_tree(cube)

for station, obs in observations.iterrows():
    try:
        data = get_nearest_water(cube, tree, obs.lon, obs.lat,
                                 shape=lon.shape, k=100)
        a = obs_data[obs.station]
        data.name = mod_name
        df = concat([a, data], axis=1).sort_index().interpolate().ix[a.index]
        ax = df.plot(legend=False)
        patches, labels = ax.get_legend_handles_labels()
        ax.legend(patches, labels, bbox_to_anchor=(1.5, 1.15),
                  ncol=3, fancybox=True, shadow=True)
    except ValueError as e:
        print(e)  # TODO: Output station object with name instead of position.

