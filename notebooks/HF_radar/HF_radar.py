# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import iris
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
    except (ConstraintMismatchError, ValueError) as e:
        warn("Unable to load %s. %s\n" % (region, e))

# <codecell>

from netCDF4 import Dataset

# <codecell>

nc = Dataset(hfradar['tampa_codar'])

# <codecell>

nc

# <codecell>

import folium
from warnings import warn
folium.initialize_notebook()

hf_radar = folium.Map(location=[40, -122], zoom_start=5,
                      tiles='OpenStreetMap')

for name, location in locations.items():
    hf_radar.polygon_marker(location=location, fill_color='#6a9fb5',
                            radius=12, popup=name)

hf_radar.render_iframe = True
hf_radar

if False:
    hf_radar.create_map('map.html')

