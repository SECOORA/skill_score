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
from iris.pandas import as_series, as_data_frame
from iris.exceptions import (CoordinateNotFoundError, CoordinateMultiDimError,
                             ConstraintMismatchError, MergeError)

import folium
import vincent
import numpy as np
from pandas import Series, DataFrame, read_csv

from owslib import fes
from owslib.csw import CatalogueServiceWeb
from pyoos.collectors.coops.coops_sos import CoopsSos

# Local imports.
from utilities import (dateRange, get_coops_longname, coops2df, make_tree,
                       get_coordinates, get_model_name, get_nearest_water,
                       service_urls, slice_bbox_extract, plt_grid, get_cube,
                       save_timeseries_cube)

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

# <codecell>

collector = CoopsSos()
sos_name = 'water_surface_height_above_reference_datum'

datum = 'NAVD'
collector.set_datum(datum)
collector.end_time = jd_stop
collector.start_time = jd_start
collector.variables = [sos_name]

ofrs = collector.server.offerings
if True:
    print(collector.server.identification.title)
    print(len(ofrs))

# <codecell>

iso_start = jd_start.strftime('%Y-%m-%dT%H:%M:%SZ')
iso_stop = jd_stop.strftime('%Y-%m-%dT%H:%M:%SZ')
box_str = ','.join(str(e) for e in box)

print("Lat/Lon Box: %s" % box_str)
print("Date: %s to %s" % (iso_start, iso_stop))

# <codecell>

url = ('http://opendap.co-ops.nos.noaa.gov/ioos-dif-sos/SOS?'
       'service=SOS&request=GetObservation&version=1.0.0&'
       'observedProperty=%s&offering=urn:ioos:network:NOAA.NOS.CO-OPS:'
       'WaterLevelActive&featureOfInterest=BBOX:%s&responseFormat='
       'text/csv&eventTime=%s' % (sos_name, box_str, iso_start))

print(url)
observations = read_csv(url)

# <markdowncell>

# ### Clean the dataframe.

# <codecell>

columns = {'station_id': 'station',
           'sensor_id': 'sensor',
           'datum_id': 'datum',
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

observations.head()

# <markdowncell>

# ### Generate a uniform 6-min time base for model/data comparison:

# <codecell>

import os
from owslib.ows import ExceptionReport

fname = 'OBS_DATA.nc'
if not os.path.isfile(fname):
    data = dict()
    for s in observations.station:
        try:
            b = coops2df(collector, s, sos_name)
            b = b['water_surface_height_above_reference_datum (m)']
            data.update({s: b})
        except ExceptionReport as e:
            print("[%s] %s:\n%s" % (s, get_coops_longname(s), e))
    obs_data = DataFrame.from_dict(data)

    diff = set(observations['station'].values).difference(obs_data.columns)
    non_navd = [c not in diff for c in observations['station']]
    observations = observations[non_navd]

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
    cube = iris.load_cube(fname)
    cube.remove_coord('longitude')
    cube.remove_coord('latitude')
    obs_data = as_data_frame(cube)

obs_data.head()

# <markdowncell>

# ### Loop the models and save a csv series at each station.

# <codecell>

name_in_list = lambda cube: cube.standard_name in name_list
constraint = iris.Constraint(cube_func=name_in_list, coord_values=None)

dfs = dict()
for url in dap_urls:
    if 'NECOFS' in url:  # FIXME: NECOFS has cartesian coordinates.
        continue
    try:
        cube = get_cube(url, constraint, jd_start, jd_stop)
    except (RuntimeError, ValueError, ConstraintMismatchError) as e:
        print('Cannot get cube for: %s\n%s' % (url, e))
        continue
    try:
        longitude = bounding_box[0][0], bounding_box[1][0]
        latitude = bounding_box[0][1], bounding_box[1][1]
        cube = cube.intersection(longitude=longitude, latitude=latitude)
    except CoordinateMultiDimError:
        cube = slice_bbox_extract(cube, bounding_box)

    mod_name, model_full_name = get_model_name(cube, url)
    print('\n[%s] %s:\n%s\n' % (mod_name, cube.attributes['title'], url))

    fname = '%s.nc' % mod_name
    if not os.path.isfile(fname):
        try:  # Make tree.
            tree, lon, lat = make_tree(cube)
            fig, ax = plt_grid(lon, lat)
        except CoordinateNotFoundError as e:
            print('Cannot make KDTree for: %s' % mod_name)
            continue
        # Get model series at observed locations.
        raw_series = dict()
        interp_series = dict()
        for station, obs in observations.iterrows():
            a = obs_data[obs['station']]
            try:
                kw = dict(k=10, max_dist=0.04, min_var=0.01)
                series, dist, idx = get_nearest_water(cube, tree,
                                                      obs.lon, obs.lat, **kw)
            except ValueError as e:
                print(e)
                continue
            if not series:
                status = "Not Found"
                series = Series(np.empty_like(a) * np.NaN, index=a.index)
            else:
                raw_series.update({obs['station']: series})
                series = as_series(series)
                status = "Found"
                ax.plot(lon[idx], lat[idx], 'g.')

            print('[%s] %s' % (status, obs.name))

            kw = dict(method='time')
            series = series.reindex(a.index).interpolate(**kw).ix[a.index]
            interp_series.update({obs['station']: series})

        interp_series = DataFrame.from_dict(interp_series).dropna(axis=1, how='all')
        dfs.update({fname[:-3]: interp_series})

        if raw_series:  # Save cube.
            for station, cube in raw_series.items():
                station_coord = iris.coords.AuxCoord(station,
                                                     var_name="station",
                                                     long_name="station name")
                cube.add_aux_coord(station_coord)

            try:
                cube = iris.cube.CubeList(raw_series.values()).merge_cube()
            except MergeError:
                cube = iris.cube.CubeList(raw_series.values()).merge()
            iris.save(cube, fname)

        ax.set_title('%s: Points found %s' % (mod_name, len(interp_series.columns)))
        ax.plot(observations.lon, observations.lat, 'ro',
                zorder=1, label='Observation', alpha=0.25)
        ax.set_extent([bounding_box[0][0], bounding_box[1][0],
                       bounding_box[0][1], bounding_box[1][1]])

# <codecell>

from pandas import Panel

dfs.update(OBS_DATA=obs_data)

dfs = Panel.fromDict(dfs)
dfs = dfs.swapaxes(0, 2)

# <codecell>

inundation_map = folium.Map(location=[np.mean(bounding_box, axis=0)[1],
                                      np.mean(bounding_box, axis=0)[0]],
                            zoom_start=5)

# Create the map and add the bounding box line.
inundation_map.line(get_coordinates(bounding_box, bounding_box_type),
                    line_color='#FF0000', line_weight=2)

html = '<b>Station:</b><br>%s<br><b>Long Name:</b><br>%s'

for station in dfs:
    sta_name = get_coops_longname(station)
    df = dfs[station].dropna(axis=1, how='all')
    # FIXME: This is bad!  But I cannot represent NaN with Vega!
    df.fillna(value=0, inplace=True)
    vis = vincent.Line(df, width=400, height=200)
    vis.axis_titles(x='Time', y='Sea surface height (m)')
    vis.legend(title=sta_name)
    vis.name = sta_name
    json = 'station_%s.json' % station
    vis.to_json(json)
    obs = observations[observations['station'] == station]
    inundation_map.simple_marker(location=[obs['lat'].values[0],
                                           obs['lon'].values[0]],
                                 popup=(vis, json))

# <codecell>

inundation_map.create_map(path='inundation_map.html')
inundation_map.render_iframe = True
inundation_map

