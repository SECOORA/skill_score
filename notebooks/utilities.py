# Standard Library.
import time
import fnmatch
import requests
import contextlib
from io import BytesIO
from warnings import warn
try:
    from urllib import urlopen
    from urlparse import urlparse
except ImportError:  # py3k
    from urllib.parse import urlparse
    from urllib.request import urlopen

# Scientific stack.
import numpy as np
import numpy.ma as ma
from owslib import fes
import matplotlib.pyplot as plt
from scipy.spatial import KDTree
from pandas import DataFrame, read_csv
from netCDF4 import Dataset, MFDataset, date2index, num2date

import iris
from iris.unit import Unit
from iris.cube import CubeList
from iris.pandas import as_cube, as_data_frame
from iris.exceptions import CoordinateNotFoundError, CoordinateMultiDimError

iris.FUTURE.netcdf_promote = True

import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


import lxml.html
from lxml import etree
from IPython.display import HTML
from folium.folium import Map

CSW = {'NGDC Geoportal':
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

titles = dict({'http://omgsrv1.meas.ncsu.edu:8080/thredds/dodsC/fmrc/sabgom/'
               'SABGOM_Forecast_Model_Run_Collection_best.ncd': 'SABGOM',
               'http://geoport.whoi.edu/thredds/dodsC/coawst_4/use/fmrc/'
               'coawst_4_use_best.ncd': 'COAWST_4',
               'http://tds.marine.rutgers.edu/thredds/dodsC/roms/espresso/'
               '2013_da/his_Best/'
               'ESPRESSO_Real-Time_v2_History_Best_Available_best.ncd':
               'ESPRESSO',
               'http://oos.soest.hawaii.edu/thredds/dodsC/hioos/tide_pac':
               'BTMPB',
               'http://opendap.co-ops.nos.noaa.gov/thredds/dodsC/TBOFS/fmrc/'
               'Aggregated_7_day_TBOFS_Fields_Forecast_best.ncd': 'TBOFS',
               'http://oos.soest.hawaii.edu/thredds/dodsC/pacioos/hycom/'
               'global': 'HYCOM',
               'http://opendap.co-ops.nos.noaa.gov/thredds/dodsC/CBOFS/fmrc/'
               'Aggregated_7_day_CBOFS_Fields_Forecast_best.ncd': 'CBOFS',
               'http://geoport-dev.whoi.edu/thredds/dodsC/estofs/atlantic':
               'ESTOFS',
               'http://www.smast.umassd.edu:8080/thredds/dodsC/FVCOM/NECOFS/'
               'Forecasts/NECOFS_GOM3_FORECAST.nc': 'NECOFS_GOM3_FVCOM',
               'http://www.smast.umassd.edu:8080/thredds/dodsC/FVCOM/NECOFS/'
               'Forecasts/NECOFS_WAVE_FORECAST.nc': 'NECOFS_GOM3_WAVE',
               'http://crow.marine.usf.edu:8080/thredds/dodsC/'
               'WFS_ROMS_NF_model/USF_Ocean_Circulation_Group_West_Florida_'
               'Shelf_Daily_ROMS_Nowcast_Forecast_Model_Data_best.ncd': 'USF'})


# Iris.
def find_timevar(cube):
    """Return the variable attached to time axis and rename it to time."""
    try:
        oldname = cube.coord(axis='T').var_name
        cube.coord(axis='T').rename('time')
        warn('Renaming {} to time for cube'
             '{}'.format(oldname, cube.name))
    except CoordinateNotFoundError:
        pass
    timevar = cube.coord('time')
    return timevar


def time_near(cube, datetime):
    """Return the nearest index to a `datetime`.
    TODO: Adapt to the new slice syntax"""
    timevar = find_timevar(cube)
    try:
        time = timevar.units.date2num(datetime)
        idx = timevar.nearest_neighbour_index(time)
    except IndexError:
        idx = -1
    return idx


def time_slice(cube, start, stop):
    """TODO: Re-write to use `iris.FUTURE.cell_datetime_objects`."""
    istart = time_near(cube, start)
    istop = time_near(cube, stop)
    if istart == istop:
        raise ValueError('istart must be different from istop.'
                         '  Got istart {} and istop {}'.format(istart, istop))
    return cube[istart:istop]


def bbox_extract_2Dcoords(cube, bbox):
    """Extract a sub-set of a cube inside a lon, lat bounding box
    bbox=[lon_min lon_max lat_min lat_max].
    NOTE: This is a work around too subset an iris cube that has
    2D lon, lat coords."""
    lons = cube.coord('longitude').points
    lats = cube.coord('latitude').points

    def minmax(v):
        return np.min(v), np.max(v)

    inregion = np.logical_and(np.logical_and(lons > bbox[0],
                                             lons < bbox[2]),
                              np.logical_and(lats > bbox[1],
                                             lats < bbox[3]))
    region_inds = np.where(inregion)
    imin, imax = minmax(region_inds[0])
    jmin, jmax = minmax(region_inds[1])
    return cube[..., imin:imax+1, jmin:jmax+1]


def intersection(cube, bbox):
    """Sub sets cube with 1D or 2D lon, lat coords.
    Using `intersection` instead of `extract` we deal with 0-360
    longitudes automagically."""
    try:
        cube = cube.intersection(longitude=(bbox[0], bbox[2]),
                                 latitude=(bbox[1], bbox[3]))
    except CoordinateMultiDimError:
        cube = bbox_extract_2Dcoords(cube, bbox)
    return cube


def get_cube(url, name_list=None, bbox=None, time=None, units=Unit('meters')):
    cubes = iris.load_raw(url)
    if name_list:
        in_list = lambda cube: cube.standard_name in name_list
        cubes = CubeList([cube for cube in cubes if in_list(cube)])
        cube = cubes.merge_cube()
    if bbox:
        cube = intersection(cube, bbox)
    if time:
        if len(time) == 1:
            start, stop = time, None
        if len(time) == 2:
            start, stop = time[0], time[1]
        else:
            raise ValueError('Time must be start or (start, stop).'
                             '  Got {}'.format(time))
        cube = time_slice(cube, start, stop)
    if units:
        if not cube.units == units:
            cube.convert_units('m')
    return cube


def standardize_fill_value(cube):
    """Work around default `fill_value` when obtaining
    `_CubeSignature` (iris) using `lazy_data()` (biggus).
    Warning use only when you DO KNOW that the slices should
    have the same `fill_value`!!!"""
    if ma.isMaskedArray(cube._my_data):
        fill_value = ma.empty(0, dtype=cube._my_data.dtype).fill_value
        cube._my_data.fill_value = fill_value
    return cube


def make_aux_coord(cube, axis='Y'):
    """Make any given coordinate an Auxiliary Coordinate."""
    coord = cube.coord(axis=axis)
    cube.remove_coord(coord)
    if cube.ndim == 2:
        cube.add_aux_coord(coord, 1)
    else:
        cube.add_aux_coord(coord)
    return cube


def ensure_timeseries(cube):
    """Ensure that the cube is CF-timeSeries compliant."""
    if not cube.coord('time').shape == cube.shape[0]:
        cube.transpose()
    make_aux_coord(cube, axis='Y')
    make_aux_coord(cube, axis='X')

    cube.attributes.update({'featureType': 'timeSeries'})
    cube.coord("station name").attributes = dict(cf_role='timeseries_id')
    return cube


def add_station(cube, station):
    """Add a station Auxiliary Coordinate and its name."""
    kw = dict(var_name="station", long_name="station name")
    coord = iris.coords.AuxCoord(station, **kw)
    cube.add_aux_coord(coord)
    return cube


def save_timeseries_cube(df, outfile='timeseries.nc', **kw):
    """http://cfconventions.org/Data/cf-convetions/cf-conventions-1.6/build
    /cf-conventions.html#idp5577536"""
    cube = as_cube(df, calendars={1: iris.unit.CALENDAR_GREGORIAN})
    cube.coord("index").rename("time")
    cube.coord("columns").rename("station name")
    cube.rename("water_surface_height_above_reference_datum")

    longitude = kw.get("longitude")
    latitude = kw.get("latitude")
    if longitude is not None:
        longitude = iris.coords.AuxCoord(longitude,
                                         var_name="lon",
                                         standard_name="longitude",
                                         long_name="station longitude",
                                         units=iris.unit.Unit("degrees"))
    cube.add_aux_coord(longitude, data_dims=1)

    if latitude is not None:
        latitude = iris.coords.AuxCoord(latitude,
                                        var_name="lat",
                                        standard_name="latitude",
                                        long_name="station latitude",
                                        units=iris.unit.Unit("degrees"))
        cube.add_aux_coord(latitude, data_dims=1)

    # Work around iris to get String instead of np.array object.
    string_list = cube.coord("station name").points.tolist()
    cube.coord("station name").points = string_list
    cube.coord("station name").var_name = 'station'

    station_attr = kw.get("station_attr")
    if station_attr is not None:
        cube.coord("station name").attributes.update(station_attr)

    cube_attr = kw.get("cube_attr")
    if cube_attr is not None:
        cube.attributes.update(cube_attr)

    iris.save(cube, outfile)


def plt_grid(lon, lat):
    fig, ax = plt.subplots(figsize=(6, 6),
                           subplot_kw=dict(projection=ccrs.PlateCarree()))
    ax.coastlines('10m', color='k', zorder=3)
    gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
                      linewidth=1.5, color='gray', alpha=0.15)
    gl.xlabels_top = gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER
    ax.plot(lon, lat, '.', color='gray', alpha=0.25, zorder=0, label='Model')
    return fig, ax


