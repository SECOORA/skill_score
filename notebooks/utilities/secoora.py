# -*- coding: utf-8 -*-
#
# secoora.py
#
# purpose:  SECOORA helper functions
# author:   Filipe P. A. Fernandes
# e-mail:   ocefpaf@gmail
# web:      http://ocefpaf.github.io/
# created:  04-Feb-2015
# modified: Thu 05 Feb 2015 03:53:20 PM BRT
#
# obs:
#

# Standard Library.
import os
import fnmatch
import warnings
from glob import glob
from io import BytesIO
from urllib import urlopen

# Scientific stack.
import numpy as np
from owslib import fes
from pandas import Panel, DataFrame, read_csv, concat
from netCDF4 import MFDataset, date2index, num2date

import iris
from iris.pandas import as_data_frame

iris.FUTURE.netcdf_promote = True
iris.FUTURE.cell_datetime_objects = True

import requests
from lxml import etree
from bs4 import BeautifulSoup

# Local.
from .pytools import url_lister, parse_url


__all__ = ['get_model_name',
           'extract_columns',
           'secoora2df',
           'secoora_buoys',
           'load_secoora_ncs',
           'fes_date_filter',
           'service_urls',
           'processStationInfo',
           'sos_request',
           'get_ndbc_longname',
           'get_coops_longname',
           'coops2df',
           'ndbc2df',
           'nc2df',
           'scrape_thredds',
           'CF_names',
           'titles']


salinity = ['sea_water_salinity',
            'sea_surface_salinity',
            'sea_water_absolute_salinity',
            'sea_water_practical_salinity']

temperature = ['sea_water_temperature',
               'sea_surface_temperature',
               'sea_water_potential_temperature',
               'equivalent_potential_temperature',
               'sea_water_conservative_temperature',
               'pseudo_equivalent_potential_temperature']

water_level = ['sea_surface_height',
               'sea_surface_elevation',
               'sea_surface_height_above_geoid',
               'sea_surface_height_above_sea_level',
               'water_surface_height_above_reference_datum',
               'sea_surface_height_above_reference_ellipsoid']

currents = ['sea_water_speed',
            'direction_of_sea_water_velocity',
            'surface_eastward_sea_water_velocity',
            'surface_northward_sea_water_velocity',
            'surface_geostrophic_sea_water_x_velocity',
            'surface_geostrophic_sea_water_y_velocity'
            'surface_geostrophic_eastward_sea_water_velocity',
            'surface_geostrophic_northward_sea_water_velocity',
            'eastward_sea_water_velocity',
            'northward_sea_water_velocity',
            'sea_water_x_velocity',
            'sea_water_y_velocity',
            'baroclinic_eastward_sea_water_velocity',
            'baroclinic_northward_sea_water_velocity',
            'barotropic_eastward_sea_water_velocity',
            'barotropic_northward_sea_water_velocity',
            'barotropic_sea_water_x_velocity',
            'barotropic_sea_water_y_velocity',
            'bolus_eastward_sea_water_velocity',
            'bolus_northward_sea_water_velocity',
            'bolus_sea_water_x_velocity',
            'bolus_sea_water_y_velocity',
            'x_sea_water_velocity',
            'y_sea_water_velocity',
            'eastward_transformed_eulerian_mean_velocity',
            'northward_transformed_eulerian_mean_velocity',
            'surface_eastward_geostrophic_sea_water_velocity',
            'surface_northward_geostrophic_sea_water_velocity',
            'surface_geostrophic_sea_water_x_velocity_assuming_'
            'sea_level_for_geoid',
            'surface_geostrophic_sea_water_y_velocity_assuming_'
            'sea_level_for_geoid',
            'surface_geostrophic_eastward_sea_water_velocity_assuming_'
            'sea_level_for_geoid',
            'surface_geostrophic_northward_sea_water_velocity_assuming_'
            'sea_level_for_geoid',
            'surface_eastward_geostrophic_sea_water_velocity_assuming_'
            'sea_level_for_geoid',
            'surface_northward_geostrophic_sea_water_velocity_assuming_'
            'sea_level_for_geoid']

CF_names = dict({'salinity': salinity,
                 'currents': currents,
                 'water level': water_level,
                 'sea_water_temperature': temperature})

