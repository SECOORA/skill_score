# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# ### Downloads HF-radar and model data for the same region at the same time

# <codecell>

# Standard Library.
from datetime import datetime, timedelta

# Scientific stack.
import iris
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
from netCDF4 import Dataset, num2date, date2index

import mplleaflet

import cartopy.crs as ccrs
from cartopy.io.img_tiles import MapQuestOpenAerial

# Custom IOOS/ASA modules (available at PyPI).

# Local imports.
from utilities import time_near, shrink, rot2d

# <codecell>

def get_hfradar(url, time_slice, n=3):
    u = iris.load_cube(radar_url, 'surface_eastward_sea_water_velocity')
    v = iris.load_cube(radar_url, 'surface_northward_sea_water_velocity')

    lon = v.coord(axis='X').points[::n]
    lat = v.coord(axis='Y').points[::n]

    uslice = u.extract(iris.Constraint(time=time_near(u, time_slice)))
    vslice = v.extract(iris.Constraint(time=time_near(v, time_slice)))
    u = uslice.data[::n, ::n]
    v = vslice.data[::n, ::n]

    time = uslice.coord('time')
    time = time.units.num2date(time.points[0])
    
    lon, lat = np.meshgrid(lon, lat)

    return dict(lon=lon, lat=lat, u=u, v=v, time=time)

# <codecell>

def get_roms(url, time_slice, n=3):
    """FIXME: Re-write this using iris."""
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
        return dict(lon=lon, lat=lat, u=u, v=v, time=time)

# <codecell>

# Six hours ago...
time_slice = datetime.utcnow() - timedelta(hours=6)

# <codecell>

# HF radar.
radar_url = 'http://hfrnet.ucsd.edu/'
radar_url += 'thredds/dodsC/HFRNet/USEGC/6km/hourly/RTV'

radar = get_hfradar(radar_url, time_slice, n=6)

# <codecell>

# SABGOM model.
model_url = 'http://omgsrv1.meas.ncsu.edu:8080/thredds/dodsC/fmrc/sabgom/'
model_url += 'SABGOM_Forecast_Model_Run_Collection_best.ncd'

model = get_roms(model_url, time_slice, n=6)

# <markdowncell>

# # Cartopy

# <codecell>

extent = [-87.4, -74.7, 24.25, 36.70]  # SECOORA: NC, SC GA, FL

tiler = MapQuestOpenAerial()
geodetic = ccrs.Geodetic(globe=ccrs.Globe(datum='WGS84'))

fig, ax = plt.subplots(figsize=(8, 8),
                       subplot_kw=dict(projection=tiler.crs))

ax.set_extent(extent, geodetic)
ax.add_image(tiler, 5)

kw = dict(scale=20, headwidth=2, transform=ccrs.PlateCarree())
Qm = ax.quiver(model['lon'], model['lat'], model['u'], model['v'],
               color='red', **kw)
Qr = ax.quiver(radar['lon'], radar['lat'], radar['u'], radar['v'],
               color='white', **kw)

scale_vector = 1.0
maxstr = '%3.1f m/s' % scale_vector
kw = dict(transform=ccrs.PlateCarree(), color='white',
          labelpos='W', labelcolor='white')
qk = ax.quiverkey(Qr, 0.15, 0.85, scale_vector, maxstr, **kw)


gl = ax.gridlines(draw_labels=True)
gl.xlabels_top = gl.ylabels_right = False

US_format = '%Y/%m/%d %H:%M%Z'
date1 = radar['time'].strftime(US_format)
date2 = model['time'].strftime(US_format)
_ = ax.set_title('HFR 6km Velocity at %s\nModel Velocity at %s' %
                 (date1, date2))

# <markdowncell>

# # mplleaflet

# <codecell>

fig, ax = plt.subplots()
kw = dict(scale=20, headwidth=2)

# No masked array support!
mask = ~radar['u'].mask

Q = ax.quiver(radar['lon'][mask], radar['lat'][mask],
              radar['u'][mask], radar['v'][mask], color='black', **kw)

mask = ~model['u'].mask

Q = ax.quiver(model['lon'][mask], model['lat'][mask],
              model['u'][mask], model['v'][mask], color='red', **kw)

mplleaflet.display(fig=ax.figure)