def get_model_name(cube, url):
    url = parse_url(url)
    try:
        model_full_name = cube.attributes['title']
    except AttributeError:
        model_full_name = url
    try:
        mod_name = titles[url]
    except KeyError:
        print('Model %s not in the list' % url)
        mod_name = model_full_name
    return mod_name, model_full_name


def wrap_lon180(lon):
    lon = np.atleast_1d(lon).copy()
    angles = np.logical_or((lon < -180), (180 < lon))
    lon[angles] = wrap_lon360(lon[angles] + 180) - 180
    return lon


def wrap_lon360(lon):
    lon = np.atleast_1d(lon).copy()
    positive = lon > 0
    lon = lon % 360
    lon[np.logical_and(lon == 0, positive)] = 360
    return lon


def make_tree(cube):
    """Create KDTree."""
    lon = cube.coord(axis='X').points
    lat = cube.coord(axis='Y').points
    # FIXME: Not sure if it is need when using `iris.intersect()`.
    lon = wrap_lon180(lon)
    # Structured models with 1D lon, lat.
    if (lon.ndim == 1) and (lat.ndim == 1) and (cube.ndim == 3):
        lon, lat = np.meshgrid(lon, lat)
    # Unstructure are already paired!
    tree = KDTree(zip(lon.ravel(), lat.ravel()))
    return tree, lon, lat


