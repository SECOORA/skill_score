# Standard Library.
import os
import time
import signal
from urllib import urlopen
from urlparse import urlparse
from contextlib import contextmanager

# Scientific stack.
import numpy as np
import numpy.ma as ma
from pandas import read_csv
from netCDF4 import Dataset, date2index, num2date

import iris

iris.FUTURE.netcdf_promote = True
iris.FUTURE.cell_datetime_objects = True

from cartopy.feature import NaturalEarthFeature, COLORS

import lxml.html
from folium.folium import Map
from IPython.display import HTML, IFrame


__all__ = ['rot2d',
           'shrink',
           'get_roms',
           'css_styles',
           'to_html',
           'make_map',
           'inline_map',
           'get_coordinates',
           'parse_url',
           'url_lister',
           'timeit',
           'time_limit',
           'TimeoutException']


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


# IPython display.
def css_styles(css='style.css'):
    with open(css) as f:
        styles = f.read()
    return HTML('<style>{}</style>'.format(styles))


def to_html(df, css='style.css'):
    with open(css, 'r') as f:
        style = """<style>{}</style>""".format(f.read())
    table = dict(style=style, table=df.to_html())
    return HTML('{style}<div class="datagrid">{table}</div>'.format(**table))


# Mapping
LAND = NaturalEarthFeature('physical', 'land', '10m', edgecolor='face',
                           facecolor=COLORS['land'])

rootpath = os.path.split(__file__)[0]
df = read_csv(os.path.join(rootpath, 'climatology_data_sources.csv'))


def make_map(bbox, **kw):
    """Creates a folium map instance for SECOORA."""

    line = kw.pop('line', True)
    states = kw.pop('states', True)
    zoom_start = kw.pop('zoom_start', 5)
    secoora_stations = kw.pop('secoora_stations', True)

    lon, lat = np.array(bbox).reshape(2, 2).mean(axis=0)
    m = Map(width=750, height=500,
            location=[lat, lon], zoom_start=zoom_start)
    if line:
        # Create the map and add the bounding box line.
        kw = dict(line_color='#FF0000', line_weight=2)
        m.line(get_coordinates(bbox), **kw)
    if states:
        path = 'https://raw.githubusercontent.com/ocefpaf/secoora/factor_map/'
        path += 'notebooks/secoora.json'
        m.geo_json(geo_path=path,
                   fill_color='none', line_color='Orange')
    if secoora_stations:
        for x, y, name in zip(df['lon'], df['lat'], df['ID']):
            if not np.isnan(x) and not np.isnan(y):
                location = y, x
                popup = '<b>{}</b>'.format(name)
                kw = dict(radius=500, fill_color='#3186cc', popup=popup,
                          fill_opacity=0.2)
                m.circle_marker(location=location, **kw)
    return m


def inline_map(m):
    """Takes a folium instance or a html path and load into an iframe."""
    if isinstance(m, Map):
        m._build_map()
        srcdoc = m.HTML.replace('"', '&quot;')
        embed = HTML('<iframe srcdoc="{srcdoc}" '
                     'style="width: 100%; height: 500px; '
                     'border: none"></iframe>'.format(srcdoc=srcdoc))
    elif isinstance(m, str):
        embed = IFrame(m, width=750, height=500)
    return embed


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


# Misc.
@contextmanager
def timeit(log=None):
    t = time.time()
    yield
    elapsed = time.strftime("%H:%M:%S", time.gmtime(time.time()-t))
    if log:
        log.info(elapsed)
    else:
        print(elapsed)


@contextmanager
def time_limit(seconds=10):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


class TimeoutException(Exception):
    """
    Example
    -------
    >>> def long_function_call():
    >>>     import time
    >>>     sec = 0
    >>>>    while True:
    >>>         sec += 1
    >>>         print(sec)
    >>>         time.sleep(1)
    >>>
    >>> try:
    >>>     with time_limit(10):
    >>>     long_function_call()
    >>> except TimeoutException as msg:
    >>>     print("Timed out!")
    """
    pass
