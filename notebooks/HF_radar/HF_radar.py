# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import iris
from warnings import warn
from iris.exceptions import ConstraintMismatchError

# <codecell>

hfradar = dict(longbay="http://129.252.139.124/thredds/dodsC/longbay.nc",
               savannah="http://129.252.139.124/thredds/dodsC/savannah.nc",
               miami_wera="http://129.252.139.124/thredds/dodsC/miami_wera.nc",
               tampa_codar="http://129.252.139.124/thredds/dodsC/tampa_codar.nc",
               tampa_wera="http://129.252.139.124/thredds/dodsC/tampa_wera.nc")

# <codecell>

for region in hfradar.keys():
    print(region)
    try:
        cube = iris.load_cube(hfradar[region])
    except (ConstraintMismatchError, ValueError, TypeError) as e:
        warn("Unable to load %s. %s\n" % (region, e))