def get_nearest_water(cube, tree, xi, yi, k=10, max_dist=0.04, min_var=0.01):
    """Find `k` nearest model data points from an iris `cube` at station
    lon=`xi`, lat=`yi` up to `max_dist` in degrees.  Must provide a Scipy's
    KDTree `tree`."""
    # TODO: pykdtree might be faster, but would introduce another dependency.
    # Scipy is more likely to be already installed.  Still, this function could
    # be generalized to accept pykdtree tree object.
    # TODO: Make the `tree` optional, so it can be created here in case of a
    #  single search.  However, make sure that it will be faster if the `tree`
    #  is created and passed as an argument in multiple searches.
    distances, indices = tree.query(np.array([xi, yi]).T, k=k)
    if indices.size == 0:
        raise ValueError("No data found.")
    # Get data up to specified distance.
    mask = distances <= max_dist
    distances, indices = distances[mask], indices[mask]
    if distances.size == 0:
        raise ValueError("No data found for (%s,%s) using max_dist=%s." %
                         (xi, yi, max_dist))
    # Unstructured model.
    if (cube.coord(axis='X').ndim == 1) and (cube.ndim == 2):
        i = j = indices
        unstructured = True
    # Structured model.
    else:
        unstructured = False
        if cube.coord(axis='X').ndim == 2:  # CoordinateMultiDim
            i, j = np.unravel_index(indices, cube.coord(axis='X').shape)
        else:
            shape = (cube.coord(axis='Y').shape[0],
                     cube.coord(axis='X').shape[0])
            i, j = np.unravel_index(indices, shape)
    # Use only data where the standard deviation of the time series exceeds
    # 0.01 m (1 cm) this eliminates flat line model time series that come from
    # land points that should have had missing values.
    series, dist, idx = None, None, None
    for dist, idx in zip(distances, zip(i, j)):
        if unstructured:  # NOTE: This would be so elegant in py3k!
            idx = (idx[0],)
        series = cube[(slice(None),)+idx]
        # Accounting for wet-and-dry models.
        arr = ma.masked_invalid(series.data).filled(fill_value=0)
        if arr.std() <= min_var:
            series = None
            break
    return series, dist, idx


