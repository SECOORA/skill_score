# Standard Library.
import fnmatch
import requests
from io import BytesIO
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
from iris.cube import CubeList
from iris.pandas import as_cube, as_data_frame
from iris.exceptions import CoordinateNotFoundError, CoordinateMultiDimError
iris.FUTURE.netcdf_promote = True

import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER


import lxml.html
from lxml import etree
from IPython.display import HTML


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


def parse_url(url):
    """This will preserve any given scheme but will add http if none is
    provided."""
    if not urlparse(url).scheme:
        url = "http://{}".format(url)
    return url


def find_timevar(cube):
    """Return the time variable from iris."""
    try:
        cube.coord(axis='T').rename('time')
    except CoordinateNotFoundError:
        pass
    timevar = cube.coord('time')
    return timevar


def time_near(cube, start):
    """Return the nearest time to `start`."""
    timevar = find_timevar(cube)
    try:
        time = timevar.units.date2num(start)
        itime = timevar.nearest_neighbour_index(time)
    except IndexError:
        itime = -1
    return timevar.points[itime]


def slice_bbox_extract(cube, bbox):
    """Extract a sub-set of a cube inside a lon, lat bounding box
    bbox=[lon_min lon_max lat_min lat_max]."""
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
        cube = cube.intersection(longitude=(bbox[0][0], bbox[1][0]),
                                 latitude=(bbox[0][1], bbox[1][1]))
    except CoordinateMultiDimError:
        cube = slice_bbox_extract(cube, bbox)
    return cube


def get_cubes(url, name_list=None, bbox=None, time=None):
    """Load and time/space-slice the cubes from a given `url`.
    name_list : CF standard_name list of cubes
    bbox : [[lon_min, lat_min], [lon_max, lat_max]]
    time : datetime object (TODO: make it a time range.)
    """
    url = parse_url(url)
    cubes = iris.load_raw(url)
    if name_list:
        in_list = lambda cube: cube.standard_name in name_list
        cubes = CubeList([cube for cube in cubes if in_list(cube)])
        cubes = cubes.merge()
    if time:
        cubes = cubes.extract(iris.Constraint(time=time_near(cubes[0], time)))
    if bbox:
        cubes = CubeList([intersection(cube, bbox) for cube in cubes])
    return cubes


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


def inline_map(m):
    m._build_map()
    srcdoc = m.HTML.replace('"', '&quot;')
    embed = HTML('<iframe srcdoc="{srcdoc}" '
                 'style="width: 100%; height: 500px; '
                 'border: none"></iframe>'.format(srcdoc=srcdoc))
    return embed


