# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# https://github.com/ioos/secoora/issues/2

# <codecell>

import iris

print(iris.__version__)

# <markdowncell>

# http://cfconventions.org/1.6.html#dimensionless-v-coord
# 
# * `ocean_sigma_over_z`  **implemented** (https://github.com/SciTools/iris/pull/509)
# * `ocean_sigma`  **not implemented**
# * `ocean_s_coordinate`  **not implemented**
# * `ocean_s_coordinate_g1`  **not implemented** (https://cf-pcmdi.llnl.gov/trac/ticket/93)
# * `ocean_s_coordinate_g2`  **not implemented** (https://cf-pcmdi.llnl.gov/trac/ticket/93)

# <markdowncell>

# Use these files or the urls for the examples below.
# 
# * wget http://geoport.whoi.edu/thredds/fileServer/usgs/data2/rsignell/models/ncom/ncom_sigma_over_z.nc
# * wget http://geoport.whoi.edu/thredds/fileServer/usgs/data2/rsignell/models/z_coord/ocean_sigma.nc
# * wget http://geoport.whoi.edu/thredds/fileServer/examples/bora_feb.nc
# * wget http://geoport.whoi.edu/thredds/fileServer/usgs/data2/rsignell/models/z_coord/ocean_s_coordinate_g1.nc
# * wget http://geoport.whoi.edu/thredds/fileServer/usgs/data2/rsignell/models/z_coord/ocean_s_coordinate_g2.nc

# <codecell>

# url = "http://geoport.whoi.edu/thredds/dodsC/usgs/data2/rsignell/models/ncom/ncom_sigma_over_z.nc"
cube = iris.load_cube('./data/ncom_sigma_over_z.nc', 'sea_water_potential_temperature')
z = cube.coords(axis='Z')

print(cube)
print(z)

# <codecell>

# url = "http://opendap.co-ops.nos.noaa.gov/thredds/dodsC/NYOFS/fmrc/Aggregated_7_day_NYOFS_Fields_Forecast_best.ncd"
cube = iris.load_cube('./data/ocean_sigma.nc', 'upward_sea_water_velocity')
z = cube.coords(axis='Z')

print(cube)
print(z)

# <codecell>

#url = "http://geoport.whoi.edu/thredds/dodsC/examples/bora_feb.nc"
cube = iris.load('./data/ocean_s_coordinate.nc')[22]
z = cube.coords(axis='Z')

print(cube)
print(z)

# <codecell>

#url = "http://geoport.whoi.edu/thredds/dodsC/coawst_4/use/fmrc/coawst_4_use_best.ncd"
cube = iris.load_cube('./data/ocean_s_coordinate_g1.nc', 'sea_water_salinity')
z = cube.coords(axis='Z')

print(cube)
print(z)

# <codecell>

#url = "http://oos.soest.hawaii.edu/thredds/dodsC/hioos/roms_assim/hiig/ROMS_Hawaii_Regional_Ocean_Model_Assimilation_best.ncd"
cube = iris.load_cube('./data/ocean_s_coordinate_g2.nc', 'salinity')
z = cube.coords(axis='Z')

print(cube)
print(z)

