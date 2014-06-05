# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# https://github.com/SciTools/iris/pull/1070
# https://github.com/SciTools/iris/pull/1159

# <codecell>

import iris
print(iris.__version__)  # remotes/origin/netcdf_promote 15b2c96

# <codecell>

print(iris.FUTURE.netcdf_promote)

# <codecell>

url = 'http://geoport.whoi.edu/thredds/dodsC/coawst_4/use/fmrc/coawst_4_use_best.ncd'

cube = iris.load_cube(url, 'water_surface_height_above_reference_datum')
print(cube)

# <codecell>

iris.FUTURE.netcdf_promote = True

cube = iris.load_cube(url, 'water_surface_height_above_reference_datum')
print(cube)

# <codecell>

from iris.fileformats.cf import reference_terms
reference_terms

# <markdowncell>

# We can add non-standard names!  (Not really needed for the URL below.  See https://github.com/SciTools/iris/pull/1159#issuecomment-45201929)

# <codecell>

reference_terms['ocean_sigma/general_coordinate'] = 'eta'
reference_terms

# <codecell>

url = "http://fvcom.smast.umassd.edu:8080/thredds/dodsC/FVCOM/NECOFS/Forecasts/NECOFS_GOM3_FORECAST.nc"

zeta = iris.load_cube(url, 'sea_surface_height_above_geoid')
print(zeta)

