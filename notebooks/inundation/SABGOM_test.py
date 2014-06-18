# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# <font color='red'>Cannot use now, dates are a few days behind:</font>

# <codecell>

from netCDF4 import Dataset, num2date

sabgom = 'http://omgsrv1.meas.ncsu.edu:8080/thredds/dodsC/fmrc/sabgom/'
sabgom += 'SABGOM_Forecast_Model_Run_Collection_best.ncd'

with Dataset(sabgom) as nc:
    ocean_time = nc.variables['ocean_time']
    time = num2date(ocean_time[:], ocean_time.units)
    print('Model date range is from %s to %s' % (time[0], time[-1]))

# <markdowncell>

# <font color='red'>Cannot load using standard names:</font>

# <codecell>

import iris
from iris.exceptions import ConstraintMismatchError
iris.FUTURE.netcdf_promote = True

name_list = ['water level',
             'sea_surface_height',
             'sea_surface_elevation',
             'sea_surface_height_above_geoid',
             'sea_surface_height_above_sea_level',
             'water_surface_height_above_reference_datum',
             'sea_surface_height_above_reference_ellipsoid']

name_in_list = lambda cube: cube.standard_name in name_list
constraint = iris.Constraint(cube_func=name_in_list)

import warnings
with warnings.catch_warnings():
    # Less noise and more attetion to the issue!
    warnings.simplefilter("ignore")
    try:
        cube = iris.load_cube(sabgom, constraint)
    except ConstraintMismatchError as e:
        print(e)
    

# <markdowncell>

# <font color='red'>Here is CF-checker output:</font>

# <codecell>

from tempfile import NamedTemporaryFile
from sh import ncdump, ncgen, cfchecker

def call_cf_checker(url):
    cdl = ncdump('-h', url)
    if cdl.exit_code == 0:
        with NamedTemporaryFile(suffix='.cdl') as cdl_file:
            cdl_file.write(cdl.stdout)
            cdl_file.flush()
            with NamedTemporaryFile(suffix='.nc') as nc_file:
                out = ncgen('-x', cdl_file.name, o=nc_file.name, _ok_code=1)
                if out.exit_code == 0:
                    out = cfchecker(nc_file.name, _ok_code=1)
    return cdl, out

# <codecell>

cdl, out = call_cf_checker(sabgom)

print('CF Checker:\n%s\nCF Error:\n%s' % (out.stdout, out.stderr))

# <codecell>

for line in cdl.stdout.split('\n'):
    if 'zeta' in line:
        print(line.strip())

# <markdowncell>

# <font color='red'>Example of a "healthy" url:</font>

# <codecell>

espresso = 'http://tds.marine.rutgers.edu/thredds/dodsC/roms/espresso/2013_da/his_Best/'
espresso +='ESPRESSO_Real-Time_v2_History_Best_Available_best.ncd'

cdl, out = call_cf_checker(espresso)

for line in cdl.stdout.split('\n'):
    if 'zeta' in line:
        print(line.strip())

