
# coding: utf-8

# In[1]:

import warnings
warnings.filterwarnings("ignore")

import iris
from iris.unit import Unit
from iris.cube import CubeList
from iris.exceptions import CoordinateNotFoundError, CoordinateMultiDimError

from pyugrid import UGrid
from oceans import wrap_lon180

iris.FUTURE.netcdf_promote = True
iris.FUTURE.cell_datetime_objects = True  # <- TODO!


def time_coord(cube):
    """Return the variable attached to time axis and rename it to time."""
    try:
        cube.coord(axis='T').rename('time')
    except CoordinateNotFoundError:
        pass
    timevar = cube.coord('time')
    return timevar


def z_coord(cube):
    """Heuristic way to return the
    dimensionless vertical coordinate."""
    try:
        z = cube.coord(axis='Z')
    except CoordinateNotFoundError:
        z = cube.coords(axis='Z')
        for coord in cube.coords(axis='Z'):
            if coord.ndim == 1:
                z = coord
    return z


def time_near(cube, datetime):
    """Return the nearest index to a `datetime`."""
    timevar = time_coord(cube)
    try:
        time = timevar.units.date2num(datetime)
        idx = timevar.nearest_neighbour_index(time)
    except IndexError:
        idx = -1
    return idx


def time_slice(cube, start, stop=None):
    """TODO: Re-write to use `iris.FUTURE.cell_datetime_objects`."""
    istart = time_near(cube, start)
    if stop:
        istop = time_near(cube, stop)
        if istart == istop:
            raise ValueError('istart must be different from istop!'
                             'Got istart {!r} and '
                             ' istop {!r}'.format(istart, istop))
        return cube[istart:istop, ...]
    else:
        return cube[istart, ...]


def minmax(v):
    return np.min(v), np.max(v)


def bbox_extract_2Dcoords(cube, bbox):
    """Extract a sub-set of a cube inside a lon, lat bounding box
    bbox=[lon_min lon_max lat_min lat_max].
    NOTE: This is a work around too subset an iris cube that has
    2D lon, lat coords."""
    lons = cube.coord('longitude').points
    lats = cube.coord('latitude').points
    lons = wrap_lon180(lons)

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
    if (cube.coord(axis='X').ndim == 1 and
        cube.coord(axis='Y').ndim == 1):
        method = "Using iris `cube.intersection`"
        cube = cube.intersection(longitude=(bbox[0], bbox[2]),
                                 latitude=(bbox[1], bbox[3]))
    elif (cube.coord(axis='X').ndim == 2 and
          cube.coord(axis='Y').ndim == 2):
        method = "Using iris `bbox_extract_2Dcoords`"
        cube = bbox_extract_2Dcoords(cube, bbox)
    else:
        msg = "Cannot deal with X:{!r} and Y:{!r} dimensions"
        raise CoordinateMultiDimError(msg.format(cube.coord(axis='X').ndim),
                                      cube.coord(axis='y').ndim)
    print(method)
    return cube


def get_cube(url, name_list=None, bbox=None, callback=None,
             time=None, units=None, constraint=None):
    cubes = iris.load_raw(url, callback=callback)
    if constraint:
        cubes = cubes.extract(constraint)
    if name_list:
        in_list = lambda cube: cube.standard_name in name_list
        cubes = CubeList([cube for cube in cubes if in_list(cube)])
        if not cubes:
            raise ValueError('Cube does not contain {!r}'.format(name_list))
        else:
            cube = cubes.merge_cube()
    if bbox:
        cube = intersection(cube, bbox)
    if time:
        if isinstance(time, datetime):
            start, stop = time, None
        elif isinstance(time, tuple):
            start, stop = time[0], time[1]
        else:
            raise ValueError('Time must be start or (start, stop).'
                             '  Got {!r}'.format(time))
        cube = time_slice(cube, start, stop)
    if units:
        if not cube.units == units:
            cube.convert_units(units)
    return cube


def add_mesh(cube, url):
    """Soon in an iris near you!"""
    ug = UGrid.from_ncfile(url)
    cube.mesh = ug
    cube.mesh_dimension = 1
    return cube


