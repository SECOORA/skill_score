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
Time-series model skill

This notebook calculates several skill scores for the
SECOORA models weekly time-series saved by 00-fetch_data.py.

"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from pytools.ioos import to_html, save_html
from pytools.taylor_diagram import TaylorDiagram
from pytools.skill_score import apply_skill, mean_bias, rmse, r2

# Load configuration.
from pytools.ioos import parse_config

config_file = os.path.abspath(sys.argv[1])
config = parse_config(config_file)

save_dir = os.path.join(os.path.abspath(os.path.dirname(config_file)),
                        config['run_name'])

fname = '{}-all_obs.csv'.format(save_dir)
all_obs = pd.read_csv(os.path.join(save_dir, fname), index_col='name')


"""
Skill 1: Model Bias (or Mean Bias)

The bias skill compares the model mean values against the observations.
It is possible to introduce a Mean Bias in the model due to a mismatch of the
boundary forcing and the model interior.

$$ \text{MB} = \mathbf{\overline{m}} - \mathbf{\overline{o}}$$
"""


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

dfs = load_secoora_ncs(save_dir)

df = apply_skill(dfs, mean_bias, remove_mean=False, filter_tides=False)
skill_score = dict(mean_bias=df.copy())

# Filter out stations with no valid comparison.
df.dropna(how='all', axis=1, inplace=True)
df = df.applymap('{:.2f}'.format).replace('nan', '--')

html = to_html(df.T)
fname = os.path.join(save_dir, 'mean_bias.html'.format(config['run_name']))
save_html(fname, html)


"""
Skill 2: Central Root Mean Squared Error

Root Mean Squared Error of the deviations from the mean,

$$ \text{CRMS} = \sqrt{\left(\mathbf{m'} - \mathbf{o'}\right)^2}$$

where:

$\mathbf{m'} = \mathbf{m} - \mathbf{\overline{m}}$

and

$\mathbf{o'} = \mathbf{o} - \mathbf{\overline{o}}$
"""

dfs = load_secoora_ncs(save_dir)

df = apply_skill(dfs, rmse, remove_mean=True, filter_tides=False)
skill_score['rmse'] = df.copy()

# Filter out stations with no valid comparison.
df.dropna(how='all', axis=1, inplace=True)
df = df.applymap('{:.2f}'.format).replace('nan', '--')

html = to_html(df.T)
fname = os.path.join(save_dir, 'rmse.html'.format(config['run_name']))
save_html(fname, html)


"""
Skill 3: R$^2$

https://en.wikipedia.org/wiki/Coefficient_of_determination

"""

dfs = load_secoora_ncs(save_dir)

df = apply_skill(dfs, r2, remove_mean=True, filter_tides=False)
skill_score['r2'] = df.copy()

# Filter out stations with no valid comparison.
df.dropna(how='all', axis=1, inplace=True)
df = df.applymap('{:.2f}'.format).replace('nan', '--')

html = to_html(df.T)
fname = os.path.join(save_dir, 'r2.html'.format(config['run_name']))
save_html(fname, html)


"""
Skill 4: Low passed R$^2$

http://dx.doi.org/10.1175/1520-0450(1979)018%3C1016:LFIOAT%3E2.0.CO;2

https://github.com/ioos/secoora/issues/188

"""

dfs = load_secoora_ncs(save_dir)

df = apply_skill(dfs, r2, remove_mean=True, filter_tides=True)
skill_score['low_pass_r2'] = df.copy()

# Filter out stations with no valid comparison.
df.dropna(how='all', axis=1, inplace=True)
df = df.applymap('{:.2f}'.format).replace('nan', '--')

html = to_html(df.T)
fname = os.path.join(save_dir, 'low_pass_r2.html'.format(config['run_name']))
save_html(fname, html)


"""
Skill 4: Low passed and re-sampled (3H) R$^2$

https://github.com/ioos/secoora/issues/183

"""

dfs = load_secoora_ncs(save_dir)

# SABGOM dt = 3 hours.
dfs = dfs.swapaxes('items', 'major').resample('3H').swapaxes('items', 'major')

df = apply_skill(dfs, r2, remove_mean=True, filter_tides=False)
skill_score['low_pass_resampled_3H_r2'] = df.copy()

# Filter out stations with no valid comparison.
df.dropna(how='all', axis=1, inplace=True)
df = df.applymap('{:.2f}'.format).replace('nan', '--')

html = to_html(df.T)
fname = os.path.join(save_dir,
                     'lowpass_resampled_3H_r2.html'.format(config['run_name']))
save_html(fname, html)


# Save scores.
fname = os.path.join(save_dir, 'skill_score.csv')
skill_score.to_csv(fname, float_format='%.2f')

"""
Normalized Taylor diagrams

The radius is model standard deviation error divided by observations
deviation, azimuth is arc-cosine of cross correlation (R),
and distance to point (1, 0) on the abscissa is Centered RMS.

"""


def make_taylor(samples):
    fig = plt.figure(figsize=(9, 9))
    dia = TaylorDiagram(samples['std']['OBS_DATA'],
                        fig=fig,
                        label="Observation")
    # Add samples to Taylor diagram.
    samples.drop('OBS_DATA', inplace=True)
    for model, row in samples.iterrows():
        dia.add_sample(row['std'], row['corr'], marker='s', ls='',
                       label=model)
    # Add RMS contours, and label them.
    contours = dia.add_contours(colors='0.5')
    plt.clabel(contours, inline=1, fontsize=10)
    # Add a figure legend.
    kw = dict(prop=dict(size='small'), loc='upper right')
    fig.legend(dia.samplePoints,
               [p.get_label() for p in dia.samplePoints],
               numpoints=1, **kw)
    return fig

dfs = load_secoora_ncs(save_dir)

# Bin and interpolate all series to 1 hour.
freq = '3H'
for station, df in list(dfs.iteritems()):
    df = df.resample(freq).interpolate().dropna(axis=1)
    if 'OBS_DATA' in df:
        samples = pd.DataFrame.from_dict(dict(std=df.std(),
                                         corr=df.corr()['OBS_DATA']))
    else:
        continue
    samples[samples < 0] = np.NaN
    samples.dropna(inplace=True)
    if len(samples) <= 2:  # 1 obs 1 model.
        continue
    fig = make_taylor(samples)
    fig.savefig(os.path.join(save_dir, '{}.png'.format(station)))
    plt.close(fig)
