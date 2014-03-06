import os
import pickle
import zipfile
import tempfile
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
from netCDF4 import Dataset, date2index, num2date



def kml(lon, lat, **kwargs):
    """Based on
    https://github.com/hetland/octant/blob/master/octant/sandbox/googleearth.py
    """
    plt.ioff()
    pixels = kwargs.pop('pixels', 1024)  # Pixels of the max. dimension.
    name = kwargs.pop('name', 'overlay')
    color = kwargs.pop('color', '9effffff')
    visibility = str(kwargs.pop('visibility', 1))
    kmzfile = kwargs.pop('kmzfile', 'overlay.kmz')

    aspect = np.cos(lat.mean() * np.pi/180.0)
    xsize = lon.ptp() * aspect
    ysize = lat.ptp()
    aspect = ysize / xsize

    if aspect > 1.0:
        figsize = (10.0 / aspect, 10.0)
    else:
        figsize = (10.0, 10.0 * aspect)

    # Overlays.
    def make_gearth_fig():
        fig = plt.figure(figsize=figsize,
                         frameon=False,
                         dpi=pixels//10)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(lon.min(), lon.max())
        ax.set_ylim(lat.min(), lat.max())
        return fig, ax

    # Create your figures.
    fig, ax = make_gearth_fig()
    cs = ax.tricontourf(tri, h, levels=levels, shading='faceted',
                        cmap=plt.cm.gist_earth_r)
    ax.set_axis_off()
    with tempfile.NamedTemporaryFile(suffix='.png', prefix='overlay-') as tf:
        overlay1 = os.path.split(tf.name)[-1]
    fig.savefig(overlay1, transparent=False, format='png')
    plt.close(fig)

    fig, ax = make_gearth_fig()
    Q = ax.quiver(data['lonc'][idv], data['latc'][idv],
                  data['u'][idv], data['v'][idv], scale=20)
    maxstr = '%3.1f m s$^{-1}$' % maxvel
    ax.quiverkey(Q, 0.92, 0.08, maxvel, maxstr, labelpos='W')
    ax.set_title('NECOFS Velocity, Layer %d, %s UTC' % (ilayer, daystr))
    ax.set_axis_off()
    with tempfile.NamedTemporaryFile(suffix='.png', prefix='overlay-') as tf:
        overlay2 = os.path.split(tf.name)[-1]
    fig.savefig(overlay2, transparent=True, format='png')
    plt.close(fig)

    # Colorbar.
    fig = plt.figure(figsize=(1.0, 4.0), facecolor=None, frameon=False)
    ax = fig.add_axes([0.0, 0.05, 0.2, 0.9])
    cb = fig.colorbar(cs, cax=ax)
    cb.set_label('Water Depth (m)', rotation=-90, color='k', labelpad=20)
    with tempfile.NamedTemporaryFile(suffix='.png', prefix='legend-') as tf:
        legend = os.path.split(tf.name)[-1]
    fig.savefig(legend, transparent=True, format='png')
    plt.close(fig)

    # Save KMZ.
    kml_groundoverlay = '''<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://earth.google.com/kml/2.0">
    <Document>
    <GroundOverlay>
    <name>__NAME__</name>
    <color>__COLOR__</color>
    <visibility>__VISIBILITY__</visibility>
    <Icon>
        <href>%s</href>
    </Icon>
    <LatLonBox>
        <south>__SOUTH__</south>
        <north>__NORTH__</north>
        <west>__WEST__</west>
        <east>__EAST__</east>
    </LatLonBox>
    </GroundOverlay>
    <GroundOverlay>
    <name>__NAME__</name>
    <color>__COLOR__</color>
    <visibility>__VISIBILITY__</visibility>
    <Icon>
        <href>%s</href>
    </Icon>
    <LatLonBox>
        <south>__SOUTH__</south>
        <north>__NORTH__</north>
        <west>__WEST__</west>
        <east>__EAST__</east>
    </LatLonBox>
    </GroundOverlay>
    <ScreenOverlay>
        <name>Legend</name>
        <Icon>
            <href>%s</href>
        </Icon>
        <overlayXY x="0" y="0" xunits="fraction" yunits="fraction"/>
        <screenXY x="0.015" y="0.075" xunits="fraction" yunits="fraction"/>
        <rotationXY x="0.5" y="0.5" xunits="fraction" yunits="fraction"/>
        <size x="0" y="0" xunits="pixels" yunits="pixels"/>
    </ScreenOverlay>
    </Document>
    </kml>
    ''' % (overlay1, overlay2, legend)
    with zipfile.ZipFile(kmzfile, 'w') as f:
        f.writestr('overlay.kml',
                   kml_groundoverlay.replace('__NAME__', name)
                                    .replace('__COLOR__', color)
                                    .replace('__VISIBILITY__', visibility)
                                    .replace('__SOUTH__', str(lat.min()))
                                    .replace('__NORTH__', str(lat.max()))
                                    .replace('__EAST__', str(lon.max()))
                                    .replace('__WEST__', str(lon.min())))
        f.write(overlay1)
        f.write(overlay2)
        f.write(legend)
    os.unlink(overlay1)
    os.unlink(overlay2)
    os.unlink(legend)

# Download grid.
filename = "FVCOM_grid.nc"
url = 'http://www.smast.umassd.edu:8080/thredds/dodsC/'
url += 'FVCOM/NECOFS/Forecasts/NECOFS_FVCOM_OCEAN_MASSBAY_FORECAST.nc'

if not os.path.isfile(filename):
    os.system("nc3tonc4 -o --complevel=9 --vars lon,lat,latc,lonc,h,nv %s %s" %
              (url, filename))


def triangulate(grid):
    """Enter a netCDF FVCOM-gridfile to triangulate.
    Returns a matplotlib Triangulation object."""
    with Dataset(grid) as nc:
        lon, lat = nc.variables['lon'][:], nc.variables['lat'][:]
        # Get Connectivity array.
        triangles = nc.variables['nv'][:].T - 1
    return Triangulation(lon, lat, triangles=triangles)


def fvcom_slice(url, lims, start, ilayer):
    """Slice FVCOM velocities.  (TODO: slice all variables.)
    url/filename : str
                   local netCDF or OpenDAP
    start : datetime object
            nearest time to slice.
    ilayer : int
             0 = surface, -1 = bottom
    lims : list of floats
           bbox of the slice area
    """
    # Load grid.  (Hard-wired to use the gridfile.)
    with Dataset(filename) as nc:
        depth = nc.variables['h'][:]
        lon, lat = nc.variables['lon'][:], nc.variables['lat'][:]
        lonc, latc = nc.variables['lonc'][:], nc.variables['latc'][:]

    with Dataset(url) as nc:
        time_var = nc.variables['time']
        itime = date2index(start, time_var, select='nearest')
        dtime = num2date(time_var[itime], time_var.units)

        # Find points in bounding box.
        ind = ((lonc >= lims[0]) & (lonc <= lims[1]) &
               (latc >= lims[2]) & (latc <= lims[3]))
        u = nc.variables['u'][itime, ilayer, :]
        v = nc.variables['v'][itime, ilayer, :]
        lonc, latc, u, v = lonc[ind], latc[ind], u[ind], v[ind]

        # Find water level points in bounding box.
        idx = ((lon >= lims[0]) & (lon <= lims[1]) &
               (lat >= lims[2]) & (lat <= lims[3]))
        lon, lat, depth = lon[idx], lat[idx], depth[idx]
    return dict(lonc=lonc, latc=latc, u=u, v=v, lon=lon, lat=lat, depth=depth,
                dtime=dtime)


# Load data for Boston harbor figure.
tri = triangulate(filename)
lims = [-70.97, -70.82, 42.25, 42.35]  # bbox.
levels = range(-1, 35, 1)  # Depth contours to plot.
maxvel = 0.5  # Quiver key velcoity.
subsample = 3
ilayer = 0
start = datetime(2014, 3, 6, 12, 0, 0)

if os.path.isfile('data.pkl'):
    with open("data.pkl", "rb") as f:
        data = pickle.load(f)
else:
    data = fvcom_slice(url, lims=lims, ilayer=ilayer, start=start)
    with open("data.pkl", "wb") as f:
        pickle.dump(data, f)

# Suffle vectors and subsample.
ind = np.arange(len(data['u']))
np.random.shuffle(ind)
Nvec = len(ind) // subsample
idv = ind[:Nvec]

with Dataset(filename) as nc:
    h = nc.variables['h'][:]

daystr = data['dtime'].strftime('%Y-%b-%d %H:%M')

if False:  # Rich figure.
    merc_aspect = dict(aspect=(1.0 / np.cos(data['lat'].mean() * np.pi/180.0)))
    fig, ax = plt.subplots(figsize=(9, 5), subplot_kw=merc_aspect)
    cs = ax.tricontourf(tri, h, levels=levels, shading='faceted',
                        cmap=plt.cm.gist_earth_r)
    ax.axis(lims)
    ax.patch.set_facecolor('0.5')
    cbar = fig.colorbar(cs)
    cbar.set_label('Water Depth (m)', rotation=-90, labelpad=20)
    Q = ax.quiver(data['lonc'][idv], data['latc'][idv],
                  data['u'][idv], data['v'][idv], scale=20)
    maxstr = r'%3.1f m s$^{-1}$' % maxvel
    qk = ax.quiverkey(Q, 0.92, 0.08, maxvel, maxstr, labelpos='W')
    ax.set_title('NECOFS Velocity, Layer %d, %s UTC' % (ilayer, daystr))

if True:  # Google-Earth figure.
    kml(data['lon'], data['lat'], kmzfile='FVCOM.kmz',
        name='FVCOM_depth_and_velocity')