def get_bbox(cube):
    xmin = cube.coord(axis='X').points.min()
    xmax = cube.coord(axis='X').points.max()
    ymin = cube.coord(axis='Y').points.min()
    ymax = cube.coord(axis='Y').points.max()
    return [xmin, xmax, ymin, ymax]


# In[2]:

get_ipython().magic('matplotlib inline')
import numpy as np
import numpy.ma as ma

from scipy.spatial import Delaunay

import matplotlib.tri as tri
import matplotlib.pyplot as plt

import cartopy.crs as ccrs
from cartopy.feature import NaturalEarthFeature, COLORS
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

LAND = NaturalEarthFeature('physical', 'land', '10m',
                           edgecolor='face', facecolor=COLORS['land'])


def plot_surface(cube, model='', unstructure=False, **kw):
    projection = kw.pop('projection', ccrs.PlateCarree())
    figsize = kw.pop('figsize', (8, 6))
    cmap = kw.pop('cmap', plt.cm.rainbow)

    fig, ax = plt.subplots(figsize=figsize,
                           subplot_kw=dict(projection=projection))
    ax.set_extent(get_bbox(cube))
    ax.add_feature(LAND)
    ax.coastlines(resolution='10m')
    gl = ax.gridlines(draw_labels=True)
    gl.xlabels_top = gl.ylabels_right = False
    gl.xformatter = LONGITUDE_FORMATTER
    gl.yformatter = LATITUDE_FORMATTER

    z = z_coord(cube)
    if z:
        positive = z.attributes.get('positive', None)
        if positive == 'up':
            idx = np.argmax(z.points)
        else:
            idx = np.argmin(z.points)
        c = cube[idx, ...].copy()
    else:
        idx = None
        c = cube.copy()
    c.data = ma.masked_invalid(c.data)
    t = time_coord(cube)
    t = t.units.num2date(t.points)[0]
    if unstructure:
        #  The following lines would work if the cube is note bbox-sliced.
        # lon = cube.mesh.nodes[:, 0]
        # lat = cube.mesh.nodes[:, 1]
        # nv = cube.mesh.faces
        lon = cube.coord(axis='X').points
        lat = cube.coord(axis='Y').points
        nv = Delaunay(np.c_[lon, lat]).vertices
        triang = tri.Triangulation(lon, lat, triangles=nv)
        # http://matplotlib.org/examples/pylab_examples/
        # tricontour_smooth_delaunay.html
        if False:
            subdiv = 3
            min_circle_ratio = 0.01
            mask = tri.TriAnalyzer(triang).get_flat_tri_mask(min_circle_ratio)
            triang.set_mask(mask)
            refiner = tri.UniformTriRefiner(triang)
            tri_ref, data_ref = refiner.refine_field(cube.data, subdiv=subdiv)
        cs = ax.tricontourf(triang, c.data, cmap=cmap, **kw)
    else:
        cs = ax.pcolormesh(c.coord(axis='X').points,
                           c.coord(axis='Y').points,
                           c.data, cmap=cmap, **kw)
    title = (model, t, c.name(), idx)
    ax.set_title('{}: {}\nVariable: {} level: {}'.format(*title))
    return fig, ax, cs


# In[3]:

import time
import contextlib


@contextlib.contextmanager
def timeit(log=None):
    t = time.time()
    yield
    elapsed = time.strftime("%H:%M:%S", time.gmtime(time.time()-t))
    if log:
        log.info(elapsed)
    else:
        print(elapsed)


# In[4]:

from datetime import datetime, timedelta

start = datetime.utcnow() - timedelta(days=7)
stop = datetime.utcnow()

# name_list = ['sea_water_potential_temperature', 'sea_water_temperature']
name_list = ['water level',
             'sea_surface_height',
             'sea_surface_elevation',
             'sea_surface_height_above_geoid',
             'sea_surface_height_above_sea_level',
             'water_surface_height_above_reference_datum',
             'sea_surface_height_above_reference_ellipsoid']

bbox = [-76.4751, 38.3890, -71.7432, 42.9397]

# units = Unit('Kelvin')
units = Unit('m')


# In[5]:

