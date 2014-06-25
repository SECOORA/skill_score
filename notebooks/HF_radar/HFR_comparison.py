# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import matplotlib.pyplot as plt
from datetime import datetime, timedelta

import iris
import cartopy.crs as ccrs
from iris.exceptions import CoordinateNotFoundError
from cartopy.io.img_tiles import MapQuestOpenAerial

# <codecell>


def find_timevar(cube):
    """Return the time variable from Iris."""
    try:
        cube.coord(axis='T').rename('time')
    except CoordinateNotFoundError:
        pass
    timevar = cube.coord('time')
    return timevar


def time_near(cube, start):
    timevar = find_timevar(cube)
    try:
        time = timevar.units.date2num(start)
        itime = timevar.nearest_neighbour_index(time)
    except IndexError:
        itime = -1
    return timevar.points[itime]

# <codecell>

uri = 'http://hfrnet.ucsd.edu/thredds/dodsC/HFRNet'
# url = '%s/USWC/6km/hourly/RTV' % uri
url = '%s/USEGC/6km/hourly/RTV' % uri

# <codecell>

extent = [-87.4, -74.7, 24.25, 36.70]  # SECOORA: NC, SC GA, FL
mytime = datetime.utcnow() - timedelta(hours=6)

# <codecell>

u = iris.load_cube(url, 'surface_eastward_sea_water_velocity')
v = iris.load_cube(url, 'surface_northward_sea_water_velocity')

# <codecell>

lon = v.coord(axis='X').points
lat = v.coord(axis='Y').points

# <codecell>

uslice = u.extract(iris.Constraint(time=time_near(u, mytime)))
vslice = v.extract(iris.Constraint(time=time_near(v, mytime)))

# <codecell>

U = uslice.data
V = vslice.data

# <codecell>

tiler = MapQuestOpenAerial()
geodetic = ccrs.Geodetic(globe=ccrs.Globe(datum='WGS84'))

fig, ax = plt.subplots(figsize=(12, 12),
                       subplot_kw=dict(projection=tiler.crs))

ax.set_extent(extent, geodetic)
ax.add_image(tiler, 5)

n = 3  # Subsample interval for thinning arrows.
kw = dict(scale=20, headwidth=2, transform=ccrs.PlateCarree(), color='white')
Q = ax.quiver(lon[::n], lat[::n], U[::n, ::n], V[::n, ::n], **kw)
gl = ax.gridlines(draw_labels=True)
gl.xlabels_top = gl.ylabels_right = False

scale_vector = 1.0
maxstr = '%3.1f m/s' % scale_vector
kw = dict(transform=ccrs.PlateCarree(), color='white',
          labelpos='W', labelcolor='white')
qk = ax.quiverkey(Q, 0.15, 0.85, scale_vector, maxstr, **kw)

time = uslice.coord('time')
UTC_format = '%H%M%Z %d/%m/%Y'
US_format = '%Y/%m/%d %H:%M%Z'
date_str = time.units.num2date(time.points[0]).strftime(US_format)
ax.set_title('HFR 6km Velocity at %s' % date_str)

