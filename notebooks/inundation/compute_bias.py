# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

import os
import sys
root = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
sys.path.append(root)

# <codecell>

import os
from utilities import nc2df

directory = 'bias'
if directory == 'bias':
    fname = '2014-06-07-OBS_DATA.nc'
else:
    fname = '{}-OBS_DATA.nc'.format(directory)
fname = os.path.join(directory, fname)
OBS_DATA = nc2df(fname)
index = OBS_DATA.index

# <markdowncell>

# ### Removed model mean and "rebase" all using observation mean

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
%matplotlib inline
%config InlineBackend.figure_format = 'svg'

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

string_table = bias.applymap('{:.2f}'.format).replace('nan', '--')

columns = dict()
[columns.update({station: get_coops_longname(station)}) for
 station in string_table.columns.values]
string_table.rename(columns=columns, inplace=True)

# <codecell>

style = """<style>
    .datagrid table {
        border-collapse:collapse;
        text-align:left;
        width:65%
    }
    .datagrid td {
        border-collapse:collapse;
        text-align:right;
    }
    .datagrid {
        font:normal 12px/150% Arial,Helvetica,sans-serif;
        background:#fff;
        overflow:hidden;
        border:1px solid #069;
        -webkit-border-radius:3px;
        -moz-border-radius:3px;
        border-radius:3px
    }
    .datagrid table td,.datagrid table th {
        padding:3px 10px
    }
    .datagrid table thead th {
        background:-webkit-gradient(linear,left top,left bottom,color-stop(0.05,#069),color-stop(1,#00557F));
        background:-moz-linear-gradient(center top,#069 5%,#00557F 100%);
        filter:progid:DXImageTransform.Microsoft.gradient(startColorstr='#006699',endColorstr='#00557F');
        background-color:#069;
        color:#FFF;
        font-size:15px;
        font-weight:700;
        border-left:1px solid #0070A8
    }
    .datagrid table thead th:first-child {
        border:none
    }
    .datagrid table tbody td {
        color:#00496B;
        border-left:1px solid #E1EEF4;
        font-size:12px;
        font-weight:400
    }
    .datagrid table tbody .alt td {
        background:#E1EEF4;
        color:#00496B
    }
    .datagrid table tbody td:first-child {
        border-left:none
    }
    .datagrid table tbody tr:last-child td {
        border-bottom:none
    }
    .datagrid table tfoot td div {
        border-top:1px solid #069;
        background:#E1EEF4
    }
    .datagrid table tfoot td {
        padding:0;
        font-size:12px
    }
    .datagrid table tfoot td div {
        padding:2px
    }
    .datagrid table tfoot td ul {
        margin:0;
        padding:0;
        list-style:none;
        text-align:right
    }
    .datagrid table tfoot li {
        display:inline
    }
    .datagrid table tfoot li a {
        text-decoration:none;
        display:inline-block;
        padding:2px 8px;
        margin:1px;
        color:#FFF;
        border:1px solid #069;
        -webkit-border-radius:3px;
        -moz-border-radius:3px;
        border-radius:3px;
        background:-webkit-gradient(linear,left top,left bottom,color-stop(0.05,#069),color-stop(1,#00557F));
        background:-moz-linear-gradient(center top,#069 5%,#00557F 100%);
        filter:progid:DXImageTransform.Microsoft.gradient(startColorstr='#006699',endColorstr='#00557F');
        background-color:#069
    }
    .datagrid table tfoot ul.active,.datagrid table tfoot ul a:hover {
        text-decoration:none;
        border-color:#069;
        color:#FFF;
        background:none;
        background-color:#00557F
    }
    div.dhtmlx_window_active,div.dhx_modal_cover_dv {
        position:fixed!important
}
</style>"""

# <codecell>

from IPython.display import HTML
fname = os.path.join(directory, 'table.html'.format(directory))

table = dict(style=style, table=string_table.T.to_html(classes="datagrid"))
table = '{style}<div class="datagrid">{table}</div>'.format(**table)

with open(fname, 'w') as f:
    f.writelines(table)
    
HTML(table)