# ROMS.
def rot2d(x, y, ang):
    """Rotate vectors by geometric angle."""
    xr = x * np.cos(ang) - y * np.sin(ang)
    yr = x * np.sin(ang) + y * np.cos(ang)
    return xr, yr


def shrink(a, b):
    """Return array shrunk to fit a specified shape by trimming or averaging.

    a = shrink(array, shape)

    array is an numpy ndarray, and shape is a tuple (e.g., from
    array.shape).  `a` is the input array shrunk such that its maximum
    dimensions are given by shape. If shape has more dimensions than
    array, the last dimensions of shape are fit.

    as, bs = shrink(a, b)

    If the second argument is also an array, both a and b are shrunk to
    the dimensions of each other. The input arrays must have the same
    number of dimensions, and the resulting arrays will have the same
    shape.
    Example
    -------

    >>> shrink(rand(10, 10), (5, 9, 18)).shape
    (9, 10)
    >>> map(shape, shrink(rand(10, 10, 10), rand(5, 9, 18)))
    [(5, 9, 10), (5, 9, 10)]

    """

    if isinstance(b, np.ndarray):
        if not len(a.shape) == len(b.shape):
            raise Exception('Input arrays must have the same number of'
                            'dimensions')
        a = shrink(a, b.shape)
        b = shrink(b, a.shape)
        return (a, b)

    if isinstance(b, int):
        b = (b,)

    if len(a.shape) == 1:  # 1D array is a special case
        dim = b[-1]
        while a.shape[0] > dim:  # Only shrink a.
            if (dim - a.shape[0]) >= 2:  # Trim off edges evenly.
                a = a[1:-1]
            else:  # Or average adjacent cells.
                a = 0.5*(a[1:] + a[:-1])
    else:
        for dim_idx in range(-(len(a.shape)), 0):
            dim = b[dim_idx]
            a = a.swapaxes(0, dim_idx)  # Put working dim first
            while a.shape[0] > dim:  # Only shrink a
                if (a.shape[0] - dim) >= 2:  # trim off edges evenly
                    a = a[1:-1, :]
                if (a.shape[0] - dim) == 1:  # Or average adjacent cells.
                    a = 0.5*(a[1:, :] + a[:-1, :])
            a = a.swapaxes(0, dim_idx)  # Swap working dim back.
    return a


def get_roms(url, time_slice, n=3):
    url = parse_url(url)
    with Dataset(url) as nc:
        ncv = nc.variables
        time = ncv['ocean_time']
        tidx = date2index(time_slice, time, select='nearest')
        time = num2date(time[tidx], time.units, time.calendar)

        mask = ncv['mask_rho'][:]
        lon_rho = ncv['lon_rho'][:]
        lat_rho = ncv['lat_rho'][:]
        anglev = ncv['angle'][:]

        u = ncv['u'][tidx, -1, ...]
        v = ncv['v'][tidx, -1, ...]

        u = shrink(u, mask[1:-1, 1:-1].shape)
        v = shrink(v, mask[1:-1, 1:-1].shape)

        u, v = rot2d(u, v, anglev[1:-1, 1:-1])

        lon = lon_rho[1:-1, 1:-1]
        lat = lat_rho[1:-1, 1:-1]

        u, v = u[::n, ::n], v[::n, ::n]
        lon, lat = lon[::n, ::n], lat[::n, ::n]

        u = ma.masked_invalid(u)
        v = ma.masked_invalid(v)
    return dict(lon=lon, lat=lat, u=u, v=v, time=time)


# OWS/PYOOS.
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


