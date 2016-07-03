#!/usr/bin/env python

# conda execute
# env:
#   - iris ==1.9.2
#   - mpld3 ==0.2
#   - pyoos ==0.7.0
#   - pyyaml ==3.11
#   - folium ==0.2.1
#   - seaborn ==0.7.0
#   - geojson ==1.3.2
#   - oceans ==0.2.5
#   - mplleaflet ==0.0.5
#   - scikit-learn ==0.17.1
# channels:
#    - conda-forge
# run_with: python

"""
Model vs observations maps.

"""


import os
import sys
import numpy as np
import pandas as pd
import folium.plugins

# Load configuration.
from pytools.ioos import parse_config

config_file = os.path.abspath(sys.argv[1])
config = parse_config(config_file)

save_dir = os.path.join(os.path.abspath(os.path.dirname(config_file)),
                        config['run_name'])


# Load skill_score.
fname = os.path.join(config['run_name'], 'skill_score.csv')
skill_score = pd.read_csv(fname)


from mpld3 import save_html
import matplotlib.pyplot as plt
from mpld3.plugins import LineLabelTooltip, connect

from pytools.ioos import make_map

kw = dict(line=True, states=False, hf_radar=True, layers=False)
mapa = make_map(config['region']['bbox'], **kw)

# ROMS stations files (SABGOM and USEAST).
roms_stations = [(-77.7866, 34.2133),
                 (-78.9183, 33.6550),
                 (-81.0000, 30.3966),
                 (-80.1600, 25.7300),
                 (-81.8116, 24.5550),
                 (-82.6137, 26.1300),
                 (-82.8320, 27.9770),
                 (-86.4987, 30.1520)]

for station in roms_stations:
    location = station[::-1]
    popup = '[SABGOM/USEAST]\nROMS station file'
    kw = dict(radius=700, fill_color='red', popup=popup,
              fill_opacity=0.75)
    folium.CircleMarker(location=location, **kw).add_to(mapa)


# Clusters.
from glob import glob
from operator import itemgetter

import iris
from pandas import DataFrame, read_csv

fname = '{}-all_obs.csv'.format(config['run_name'])
all_obs = read_csv(os.path.join(config['run_name'], fname), index_col='name')

big_list = []
for fname in glob(os.path.join(config['run_name'], "*.nc")):
    if 'OBS_DATA' in fname:
        continue
    cube = iris.load_cube(fname)
    model = fname.split('-')[-1].split('.')[0]
    lons = cube.coord(axis='X').points
    lats = cube.coord(axis='Y').points
    stations = cube.coord('station name').points
    models = [model]*lons.size
    lista = zip(models, lons.tolist(), lats.tolist(), stations.tolist())
    big_list.extend(lista)

big_list.sort(key=itemgetter(3))
df = DataFrame(big_list, columns=['name', 'lon', 'lat', 'station'])
df.set_index('station', drop=True, inplace=True)
groups = df.groupby(df.index)


locations, popups = [], []
for station, info in groups:
    sta_name = all_obs['station'][all_obs['station'] == station].index[0]
    for lat, lon, name in zip(info.lat, info.lon, info.name):
        locations.append([lat, lon])
        popups.append('[{}]: {}'.format(name, sta_name))

mapa.add_children(folium.plugins.MarkerCluster(locations=locations,
                                               popups=popups))


# Model and observations plots.
def nc2df(fname):
    """Load a netCDF timeSeries file as a DataFrame."""
    import iris
    from iris.pandas import as_data_frame

    cube = iris.load_cube(fname)
    for coord in cube.coords(dimensions=[0]):
        name = coord.name()
        if name != 'time':
            cube.remove_coord(name)
    for coord in cube.coords(dimensions=[1]):
        name = coord.name()
        if name != 'station name':
            cube.remove_coord(name)
    df = as_data_frame(cube)
    if cube.ndim == 1:  # Horrible work around iris.
        station = cube.coord('station name').points[0]
        df.columns = [station]
    return df


