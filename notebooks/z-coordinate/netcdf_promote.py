# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# https://github.com/SciTools/iris/pull/1070
# https://github.com/SciTools/iris/pull/1159

# <codecell>

import iris
print(iris.__version__)  # remotes/origin/netcdf_promote 7b8b109

# <codecell>

url = 'http://geoport.whoi.edu/thredds/dodsC/coawst_4/use/fmrc/coawst_4_use_best.ncd'

# <codecell>

cube = iris.load_cube(url, 'water_surface_height_above_reference_datum')
print(cube)

# <codecell>

with iris.FUTURE.context(netcdf_promote=True):
    cube = iris.load_cube(url, 'water_surface_height_above_reference_datum')
    print(cube)

# <codecell>

url = 'http://geoport.whoi.edu/thredds/dodsC/coawst_4/use/fmrc/coawst_4_use_best.ncd'
with iris.FUTURE.context(netcdf_promote=True):
    cube = iris.load_cube(url, 'free-surface')
    print(cube)

# <codecell>

url = 'http://fvcom.smast.umassd.edu:8080/thredds/dodsC/FVCOM/NECOFS/Forecasts/NECOFS_GOM3_FORECAST.nc'
with iris.FUTURE.context(netcdf_promote=True):
    cube = iris.load_cube(url, 'sea_surface_height_above_geoid')
    
print(cube)

