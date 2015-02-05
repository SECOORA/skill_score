# -*- coding: utf-8 -*-
#
# iris_utils.py
#
# purpose:  Some iris tricks to load/slice data
# author:   Filipe P. A. Fernandes
# e-mail:   ocefpaf@gmail
# web:      http://ocefpaf.github.io/
# created:  04-Feb-2015
# modified: Thu 05 Feb 2015 04:47:58 PM BRT
#
# obs:
#

# Standard library.
from datetime import datetime

# Scientific.
import numpy as np
import numpy.ma as ma
from scipy.spatial import cKDTree as KDTree

import iris
from iris import Constraint
from iris.cube import CubeList
from iris.pandas import as_cube
from iris.exceptions import CoordinateNotFoundError, CoordinateMultiDimError

iris.FUTURE.netcdf_promote = True
iris.FUTURE.cell_datetime_objects = True

from pyugrid import UGrid
from oceans import wrap_lon180


__all__ = ['z_coord',
           'get_surface',
           'time_coord',
           'time_near',
           'time_slice',
           'time_constraint',
           'bbox_extract_2Dcoords',
           'bbox_extract_1Dcoords',
           'subset',
           'get_cubes',
           'add_mesh',
           'standardize_fill_value',
           'make_aux_coord',
           'ensure_timeseries',
           'add_station',
           'remove_ssh',
           'save_timeseries',
           'make_tree',
           'get_nearest_water']


def z_coord(cube):
    """Heuristic way to return **one** the vertical coordinate."""
    water_level = ['sea_surface_height',
                   'sea_surface_elevation',
                   'sea_surface_height_above_geoid',
                   'sea_surface_height_above_sea_level',
                   'water_surface_height_above_reference_datum',
                   'sea_surface_height_above_reference_ellipsoid']
    try:
        z = cube.coord(axis='Z')
    except CoordinateNotFoundError:
        z = None
        for coord in cube.coords(axis='Z'):
            if coord.name() not in water_level:
                z = coord
    return z


def get_surface(cube):
    """Work around `iris.cube.Cube.slices` error:
    The requested coordinates are not orthogonal."""
    z = z_coord(cube)
    if z:
        positive = z.attributes.get('positive', None)
        if positive == 'up':
            idx = np.unique(z.points.argmax(axis=0))[0]
        else:
            idx = np.unique(z.points.argmin(axis=0))[0]
        return cube[:, idx, ...]
    else:
        return cube


def time_coord(cube):
    """Return the variable attached to time axis and rename it to time."""
    try:
        cube.coord(axis='T').rename('time')
    except CoordinateNotFoundError:
        pass
    timevar = cube.coord('time')
    return timevar


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
    """Slice time by indexes using a nearest criteria.
    NOTE: Assumes time is the first dimension!"""
    istart = time_near(cube, start)
    if stop:
        istop = time_near(cube, stop)
        if istart == istop:
            raise ValueError('istart must be different from istop! '
                             'Got istart {!r} and '
                             ' istop {!r}'.format(istart, istop))
        return cube[istart:istop, ...]
    else:
        return cube[istart, ...]


def time_constraint(cube, start, stop):
    """Slice time by constraint."""
    begin = lambda cell: cell >= start
    end = lambda cell: cell <= stop
    constraint = Constraint(begin & end)
    return cube.extract(constraint)


def _minmax(v):
    return np.min(v), np.max(v)


def _get_indices(cube, bbox):
    lons = cube.coord('longitude').points
    lats = cube.coord('latitude').points
    lons = wrap_lon180(lons)

    inregion = np.logical_and(np.logical_and(lons > bbox[0],
                                             lons < bbox[2]),
                              np.logical_and(lats > bbox[1],
                                             lats < bbox[3]))
    region_inds = np.where(inregion)
    imin, imax = _minmax(region_inds[0])
    jmin, jmax = _minmax(region_inds[1])
    return imin, imax+1, jmin, jmax+1


def bbox_extract_2Dcoords(cube, bbox):
    """Extract a sub-set of a cube inside a lon, lat bounding box
    bbox=[lon_min lon_max lat_min lat_max].
    NOTE: This is a work around too subset an iris cube that has
    2D lon, lat coords."""
    imin, imax, jmin, jmax = _get_indices(cube, bbox)
    return cube[..., imin:imax, jmin:jmax]


def bbox_extract_1Dcoords(cube, bbox):
    lat = Constraint(latitude=lambda cell: bbox[1] <= cell < bbox[3])
    lon = Constraint(longitude=lambda cell: bbox[0] <= cell <= bbox[2])
    cube = cube.extract(lon & lat)
    return cube


def subset(cube, bbox):
    """Sub sets cube with 1D or 2D lon, lat coords.
    Using `intersection` instead of `extract` we deal with 0--360
    longitudes automagically."""
    if (cube.coord(axis='X').ndim == 1 and cube.coord(axis='Y').ndim == 1):
        # Workaround `cube.intersection` hanging up on FVCOM models.
        title = cube.attributes.get('title', None)
        featureType = cube.attributes.get('featureType', None)
        if (('FVCOM' in title) or ('ESTOFS' in title) or
           featureType == 'timeSeries'):
            cube = bbox_extract_1Dcoords(cube, bbox)
        else:
            cube = cube.intersection(longitude=(bbox[0], bbox[2]),
                                     latitude=(bbox[1], bbox[3]))
    elif (cube.coord(axis='X').ndim == 2 and
          cube.coord(axis='Y').ndim == 2):
        cube = bbox_extract_2Dcoords(cube, bbox)
    else:
        msg = "Cannot deal with X:{!r} and Y:{!r} dimensions."
        raise CoordinateMultiDimError(msg.format(cube.coord(axis='X').ndim),
                                      cube.coord(axis='y').ndim)
    return cube


