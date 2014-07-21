# Scientific stack.
import iris
import numpy as np
import numpy.ma as ma
from netCDF4 import Dataset, num2date, date2index
from iris.exceptions import CoordinateNotFoundError


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


def time_near(cube, start):
    timevar = find_timevar(cube)
    try:
        time = timevar.units.date2num(start)
        itime = timevar.nearest_neighbour_index(time)
    except IndexError:
        itime = -1
    return timevar.points[itime]


def find_timevar(cube):
    """Return the time variable from Iris."""
    try:
        cube.coord(axis='T').rename('time')
    except CoordinateNotFoundError:
        pass
    timevar = cube.coord('time')
    return timevar


def get_hfradar(url, time_slice, n=3):
    u = iris.load_cube(url, 'surface_eastward_sea_water_velocity')
    v = iris.load_cube(url, 'surface_northward_sea_water_velocity')

    lon = v.coord(axis='X').points[::n]
    lat = v.coord(axis='Y').points[::n]

    uslice = u.extract(iris.Constraint(time=time_near(u, time_slice)))
    vslice = v.extract(iris.Constraint(time=time_near(v, time_slice)))
    u = uslice.data[::n, ::n]
    v = vslice.data[::n, ::n]

    time = uslice.coord('time')
    time = time.units.num2date(time.points[0])

    if (lon.ndim == 1) and (lat.ndim == 1):
        lon, lat = np.meshgrid(lon, lat)
    # FIXME: return iris cube instead.
    return dict(lon=lon, lat=lat, u=u, v=v, time=time)


def get_roms(url, time_slice, n=3):
    """ FIXME: Re-write this using iris."""
    with Dataset(url) as nc:
        ncv = nc.variables
        time = ncv['ocean_time']
        tidx = date2index(time_slice, time, select='nearest')
        time = num2date(time[tidx], time.units, time.calendar)

        mask = ncv['mask_rho'][:]
        lon_rho = ncv['lon_rho'][:]
        lat_rho = ncv['lat_rho'][:]
        anglev = ncv['angle'][:]

        u = ncv['u'][tidx, -1, :, :]
        v = ncv['v'][tidx, -1, :, :]

        u = shrink(u, mask[1:-1, 1:-1].shape)
        v = shrink(v, mask[1:-1, 1:-1].shape)

        u, v = rot2d(u, v, anglev[1:-1, 1:-1])

        lon = lon_rho[1:-1, 1:-1]
        lat = lat_rho[1:-1, 1:-1]

        u, v = u[::n, ::n], v[::n, ::n]
        lon, lat = lon[::n, ::n], lat[::n, ::n]

        u = ma.masked_invalid(u)
        v = ma.masked_invalid(v)
    # FIXME: return iris cube instead.
    return dict(lon=lon, lat=lat, u=u, v=v, time=time)