model = 'MARACOOS/ESPRESSO'
url = 'http://tds.marine.rutgers.edu/thredds/dodsC/roms/espresso/2009_da/his'

with timeit():
    cube = get_cube(url, name_list=name_list, bbox=bbox,
                    time=start, units=units)

fig, ax, cs = plot_surface(cube, model)
cbar = fig.colorbar(cs, extend='both', shrink=0.75)
t = cbar.ax.set_title(cube.units)


# In[6]:

model = 'USGS/COAWST'
url = 'http://geoport.whoi.edu/thredds/dodsC/coawst_4/use/fmrc/'
url += 'coawst_4_use_best.ncd'

with timeit():
    cube = get_cube(url, name_list=name_list, bbox=bbox,
                    time=start, units=units)

fig, ax, cs = plot_surface(cube, model)
cbar = fig.colorbar(cs, extend='both', shrink=0.75)
t = cbar.ax.set_title(cube.units)


# In[7]:

model = 'HYCOM'
url = 'http://ecowatch.ncddc.noaa.gov/thredds/dodsC/hycom/hycom_reg1_agg/'
url += 'HYCOM_Region_1_Aggregation_best.ncd'


def callback(cube, field, filename):
    if cube.name() == "Water Surface Elevation":
        cube.standard_name = 'sea_surface_elevation'
    return cube


with timeit():
    cube = get_cube(url, name_list=name_list, bbox=bbox,
                    time=start, units=units, callback=callback)

fig, ax, cs = plot_surface(cube, model)
cbar = fig.colorbar(cs, extend='both', shrink=0.75)
t = cbar.ax.set_title(cube.units)


# In[8]:

model = 'NYHOP'
url = 'http://colossus.dl.stevens-tech.edu/thredds/dodsC/fmrc/NYBight/'
url += 'NYHOPS_Forecast_Collection_for_the_New_York_Bight_best.ncd'

with timeit():
    cube = get_cube(url, name_list=name_list, bbox=bbox,
                    time=start, units=units)

fig, ax, cs = plot_surface(cube, model)
cbar = fig.colorbar(cs, extend='both', shrink=0.75)
t = cbar.ax.set_title(cube.units)


# In[9]:

model = 'RUTGERS/NWA'
url = 'http://oceanus.esm.rutgers.edu:8090/thredds/dodsC/ROMS/NWA/Run03/Output'


def callback(cube, field, filename):
    if cube.name() == "time-averaged free-surface":
        cube.standard_name = 'sea_surface_elevation'
    return cube


with timeit():
    cube = get_cube(url, name_list=name_list, bbox=bbox,
                    time=start, units=units, callback=callback)

fig, ax, cs = plot_surface(cube, model)
cbar = fig.colorbar(cs, extend='both', shrink=0.75)
t = cbar.ax.set_title(cube.units)


# In[30]:

model = 'SELFE'
url = 'http://comt.sura.org/thredds/dodsC/data/comt_1_archive/'
url += 'inundation_tropical/VIMS_SELFE/Hurricane_Ike_2D_final_run_with_waves'


def cube_func(cube):
    A = cube.standard_name in name_list
    B = not any(m.method == 'maximum' for m in cube.cell_methods)
    return A and B


constraint = iris.Constraint(cube_func=cube_func)

with timeit():
    cube = get_cube(url, name_list=name_list, bbox=bbox,
                    time=start, units=units, constraint=constraint)

cube = add_mesh(cube, url)
fig, ax, cs = plot_surface(cube, model, unstructure=True)
cbar = fig.colorbar(cs, extend='both', shrink=0.75)
t = cbar.ax.set_title(cube.units)


# In[45]:

model = 'FVCOM/NECOFS'
url = 'http://www.smast.umassd.edu:8080/thredds/dodsC/FVCOM/NECOFS/Forecasts/'
url += 'NECOFS_GOM3_FORECAST.nc'

with timeit():
    cube = get_cube(url, name_list=name_list, bbox=bbox,
                    time=start, units=units)

cube = add_mesh(cube, url)
fig, ax, cs = plot_surface(cube, model, unstructure=True)
cbar = fig.colorbar(cs, extend='both', shrink=0.75)
t = cbar.ax.set_title(cube.units)

