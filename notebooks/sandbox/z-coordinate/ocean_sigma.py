# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# https://github.com/ocefpaf/secoora/issues/2

# <codecell>

import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt

import iris
import iris.plot as iplt
import iris.quickplot as qplt

print(iris.__version__)  # ocean_sigma_coordinate branch

# url = "http://opendap.co-ops.nos.noaa.gov/thredds/dodsC/NYOFS/fmrc/Aggregated_7_day_NYOFS_Fields_Forecast_best.ncd"
cube = iris.load_cube('./data/ocean_sigma.nc', 'upward_sea_water_velocity')

print(cube)

# <codecell>

z = cube.coords(axis='Z')
print(len(z))

# <codecell>

z[0]

# <codecell>

z[1].standard_name, z[1].units

# <codecell>

eta = cube.aux_coords[1].points
sigma = z[0].points
depth = cube.aux_coords[2].points

eta.shape, sigma.shape, depth.shape

# <codecell>

zz = eta + sigma[:, None, None] * (depth + eta)

# <codecell>

(ma.masked_invalid(z[1].points) == ma.masked_invalid(zz)).all()

# <codecell>

c = cube[0, :, 20, 60]

name = ' '.join(c.standard_name.split('_'))
unit = c.units
lon = c.coord(axis='X').points[0]
lat = c.coord(axis='Y').points[0]

title = r'%s in %s $\times 10^{-3}$ at: lon = %s, lat = %s' % (name, unit, lon, lat)

iplt.plot(c * 1e3, c.coord('sea_surface_height_above_reference_ellipsoid'))
plt.title(title)