def get_cubes(url, name_list, bbox=None, time=None, units=None, callback=None,
              constraint=None):
    """Some station return more than one cube.  That is why I modified
    `get_cube` to return a `Cubelist` instead.  Note that the cubes seems to be
    duplicate sensors and/or sensors at different depths.
    TODO: Create a criteria to choose a sensor.
    buoy = "http://129.252.139.124/thredds/dodsC/fldep.stlucieinlet..nc"
    buoy = "http://129.252.139.124/thredds/dodsC/lbhmc.cherrygrove.pier.nc"
    """

    cubes = iris.load_raw(url, callback=callback)

    in_list = lambda cube: cube.standard_name in name_list
    cubes = CubeList([cube for cube in cubes if in_list(cube)])

    if not cubes:
        raise ValueError('Cube does not contain {!r}'.format(name_list))

    if constraint:
        cubes = cubes.extract(constraint)
        if not cube:
            raise ValueError('No cube using {!r}'.format(constraint))
    if bbox:
        cubes = [subset(cube, bbox) for cube in cubes]
        if not cubes:
            raise ValueError('No cube using {!r}'.format(bbox))
    if time:
        if isinstance(time, datetime):
            start, stop = time, None
        elif isinstance(time, tuple):
            start, stop = time[0], time[1]
        else:
            raise ValueError('Time must be start or (start, stop).'
                             '  Got {!r}'.format(time))
        cubes = [time_slice(cube, start, stop) for cube in cubes]
    if units:
        for cube in cubes:
            if cube.units != units:
                cube.convert_units(units)
    return cubes


def add_mesh(cube, url):
    """Soon in an iris near you!"""
    ug = UGrid.from_ncfile(url)
    cube.mesh = ug
    cube.mesh_dimension = 1
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


def remove_ssh(cube):
    """
    Remove all `aux_coords` but time.  Should that has the same shape as
    the data.  NOTE: This also removes `aux_factories` to avoid update error
    when removing the coordinate."""
    for factory in cube.aux_factories:
        cube.remove_aux_factory(factory)
    for coord in cube.aux_coords:
        if coord.shape == cube.shape:
            if 'time' not in coord.name():
                cube.remove_coord(coord.name())
    return cube


def save_timeseries(df, outfile, standard_name, **kw):
    """http://cfconventions.org/Data/cf-convetions/cf-conventions-1.6/build
    /cf-conventions.html#idp5577536"""
    cube = as_cube(df, calendars={1: iris.unit.CALENDAR_GREGORIAN})
    cube.coord("index").rename("time")
    cube.coord("columns").rename("station name")
    cube.rename(standard_name)

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


def make_tree(cube):
    """Create KDTree."""
    lon = cube.coord(axis='X').points
    lat = cube.coord(axis='Y').points
    # Structured models with 1D lon, lat.
    if (lon.ndim == 1) and (lat.ndim == 1) and (cube.ndim == 3):
        lon, lat = np.meshgrid(lon, lat)
    # Unstructure are already paired!
    tree = KDTree(zip(lon.ravel(), lat.ravel()))
    return tree, lon, lat


def get_nearest_water(cube, tree, xi, yi, k=10, max_dist=0.04, min_var=0.01):
    """Find `k` nearest model data points from an iris `cube` at station
    lon: `xi`, lat: `yi` up to `max_dist` in degrees.  Must provide a Scipy's
    KDTree `tree`."""
    # TODO: Use rtree instead of KDTree.
    # NOTE: Based on the iris `_nearest_neighbour_indices_ndcoords`.

    distances, indices = tree.query(np.array([xi, yi]).T, k=k)
    if indices.size == 0:
        raise ValueError("No data found.")
    # Get data up to specified distance.
    mask = distances <= max_dist
    distances, indices = distances[mask], indices[mask]
    if distances.size == 0:
        msg = "No data near ({}, {}) max_dist={}.".format
        raise ValueError(msg(xi, yi, max_dist))
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
        # This weird syntax allow for idx to be len 1 or 2.
        series = cube[(slice(None),)+idx]
        # Accounting for wet-and-dry models.
        arr = ma.masked_invalid(series.data).filled(fill_value=0)
        if arr.std() <= min_var:
            series = None
            break
    return series, dist, idx


def var_lev_date(url=None, var=None, mytime=None, lev=0, subsample=1,
                 bbox=None):
    """
    @rsignell-usgs function from:
    http://nbviewer.ipython.org/gist/rsignell-usgs/2e04b3e732ac1728400f

    Specify lev=None if the variable does not have layers.
    @ocefpaf: Right now get_cubes does all but the level slice.
    For now I use `get_surface` to find the first layer.  But I want to modify
    it to find an arbitrary layer at a given depth.
    """

    import time

    time0 = time.time()
    cube = iris.load_cube(url, var)

    try:
        cube.coord(axis='T').rename('time')
    except Exception as e:
        print(e)  # NOTE: Never pass exceptions silently!
        pass
    sliced = cube.extract(iris.Constraint(time=time_near(cube, mytime)))

    if bbox is None:
        imin, jmin = 0, 0
        imax, jmax = -2, -2  # NOTE: Hard-coded corners...
    else:
        imin, imax, jmin, jmax = _get_indices(cube, bbox)
    if lev is None:
        sliced = sliced[jmin:jmax:subsample, imin:imax:subsample]
    else:
        sliced = sliced[lev, jmin:jmax:subsample, imin:imax:subsample]
    print('Slice retrieved in %f seconds' % (time.time() - time0))
    return sliced