def css_styles():
    style = """
        <style>
        .info {
            background-color:#fcf8e3;
            border-color:#faebcc;
            border-left:5px solid #8a6d3b;
            padding:.5em;
            color:#8a6d3b
        }

        .success {
            background-color:#d9edf7;
            border-color:#bce8f1;
            border-left:5px solid #31708f;
            padding:.5em;
            color:#31708f
        }

        .error {
            background-color:#f2dede;
            border-color:#ebccd1;
            border-left:5px solid #a94442;
            padding:.5em;
            color:#a94442
        }

        .warning {
            background-color:#fcf8e3;
            border-color:#faebcc;
            border-left:5px solid #8a6d3b;
            padding:.5em;
            color:#8a6d3b
        }

        .text-shadow {
            text-shadow:0 1px 0 #ccc,0 2px 0 #c9c9c9,0 3px 0 #bbb,0 4px 0 #b9b9b9,0 5px 0 #aaa,0 6px 1px rgba(0,0,0,.1)
        }

        .datagrid table {
            border-collapse:collapse;
            text-align:left;
            width:65%
        }

        .datagrid td {
            border-collapse:collapse;
            text-align:right;
        }

        .datagrid {
            font:normal 12px/150% Arial,Helvetica,sans-serif;
            background:#fff;
            overflow:hidden;
            border:1px solid #069;
            -webkit-border-radius:3px;
            -moz-border-radius:3px;
            border-radius:3px
        }

        .datagrid table td,.datagrid table th {
            padding:3px 10px
        }

        .datagrid table thead th {
            background:-webkit-gradient(linear,left top,left bottom,color-stop(0.05,#069),color-stop(1,#00557F));
            background:-moz-linear-gradient(center top,#069 5%,#00557F 100%);
            filter:progid:DXImageTransform.Microsoft.gradient(startColorstr='#006699',endColorstr='#00557F');
            background-color:#069;
            color:#FFF;
            font-size:15px;
            font-weight:700;
            border-left:1px solid #0070A8
        }

        .datagrid table thead th:first-child {
            border:none
        }

        .datagrid table tbody td {
            color:#00496B;
            border-left:1px solid #E1EEF4;
            font-size:12px;
            font-weight:400
        }

        .datagrid table tbody .alt td {
            background:#E1EEF4;
            color:#00496B
        }

        .datagrid table tbody td:first-child {
            border-left:none
        }

        .datagrid table tbody tr:last-child td {
            border-bottom:none
        }

        .datagrid table tfoot td div {
            border-top:1px solid #069;
            background:#E1EEF4
        }

        .datagrid table tfoot td {
            padding:0;
            font-size:12px
        }

        .datagrid table tfoot td div {
            padding:2px
        }

        .datagrid table tfoot td ul {
            margin:0;
            padding:0;
            list-style:none;
            text-align:right
        }

        .datagrid table tfoot li {
            display:inline
        }

        .datagrid table tfoot li a {
            text-decoration:none;
            display:inline-block;
            padding:2px 8px;
            margin:1px;
            color:#FFF;
            border:1px solid #069;
            -webkit-border-radius:3px;
            -moz-border-radius:3px;
            border-radius:3px;
            background:-webkit-gradient(linear,left top,left bottom,color-stop(0.05,#069),color-stop(1,#00557F));
            background:-moz-linear-gradient(center top,#069 5%,#00557F 100%);
            filter:progid:DXImageTransform.Microsoft.gradient(startColorstr='#006699',endColorstr='#00557F');
            background-color:#069
        }

        .datagrid table tfoot ul.active,.datagrid table tfoot ul a:hover {
            text-decoration:none;
            border-color:#069;
            color:#FFF;
            background:none;
            background-color:#00557F
        }

        div.dhtmlx_window_active,div.dhx_modal_cover_dv {
            position:fixed!important
        }
        </style>
    """
    return HTML(style)


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


def url_lister(url):
    urls = []
    connection = urlopen(url)
    dom = lxml.html.fromstring(connection.read())
    for link in dom.xpath('//a/@href'):
        urls.append(link)
    return urls


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


def get_cube(url, constraint, jd_start, jd_stop):
    """Load cube, check units and return a
    time-sliced cube to reduce download."""
    url = parse_url(url)
    cube = iris.load_cube(url, constraint)
    if not cube.units == iris.unit.Unit('meters'):
        # TODO: Isn't working for unstructured data.
        cube.convert_units('m')
    timevar = find_timevar(cube)
    start = timevar.units.date2num(jd_start)
    istart = timevar.nearest_neighbour_index(start)
    stop = timevar.units.date2num(jd_stop)
    istop = timevar.nearest_neighbour_index(stop)
    if istart == istop:
        raise(ValueError)
    return cube[istart:istop]


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


def get_nearest_water(cube, tree, xi, yi, k=10,
                      max_dist=0.04, min_var=0.01):
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


def df_html(df, max_cols=10):
    table_style = """
    <style>
    .df th { background-color: LightGray; }
    .df tbody tr:nth-child(odd) { background-color: AliceBlue; }
    .df tbody tr:nth-child(even) { background-color: Ivory; }
    </style>
    """
    return HTML(table_style + df.to_html(max_cols=max_cols, classes='df'))


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