CSW = {'COMT':
       'comt.sura.org:8000',
       'NGDC Geoportal':
       'http://www.ngdc.noaa.gov/geoportal/csw',
       'USGS WHSC Geoportal':
       'http://geoport.whoi.edu/geoportal/csw',
       'NODC Geoportal: granule level':
       'http://www.nodc.noaa.gov/geoportal/csw',
       'NODC Geoportal: collection level':
       'http://data.nodc.noaa.gov/geoportal/csw',
       'NRCAN CUSTOM':
       'http://geodiscover.cgdi.ca/wes/serviceManagerCSW/csw',
       'USGS Woods Hole GI_CAT':
       'http://geoport.whoi.edu/gi-cat/services/cswiso',
       'USGS CIDA Geonetwork':
       'http://cida.usgs.gov/gdp/geonetwork/srv/en/csw',
       'USGS Coastal and Marine Program':
       'http://cmgds.marine.usgs.gov/geonetwork/srv/en/csw',
       'USGS Woods Hole Geoportal':
       'http://geoport.whoi.edu/geoportal/csw',
       'CKAN testing site for new Data.gov':
       'http://geo.gov.ckan.org/csw',
       'EPA':
       'https://edg.epa.gov/metadata/csw',
       'CWIC':
       'http://cwic.csiss.gmu.edu/cwicv1/discovery'}

titles = dict(SABGOM='http://omgsrv1.meas.ncsu.edu:8080/thredds/dodsC/fmrc/'
              'sabgom/SABGOM_Forecast_Model_Run_Collection_best.ncd',
              USEAST='http://omgsrv1.meas.ncsu.edu:8080/thredds/dodsC/fmrc/'
              'us_east/US_East_Forecast_Model_Run_Collection_best.ncd',
              COAWST_4='http://geoport.whoi.edu/thredds/dodsC/coawst_4/use/'
              'fmrc/coawst_4_use_best.ncd',
              ESPRESSO='http://tds.marine.rutgers.edu/thredds/dodsC/roms/'
              'espresso/2013_da/his_Best/'
              'ESPRESSO_Real-Time_v2_History_Best_Available_best.ncd',
              BTMPB='http://oos.soest.hawaii.edu/thredds/dodsC/hioos/tide_pac',
              TBOFS='http://opendap.co-ops.nos.noaa.gov/thredds/dodsC/TBOFS/'
              'fmrc/Aggregated_7_day_TBOFS_Fields_Forecast_best.ncd',
              HYCOM='http://oos.soest.hawaii.edu/thredds/dodsC/pacioos/hycom/'
              'global',
              CBOFS='http://opendap.co-ops.nos.noaa.gov/thredds/dodsC/CBOFS/'
              'fmrc/Aggregated_7_day_CBOFS_Fields_Forecast_best.ncd',
              ESTOFS='http://geoport-dev.whoi.edu/thredds/dodsC/estofs/'
              'atlantic',
              NECOFS_GOM3_FVCOM='http://www.smast.umassd.edu:8080/thredds/'
              'dodsC/FVCOM/NECOFS/Forecasts/NECOFS_GOM3_FORECAST.nc',
              NECOFS_GOM3_WAVE='http://www.smast.umassd.edu:8080/thredds/dodsC'
              '/FVCOM/NECOFS/Forecasts/NECOFS_WAVE_FORECAST.nc',
              USF_ROMS='http://crow.marine.usf.edu:8080/thredds/dodsC/'
              'WFS_ROMS_NF_model/USF_Ocean_Circulation_Group_West_Florida_'
              'Shelf_Daily_ROMS_Nowcast_Forecast_Model_Data_best.ncd',
              USF_SWAN='http://crow.marine.usf.edu:8080/thredds/dodsC/'
              'WFS_SWAN_NF_model/USF_Ocean_Circulation_Group_West_Florida_'
              'Shelf_Daily_SWAN_Nowcast_Forecast_Wave_Model_Data_best.ncd',
              USF_FVCOM='http://crow.marine.usf.edu:8080/thredds/dodsC/'
              'FVCOM-Nowcast-Agg.nc')


def get_model_name(cube, url):
    url = parse_url(url)
    try:
        model_full_name = cube.attributes['title']
    except AttributeError:
        model_full_name = url
    try:
        for mod_name, uri in titles.items():
            if url == uri:
                break
    except KeyError:
        warnings.warn('Model %s not in the list' % url)
        mod_name = model_full_name
    return mod_name, model_full_name


def extract_columns(name, cube):
    try:
        station = cube.attributes['abstract']
    except KeyError:
        station = name.replace('.', '_')
    sensor = 'NA'
    lon = cube.coord(axis='X').points[0]
    lat = cube.coord(axis='Y').points[0]
    time = cube.coord(axis='T')
    time = time.units.num2date(cube.coord(axis='T').points)[0]
    date_time = time.strftime('%Y-%M-%dT%H:%M:%SZ')
    data = cube.data.mean()
    return station, sensor, lat, lon, date_time, data


