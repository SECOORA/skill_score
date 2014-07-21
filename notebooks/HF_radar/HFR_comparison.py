# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# ## HF-radar and model data

# <codecell>

# Standard Library.
from datetime import datetime, timedelta

# Scientific stack.
import mplleaflet
import numpy as np
from iris.unit import Unit
import matplotlib.pyplot as plt

# Local imports.
from utilities import get_roms, get_cubes

# <markdowncell>

# ### When and where

# <codecell>

bbox = [[-87.4, 24.25],
        [-74.7, 36.70]]  # SECOORA: NC, SC GA, FL

time = datetime.utcnow() - timedelta(hours=6)

# <markdowncell>

# ### HF radar

# <codecell>

url = 'http://hfrnet.ucsd.edu/thredds/dodsC/HFRNet/USEGC/6km/hourly/RTV'

u_name_list = ['x_sea_water_velocity',
               'sea_water_x_velocity',
               'eastward_sea_water_velocity',
               'surface_eastward_sea_water_velocity']

v_name_list = ['y_sea_water_velocity',
               'sea_water_y_velocity',
               'northward_sea_water_velocity',
               'surface_northward_sea_water_velocity']

cubes = get_cubes(url, name_list=u_name_list+v_name_list,
                  time=time, bbox=bbox)

for cube in cubes:
    if not cube.units == Unit('m s-1'):
        cube.convert_units('m s-1')

print(cubes)

# <codecell>

# This is just for plotting.  If using cartopy do not
# subsample.  Use cartopy's resample instead.


def subsample_cubes(cubes, n=6):
    u = cubes[0][::n, ::n]
    v = cubes[0][::n, ::n]
    lon = u.coord(axis='X').points
    lat = u.coord(axis='Y').points
    if (lon.ndim == 1) and (lat.ndim == 1):
        lon, lat = np.meshgrid(lon, lat)
    time = u.coord('time')
    time.units.num2date(time.points)
    return dict(lon=lon, lat=lat, u=u.data, v=v.data, time=time)

hf_radar = subsample_cubes(cubes, n=6)

# <markdowncell>

# ### SABGOM model

# <codecell>

model_url = 'http://omgsrv1.meas.ncsu.edu:8080/thredds/dodsC/fmrc/sabgom/'
model_url += 'SABGOM_Forecast_Model_Run_Collection_best.ncd'

model = get_roms(model_url, time, n=6)

# <codecell>

fig, ax = plt.subplots()
kw = dict(scale=20, headwidth=2)

# NOTE: mplleaflet does not support masked array.
mask = ~hf_radar['u'].mask

Q = ax.quiver(hf_radar['lon'][mask], hf_radar['lat'][mask],
              hf_radar['u'][mask], hf_radar['v'][mask], color='black', **kw)

mask = ~model['u'].mask

Q = ax.quiver(model['lon'][mask], model['lat'][mask],
              model['u'][mask], model['v'][mask], color='red', **kw)

mplleaflet.display(fig=ax.figure)

