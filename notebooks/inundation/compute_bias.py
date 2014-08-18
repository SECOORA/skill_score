# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import os
from utilities import nc2df

directory = '2014-08-08'
fname = '{}-OBS_DATA.nc'.format(directory)
fname = os.path.join(directory, fname)
OBS_DATA = nc2df(fname)
index = OBS_DATA.index

# <codecell>

from glob import glob
from pandas import Panel

dfs = dict(OBS_DATA=OBS_DATA)
for fname in glob(os.path.join(directory, "*.nc")):
    if 'OBS_DATA' in fname:
        pass
    else:
        model = fname.split('.')[0].split('-')[-1]
        df = nc2df(fname)
        if False:
            kw = dict(method='time')
            df = df.reindex(index).interpolate(**kw).ix[index]
        dfs.update({model: df})

dfs = Panel.fromDict(dfs).swapaxes(0, 2)

# <codecell>

import seaborn
import matplotlib.pyplot as plt

from utilities import get_coops_longname

for station, df in dfs.iteritems():
    df.dropna(axis=1, how='all', inplace=True)
    if len(df.columns) == 1:
        pass
    else:
        fig, ax = plt.subplots()
        for name, series in df.iteritems():
            series.dropna().plot(ax=ax)
        ax.set_title(station)
        ax.legend()

# <codecell>

from pandas import DataFrame

means = dict()
for station, df in dfs.iteritems():
    df.dropna(axis=1, how='all', inplace=True)
    mean = df.mean()
    df = df - mean + mean['OBS_DATA']
    means.update({station: mean['OBS_DATA'] - mean.drop('OBS_DATA')})
    if len(df.columns) == 1:
        pass
    else:
        fig, ax = plt.subplots()
        for name, series in df.iteritems():
            series.dropna().plot(ax=ax)
        ax.set_title(get_coops_longname(station))
        ax.set_ylim(-1.5, 1.5)
        kw = dict(loc='upper center', bbox_to_anchor=(0.5, .97),
              ncol=2, fancybox=True, shadow=True)
        ax.legend(**kw)
        ax.set_ylabel('m')

# <codecell>

bias = DataFrame.from_dict(means).dropna(axis=1, how='all')
bias

