# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# ### This notebook is just an interpolation test for the `inundation_secoora.ipynb` notebook

# <codecell>

import os
from utilities import nc2df

directory = 'bias'
fname = '2014-06-07-OBS_DATA.nc'

fname = os.path.join(directory, fname)
OBS_DATA = nc2df(fname)
index = OBS_DATA.index

# <markdowncell>

# First the original downloaded series.

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
        dfs.update({model: df})

dfs = Panel.fromDict(dfs).swapaxes(0, 2)

# <codecell>

import seaborn
from pandas import DataFrame
from utilities import get_coops_longname
%config InlineBackend.figure_format = 'svg'


def plot_series(dfs, marker='.', dropna=False):
    station, df = list(dfs.iteritems())[0]
    df.dropna(axis=1, how='all', inplace=True)
    fig, ax = plt.subplots()
    for name, series in df.iteritems():
        if dropna:
            series.dropna().plot(ax=ax, marker=marker)
        else:
            series.plot(ax=ax, marker=marker)
    ax.set_title(get_coops_longname(station))
    ax.set_ylim(-1.5, 1.5)
    kw = dict(loc='upper center', bbox_to_anchor=(0.5, .97),
              ncol=2, fancybox=True, shadow=True)
    ax.legend(**kw)
    ax.set_ylabel('m')

# <markdowncell>

# There is no interpolation yet, but I want to test the best way to plot them.

# <codecell>

plot_series(dfs, marker=None, dropna=False)

# <codecell>

plot_series(dfs, marker='.', dropna=False)

# <codecell>

plot_series(dfs, marker=None, dropna=True)

# <markdowncell>

# Conclusion: I have to either use `dropna` or use a `marker` to plot the series
# with the `NaNs`.  If I use `dropna` pandas will stretch the gaps and connect
# them with a line.  Note that the data remains unchanged!

# <markdowncell>

# Now I will try to find the different time resolution in the Panel and compute
# how many point I need to interpolate to match them with the observed data
# resolution (6 min).

# <codecell>

dfs = dict(OBS_DATA=OBS_DATA)
for fname in glob(os.path.join(directory, "*.nc")):
    if 'OBS_DATA' in fname:
        pass
    else:
        model = fname.split('.')[0].split('-')[-1]
        df = nc2df(fname)
        res = np.diff(df.index.to_pydatetime())[0].total_seconds()
        print('{}: resolution {} hours ({} points to fill)'.format(model, res/60/60., res / 60 / 6.))
        if True:
            kw = dict(method='time', limit=240)
            df = df.reindex(index).interpolate(**kw).ix[index]
        dfs.update({model: df})

dfs = Panel.fromDict(dfs).swapaxes(0, 2)
plot_series(dfs, marker='.', dropna=False)

# <markdowncell>

# Using the max fill potins, 240, is a bad choice.  Now the line is actually data connecting the gap.  Lets try 10.

# <codecell>

dfs = dict(OBS_DATA=OBS_DATA)
for fname in glob(os.path.join(directory, "*.nc")):
    if 'OBS_DATA' in fname:
        pass
    else:
        model = fname.split('.')[0].split('-')[-1]
        df = nc2df(fname)
        if True:
            kw = dict(method='time', limit=10)
            df = df.reindex(index).interpolate(**kw).ix[index]
        dfs.update({model: df})

dfs = Panel.fromDict(dfs).swapaxes(0, 2)
plot_series(dfs, marker='.', dropna=False)

# <markdowncell>

# 10 is bad for `SABGOM` and will be worse for `USF` and `HYCOM` low resolutions.
# Lets try to interpolate all the series to `SABGOM` 3H resolution using a 1 hour limit to extrapolation.

# <codecell>

from pandas import date_range

new_index = date_range(start=index[0], end=index[-1], freq='3H')

def interp_series(fname, method='time', limit=10):
    df = nc2df(fname)
    df = df.reindex(new_index)
    df = df.interpolate(method=method, limit=limit).ix[new_index]
    return df

dfs = dict()
for fname in glob(os.path.join(directory, "*.nc")):
    model = fname.split('.')[0].split('-')[-1]
    if model == 'OBS_DATA':
        df = interp_series(fname, method='time', limit=0)
    else:
        df = interp_series(fname, method='time', limit=1)
    dfs.update({model: df})


dfs = Panel.fromDict(dfs).swapaxes(0, 2)
plot_series(dfs, marker='.', dropna=False)

# <markdowncell>

# Almost ideal for plotting, but `ESTOFS` has several gaps that get
# extrapolated for at least +3 hours inside the gap.
# 
# Here is a *hacky* work around.  I do extrapolate that first +3 hours and then
# remove it.  That way pandas interpolate all the intervals up to 3 hours, but if
# the gap is longer than 3 hours I consider the interpolation an extrapolation
# and remove that point.

# <codecell>

def remove_extrapolation(series, num=1):
    """Make the idx before the first NaN a NaN as well."""
    clean_series = series.copy()
    idx = np.where(np.isnan(series))[0] - num
    clean_series.ix[idx] = np.NaN
    return clean_series
        
def plot_series(dfs, marker='.', dropna=False):
    station, df = list(dfs.iteritems())[0]
    df.dropna(axis=1, how='all', inplace=True)
    fig, ax = plt.subplots()
    for name, series in df.iteritems():
        series = remove_extrapolation(series, num=1)
        if dropna:
            series.dropna().plot(ax=ax, marker=marker)
        else:
            series.plot(ax=ax, marker=marker)
    ax.set_title(get_coops_longname(station))
    ax.set_ylim(-1.5, 1.5)
    kw = dict(loc='upper center', bbox_to_anchor=(0.5, .97),
              ncol=2, fancybox=True, shadow=True)
    ax.legend(**kw)
    ax.set_ylabel('m')

# <codecell>

plot_series(dfs, marker=None, dropna=False)

# <markdowncell>

# I will probaly be using this to plot.

