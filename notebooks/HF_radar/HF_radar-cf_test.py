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
    try:
        cube = iris.load_cube(hfradar[region])
    except (ConstraintMismatchError, ValueError, TypeError) as e:
        warn("Unable to load %s. %s\n" % (region, e))

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

for region in hfradar.keys():
    url = hfradar[region]
    cdl, out = call_cf_checker(url)
    print(url)
    print('CF Checker:\n%s\nCF Error:\n%s\nCDL:\n%s\n' % (out.stdout, out.stderr, cdl))

