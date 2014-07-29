# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

# http://cfconventions.org/Data/cf-convetions/cf-conventions-1.7/build/cf-conventions.html#Example%20H2.1.1

import iris
from iris.pandas import as_cube

from pandas import read_csv

obs_data = read_csv('OBS_DATA.csv', parse_dates=True, index_col=0)


cube = as_cube(obs_data, calendars={1: iris.unit.CALENDAR_GREGORIAN})
cube.coord('index').rename('time')
cube.coord('columns').rename('station')
cube.rename('sea_surface_height')

longitude = iris.coords.AuxCoord(range(len(obs_data.columns)),  # Fake lon.
                                 var_name="lon",
                                 standard_name="longitude",
                                 long_name="station longitude",
                                 units=iris.unit.Unit('degrees'))

latitude = iris.coords.AuxCoord(range(len(obs_data.columns)),  # Fake lat.
                                 var_name="lat",
                                 standard_name="latitude",
                                 long_name="station latitude",
                                 units=iris.unit.Unit('degrees'))

#cube.add_aux_coord(longitude, data_dims=?)
#cube.add_aux_coord(latitude, data_dims=?)

print(cube)