def load_secoora_ncs(run_name):
    """Loads local files using the `run_name` date."""
    from glob import glob

    fname = '{}-{}.nc'.format
    OBS_DATA = nc2df(os.path.join(run_name,
                                  fname(run_name, 'OBS_DATA')))
    SECOORA_OBS_DATA = nc2df(os.path.join(run_name,
                                          fname(run_name, 'SECOORA_OBS_DATA')))

    ALL_OBS_DATA = pd.concat([OBS_DATA, SECOORA_OBS_DATA], axis=1)
    index = ALL_OBS_DATA.index

    dfs = dict(OBS_DATA=ALL_OBS_DATA)
    for fname in glob(os.path.join(run_name, "*.nc")):
        if 'OBS_DATA' in fname:
            continue
        else:
            model = fname.split('.')[0].split('-')[-1]
            df = nc2df(fname)
            # FIXME: Horrible work around duplicate times.
            if len(df.index.values) != len(np.unique(df.index.values)):
                kw = dict(subset='index', keep='last')
                df = df.reset_index().drop_duplicates(**kw).set_index('index')
            kw = dict(method='time', limit=30)
            df = df.reindex(index).interpolate(**kw).ix[index]
            dfs.update({model: df})
    return pd.Panel.fromDict(dfs).swapaxes(0, 2)

dfs = load_secoora_ncs(config['run_name'])

mean_bias = skill_score['mean_bias'].applymap('{:.2f}'.format).replace('nan', '--')  # noqa
low_pass_r2 = skill_score['low_pass_resampled_3H_r2'].applymap('{:.2f}'.format).replace('nan', '--')  # noqa

resolution, width, height = 75, 7, 3


def make_plot():
    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_ylabel('Sea surface salinity ({})'.format(config['units']))
    ax.grid(True)
    return fig, ax


# SABGOM dt = 3 hours.
dfs = dfs.swapaxes('items', 'major').resample('3H').swapaxes('items', 'major')

for station in dfs:
    df = dfs[station].dropna(axis=1, how='all')
    if df.empty:
        continue
    labels = []
    fig, ax = make_plot()
    for col in df.columns:
        serie = df[col].dropna()
        lines = ax.plot(serie.index, serie, label=col,
                        linewidth=2.5, alpha=0.5)
        if 'OBS_DATA' not in col:
            text0 = col
            text1 = mean_bias.get(station).get(col, '--')
            text2 = low_pass_r2.get(station).get(col, '--')
            tooltip = '{}:\nbias {}\nskill: {}'.format
            labels.append(tooltip(text0, text1, text2))
        else:
            labels.append('OBS_DATA')
    kw = dict(loc='upper center', bbox_to_anchor=(0.5, 1.05), numpoints=1,
              ncol=2, framealpha=0)
    l = ax.legend(**kw)
    l.set_title("")  # Workaround str(None).

    [connect(fig, LineLabelTooltip(line, name))
     for line, name in zip(ax.lines, labels)]

    html = 'station_{}.html'.format(station)
    figname = '{}/{}'.format(config['run_name'], html)
    save_html(fig, figname)
    plt.close(fig)

    with open(figname, 'r') as f:
        html = f.read()
    iframe = folium.element.IFrame(html,
                                   width=(width*resolution)+75,
                                   height=(height*resolution)+50)
    popup = folium.Popup(iframe, max_width=2650)

    if (df.columns == 'OBS_DATA').all():
        icon = folium.Icon(color='blue', icon_color='white', icon='ok')
    else:
        conj = set(df.columns)
        conj.intersection_update(config['secoora_models'])
        kw = dict(color='green', icon_color='white')
        if conj:
            icon = folium.Icon(icon='ok-sign', **kw)
        else:
            icon = folium.Icon(icon='ok', **kw)
    obs = all_obs[all_obs['station'] == station].squeeze()
    folium.Marker(location=[obs['lat'], obs['lon']],
                  icon=icon, popup=popup).add_to(mapa)


# Bad stations.
bad_station = all_obs[all_obs['bad_station']]

if not bad_station.empty:
    for station, obs in bad_station.iterrows():
        popup = '[Station]: {}'
        popup = popup.format(station)
        kw = dict(color='red', icon_color='white', icon='question-sign')
        icon = folium.Icon(**kw)
        folium.Marker(location=[obs['lat'], obs['lon']],
                      icon=icon, popup=popup).add_to(mapa)

# Map.
mapa.save(os.path.join(config['run_name'], 'mapa.html'))