def get_ncfiles_catalog(station_id, jd_start, jd_stop):
    station_name = station_id.split(":")[-1]
    uri = 'http://dods.ndbc.noaa.gov/thredds/dodsC/data/adcp'
    url = ('%s/%s/' % (uri, station_name))
    urls = url_lister(url)
    filetype = "*.nc"
    file_list = [filename for filename in fnmatch.filter(urls, filetype)]
    files = [fname.split('/')[-1] for fname in file_list]
    urls = ['%s/%s/%s' % (uri, station_name, fname) for fname in files]

    nc = MFDataset(urls)

    time_dim = nc.variables['time']
    calendar = 'gregorian'
    idx_start = date2index(jd_start, time_dim, calendar=calendar,
                           select='nearest')
    idx_stop = date2index(jd_stop, time_dim, calendar=calendar,
                          select='nearest')

    dir_dim = nc.variables['water_dir'][idx_start:idx_stop, ...].squeeze()
    speed_dim = nc.variables['water_spd'][idx_start:idx_stop, ...].squeeze()
    if dir_dim.ndim != 1:
        dir_dim = dir_dim[:, 0]
        speed_dim = speed_dim[:, 0]
    time_dim = nc.variables['time']
    dates = num2date(time_dim[idx_start:idx_stop],
                     units=time_dim.units,
                     calendar='gregorian').squeeze()
    data = dict()
    data['sea_water_speed (cm/s)'] = speed_dim
    col = 'direction_of_sea_water_velocity (degree)'
    data[col] = dir_dim
    time = dates
    columns = ['sea_water_speed (cm/s)',
               'direction_of_sea_water_velocity (degree)']
    df = DataFrame(data=data, index=time, columns=columns)
    return df


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


def coops2df(collector, coops_id, sos_name):
    """Request CSV response from SOS and convert to Pandas DataFrames."""
    collector.features = [coops_id]
    collector.variables = [sos_name]
    long_name = get_coops_longname(coops_id)
    response = collector.raw(responseFormat="text/csv")
    kw = dict(parse_dates=True, index_col='date_time')
    data_df = read_csv(BytesIO(response.encode('utf-8')), **kw)
    col = 'water_surface_height_above_reference_datum (m)'
    data_df['Observed Data'] = data_df[col]
    data_df.name = long_name
    return data_df


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


# IPython display.
def css_styles(css='style.css'):
    with open(css) as f:
        styles = f.read()
    return HTML('<style>{}</style>'.format(styles))


def to_html(df, css='../style.css'):
    with open(css, 'r') as f:
        style = """<style>{}</style>""".format(f.read())
    table = dict(style=style, table=df.to_html())
    return HTML('{style}<div class="datagrid">{table}</div>'.format(**table))


def inline_map(m):
    """Takes a folium instance or a html path and load into an iframe."""
    if isinstance(m, Map):
        m._build_map()
        srcdoc = m.HTML.replace('"', '&quot;')
        embed = HTML('<iframe srcdoc="{srcdoc}" '
                     'style="width: 100%; height: 500px; '
                     'border: none"></iframe>'.format(srcdoc=srcdoc))
    elif isinstance(m, str):
        embed = HTML('<iframe src="{src}" '
                     'style="width: 100%; height: 500px; '
                     'border: none"></iframe>'.format(src=m))
    return embed


# Web-parsing.
def parse_url(url):
    """This will preserve any given scheme but will add http if none is
    provided."""
    if not urlparse(url).scheme:
        url = "http://{}".format(url)
    return url


def url_lister(url):
    urls = []
    connection = urlopen(url)
    dom = lxml.html.fromstring(connection.read())
    for link in dom.xpath('//a/@href'):
        urls.append(link)
    return urls


def get_coordinates(bbox):
    """Create bounding box coordinates for the map.  It takes flat or
    nested list/numpy.array and returns 4 points for the map corners."""
    bbox = np.asanyarray(bbox).ravel()
    if bbox.size == 4:
        bbox = bbox.reshape(2, 2)
        coordinates = []
        coordinates.append([bbox[0][1], bbox[0][0]])
        coordinates.append([bbox[0][1], bbox[1][0]])
        coordinates.append([bbox[1][1], bbox[1][0]])
        coordinates.append([bbox[1][1], bbox[0][0]])
        coordinates.append([bbox[0][1], bbox[0][0]])
    else:
        raise ValueError('Wrong number corners.'
                         '  Expected 4 got {}'.format(bbox.size))
    return coordinates


# Misc.
@contextlib.contextmanager
def timeit(log=None):
    t = time.time()
    yield
    elapsed = time.strftime("%H:%M:%S", time.gmtime(time.time()-t))
    if log:
        log.info(elapsed)
    else:
        print(elapsed)