def secoora2df(buoys, varname):
    secoora_obs = dict()
    for station, cube in buoys.items():
        secoora_obs.update({station: extract_columns(station, cube)})

    df = DataFrame.from_dict(secoora_obs, orient='index')
    df.reset_index(inplace=True)
    columns = {'index': 'station',
               0: 'name',
               1: 'sensor',
               2: 'lat',
               3: 'lon',
               4: 'date_time',
               5: varname}

    df.rename(columns=columns, inplace=True)
    df.set_index('name', inplace=True)
    return df


def secoora_buoys():
    thredds = "http://129.252.139.124/thredds/catalog_platforms.html"
    urls = url_lister(thredds)
    base_url = "http://129.252.139.124/thredds/dodsC"
    for buoy in urls:
        if (("?dataset=" in buoy)
           and ('archive' not in buoy)
           and ('usf.c12.weatherpak' not in buoy)
           and ('cormp.ocp1.buoy' not in buoy)):
            buoy = buoy.split('id_')[1]
            url = '{}/{}.nc'.format(base_url, buoy)
            yield url


def load_secoora_ncs(run_name):
    fname = '{}-{}.nc'.format
    OBS_DATA = nc2df(os.path.join(run_name,
                                  fname(run_name, 'OBS_DATA')))
    SECOORA_OBS_DATA = nc2df(os.path.join(run_name,
                                          fname(run_name, 'SECOORA_OBS_DATA')))

    ALL_OBS_DATA = concat([OBS_DATA, SECOORA_OBS_DATA], axis=1)
    index = ALL_OBS_DATA.index

    dfs = dict(OBS_DATA=ALL_OBS_DATA)
    for fname in glob(os.path.join(run_name, "*.nc")):
        if 'OBS_DATA' in fname:
            continue
        else:
            model = fname.split('.')[0].split('-')[-1]
            df = nc2df(fname)
            # FIXME: Horrible work around duplicate times.
            if len(df.index.values) != len(np.unique(df.index.values)):
                kw = dict(cols='index', take_last=True)
                df = df.reset_index().drop_duplicates(**kw).set_index('index')
            kw = dict(method='time', limit=30)
            df = df.reindex(index).interpolate(**kw).ix[index]
            dfs.update({model: df})

    return Panel.fromDict(dfs).swapaxes(0, 2)


def fes_date_filter(start, stop, constraint='overlaps'):
    """Take datetime-like objects and returns a fes filter for date range.
    NOTE: Truncates the minutes!"""
    start = start.strftime('%Y-%m-%d %H:00')
    stop = stop.strftime('%Y-%m-%d %H:00')
    if constraint == 'overlaps':
        propertyname = 'apiso:TempExtent_begin'
        begin = fes.PropertyIsLessThanOrEqualTo(propertyname=propertyname,
                                                literal=stop)
        propertyname = 'apiso:TempExtent_end'
        end = fes.PropertyIsGreaterThanOrEqualTo(propertyname=propertyname,
                                                 literal=start)
    elif constraint == 'within':
        propertyname = 'apiso:TempExtent_begin'
        begin = fes.PropertyIsGreaterThanOrEqualTo(propertyname=propertyname,
                                                   literal=start)
        propertyname = 'apiso:TempExtent_end'
        end = fes.PropertyIsLessThanOrEqualTo(propertyname=propertyname,
                                              literal=stop)
    else:
        raise NameError('Unrecognized constraint {}'.format(constraint))
    return begin, end


def service_urls(records, service='odp:url'):
    """Extract service_urls of a specific type (DAP, SOS) from records."""
    service_string = 'urn:x-esri:specification:ServiceType:' + service
    urls = []
    for key, rec in records.items():
        # Create a generator object, and iterate through it until the match is
        # found if not found, gets the default value (here "none").
        url = next((d['url'] for d in rec.references if
                    d['scheme'] == service_string), None)
        if url is not None:
            urls.append(url)
    urls = sorted(set(urls))
    return urls


def processStationInfo(obs_loc_df, st_list, source):
    st_data = obs_loc_df['station_id']
    lat_data = obs_loc_df['latitude (degree)']
    lon_data = obs_loc_df['longitude (degree)']
    for k in range(0, len(st_data)):
        station_name = st_data[k]
        if station_name in st_list:
            pass
        else:
            st_list[station_name] = {}
            st_list[station_name]["lat"] = lat_data[k]
            st_list[station_name]["source"] = source
            st_list[station_name]["lon"] = lon_data[k]
            print(station_name)
    print("number of stations in bbox %s" % len(st_list.keys()))
    return st_list


def sos_request(url='opendap.co-ops.nos.noaa.gov/ioos-dif-sos/SOS', **kw):
    url = parse_url(url)
    offering = 'urn:ioos:network:NOAA.NOS.CO-OPS:CurrentsActive'
    params = dict(service='SOS',
                  request='GetObservation',
                  version='1.0.0',
                  offering=offering,
                  responseFormat='text/csv')
    params.update(kw)
    r = requests.get(url, params=params)
    r.raise_for_status()
    content = r.headers['Content-Type']
    if 'excel' in content or 'csv' in content:
        return r.url
    else:
        raise TypeError('Bad url {}'.format(r.url))


def get_ndbc_longname(station):
    """Get long_name for specific station from NOAA NDBC."""
    url = "http://www.ndbc.noaa.gov/station_page.php"
    params = dict(station=station)
    r = requests.get(url, params=params)
    r.raise_for_status()
    soup = BeautifulSoup(r.content)
    # NOTE: Should be only one!
    long_name = soup.findAll("h1")[0]
    long_name = long_name.text.split(' - ')[1].strip()
    long_name = long_name.split(',')[0].strip()
    return long_name.title()


def get_coops_longname(station):
    """Get longName for specific station from COOPS SOS using DescribeSensor
    request."""
    url = ('opendap.co-ops.nos.noaa.gov/ioos-dif-sos/SOS?service=SOS&'
           'request=DescribeSensor&version=1.0.0&'
           'outputFormat=text/xml;subtype="sensorML/1.0.1"&'
           'procedure=urn:ioos:station:NOAA.NOS.CO-OPS:%s') % station
    url = parse_url(url)
    tree = etree.parse(urlopen(url))
    root = tree.getroot()
    path = "//sml:identifier[@name='longName']/sml:Term/sml:value/text()"
    namespaces = dict(sml="http://www.opengis.net/sensorML/1.0.1")
    longName = root.xpath(path, namespaces=namespaces)
    if len(longName) == 0:
        longName = station
    return longName[0]


def coops2df(collector, coops_id):
    """Request CSV response from SOS and convert to Pandas DataFrames."""
    collector.features = [coops_id]
    long_name = get_coops_longname(coops_id)
    response = collector.raw(responseFormat="text/csv")
    kw = dict(parse_dates=True, index_col='date_time')
    data_df = read_csv(BytesIO(response.encode('utf-8')), **kw)
    data_df.name = long_name
    return data_df


def ndbc2df(collector, ndbc_id):
    uri = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/adcp'
    url = ('%s/%s/' % (uri, ndbc_id))
    urls = url_lister(url)

    filetype = "*.nc"
    file_list = [filename for filename in fnmatch.filter(urls, filetype)]
    files = [fname.split('/')[-1] for fname in file_list]
    urls = ['%s/%s/%s' % (uri, ndbc_id, fname) for fname in files]
    if not urls:
        raise Exception("Cannot find data at {!r}".format(url))
    nc = MFDataset(urls)

    kw = dict(calendar='gregorian', select='nearest')
    time_dim = nc.variables['time']
    dates = num2date(time_dim[:], units=time_dim.units,
                     calendar=kw['calendar'])

    idx_start = date2index(collector.start_time, time_dim, **kw)
    idx_stop = date2index(collector.end_time, time_dim, **kw)
    if idx_start == idx_stop:
        raise Exception("No data within time range"
                        " {!r} and {!r}".format(collector.start_time,
                                                collector.end_time))
    dir_dim = nc.variables['water_dir'][idx_start:idx_stop, ...].squeeze()
    speed_dim = nc.variables['water_spd'][idx_start:idx_stop, ...].squeeze()
    if dir_dim.ndim != 1:
        dir_dim = dir_dim[:, 0]
        speed_dim = speed_dim[:, 0]
    time_dim = nc.variables['time']
    dates = dates[idx_start:idx_stop].squeeze()
    data = dict()
    data['sea_water_speed (cm/s)'] = speed_dim
    col = 'direction_of_sea_water_velocity (degree)'
    data[col] = dir_dim
    time = dates
    columns = ['sea_water_speed (cm/s)',
               'direction_of_sea_water_velocity (degree)']
    return DataFrame(data=data, index=time, columns=columns)


def nc2df(fname):
    cube = iris.load_cube(fname)
    for coord in cube.coords(dimensions=[0]):
        name = coord.name()
        if name != 'time':
            cube.remove_coord(name)
    for coord in cube.coords(dimensions=[1]):
        name = coord.name()
        if name != 'station name':
            cube.remove_coord(name)
    df = as_data_frame(cube)
    if cube.ndim == 1:  # Horrible work around iris.
        station = cube.coord('station name').points[0]
        df.columns = [station]
    return df


def scrape_thredds(url, uri):
    urls = url_lister(url)
    filetype = "?dataset="
    file_list = [filename for filename in fnmatch.filter(urls, filetype)]

    files = [fname.split('/')[-1] for fname in file_list]
    urls = ['%s/%s' % (uri, fname) for fname in files]
    if not urls:
        raise Exception("Cannot find data at {!r}".format(url))
    return urls
