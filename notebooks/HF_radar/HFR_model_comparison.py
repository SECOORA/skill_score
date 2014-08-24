# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

from cartopy.io import shapereader

kw = dict(resolution='110m', category='cultural',
          name='admin_1_states_provinces')
shpfilename = shapereader.natural_earth(**kw)

reader = shapereader.Reader(shpfilename)
states = reader.records()
SECOORA = ('North Carolina', 'South Carolina', 'Georgia', 'Florida')
for state in states:
    name = state.attributes['name']
    if name in SECOORA:
        print(name)

# <codecell>

from utilities import css_styles
css_styles()

# <markdowncell>

# #### User options are bbox and time range

# <codecell>

from datetime import datetime, timedelta

# SECOORA: NC, SC GA, FL
bounding_box_type = "box"
bounding_box = [-87.4, 24.25, -74.7, 36.70]

# Temporal range.
jd_now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
jd_start,  jd_stop = jd_now - timedelta(hours=(6)), jd_now

print('%s, %s ' % (jd_start,  jd_stop))

# <markdowncell>

# #### CSW Search NGDC Geoportal

# <codecell>

from owslib import fes
from owslib.csw import CatalogueServiceWeb

from utilities import date_range
from ipy_table import make_table, apply_theme

def fes_filter(jd_start, jd_stop, bounding_box, data_dict):
    """Convert User Input into FES filters."""
    time_fmt = '%Y-%m-%d %H:%M'
    start, stop = date_range(jd_start.strftime(time_fmt),
                             jd_stop.strftime(time_fmt))
    bbox = fes.BBox(bounding_box)
    # Use the search name to create search filter.
    kw = dict(propertyname='apiso:AnyText', escapeChar='\\',
              wildCard='*', singleChar='?')
    or_filt = fes.Or([fes.PropertyIsLike(literal=('*%s*' % val), **kw) for
                      val in data_dict['currents']['names']])
    
    val = 'Averages'
    not_filt = fes.Not([fes.PropertyIsLike(literal=('*%s*' % val), **kw)])
    
    filter_list = [fes.And([bbox, start, stop, or_filt, not_filt])]
    return filter_list
    
# CF and SOS names.
data_dict = dict()
sos_name = 'Currents'
# FIXME: Add model names
data_dict['currents'] = {"names": ['currents',
                                   'surface_eastward_sea_water_velocity',
                                   '*surface_eastward_sea_water_velocity*'],
                         "sos_name": ['currents']}  # <- TODOL Check why sos_name is here!

# Catalog.
endpoint = 'http://www.ngdc.noaa.gov/geoportal/csw'
csw = CatalogueServiceWeb(endpoint, timeout=60)
filter_list = fes_filter(jd_start, jd_stop, bounding_box, data_dict)
csw.getrecords2(constraints=filter_list, maxrecords=1000, esn='full')

<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Added currents CF names.
=======
>>>>>>> 6cb334599ccb7661357564cc98abf7ebf1ab3deb
# <markdowncell>

# ```python
# name_list = ['surface_eastward_sea_water_velocity',
#              'surface_northward_sea_water_velocity',
#              'surface_geostrophic_sea_water_x_velocity',
#              'surface_geostrophic_sea_water_y_velocity'
#              'surface_geostrophic_eastward_sea_water_velocity',
#              'surface_geostrophic_northward_sea_water_velocity',
#              'eastward_sea_water_velocity',
#              'northward_sea_water_velocity',
#              'sea_water_x_velocity',
#              'sea_water_y_velocity',
#              'baroclinic_eastward_sea_water_velocity',
#              'baroclinic_northward_sea_water_velocity',
#              'barotropic_eastward_sea_water_velocity',
#              'barotropic_northward_sea_water_velocity',
#              'barotropic_sea_water_x_velocity',
#              'barotropic_sea_water_y_velocity',
#              'bolus_eastward_sea_water_velocity',
#              'bolus_northward_sea_water_velocity',
#              'bolus_sea_water_x_velocity',
#              'bolus_sea_water_y_velocity',
#              'direction_of_sea_water_velocity',
#              'sea_water_speed',
#              'x_sea_water_velocity',
#              'y_sea_water_velocity',
#              'eastward_transformed_eulerian_mean_velocity',
#              'northward_transformed_eulerian_mean_velocity',
#              'surface_eastward_geostrophic_sea_water_velocity',
#              'surface_northward_geostrophic_sea_water_velocity',
#              'surface_geostrophic_sea_water_x_velocity_assuming_sea_level_for_geoid',
#              'surface_geostrophic_sea_water_y_velocity_assuming_sea_level_for_geoid',
#              'surface_geostrophic_eastward_sea_water_velocity_assuming_sea_level_for_geoid',
#              'surface_geostrophic_northward_sea_water_velocity_assuming_sea_level_for_geoid',
#              'surface_eastward_geostrophic_sea_water_velocity_assuming_sea_level_for_geoid',
#              'surface_northward_geostrophic_sea_water_velocity_assuming_sea_level_for_geoid']
# ```

<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> Trying to use catalog to find the data.
=======
>>>>>>> Added currents CF names.
=======
>>>>>>> 6cb334599ccb7661357564cc98abf7ebf1ab3deb
# <codecell>

print("Found {} csw records:\n".format(len(csw.records)))

table = [(item.title, rec) for rec, item in csw.records.items()]
table.insert(0, ('Title', 'Record'))
make_table(table)
apply_theme('basic')

# <markdowncell>

# #### DAP

# <codecell>

from utilities import service_urls

dap_urls = service_urls(csw.records, service='odp:url')
dap_urls = sorted(set(dap_urls))
print("Total DAP: %s" % len(dap_urls))
print("\n".join(dap_urls))

# <markdowncell>

# #### SOS

# <codecell>

sos_urls = service_urls(csw.records, service='sos:url')
sos_urls = sorted(set(sos_urls))
print("Total SOS: %s" % len(sos_urls))
print("\n".join(sos_urls))

# <markdowncell>

# #### Update SOS time-date

# <codecell>

iso_start = jd_start.strftime('%Y-%m-%dT%H:%M:%SZ')
iso_end = jd_stop.strftime('%Y-%m-%dT%H:%M:%SZ')
print('{}\n{}'.format(iso_start, iso_end))

# <markdowncell>

# <div class="success"><strong>Get list of stations</strong>
# - we get a list of the available stations from NOAA and COOPS</div>

# <markdowncell>

# #### Get CO-OPS Station Data

# <codecell>

from pyoos.collectors.coops.coops_sos import CoopsSos

coops_collector = CoopsSos()
coops_collector.start_time = jd_start
coops_collector.end_time = jd_stop
coops_collector.variables = data_dict["currents"]["sos_name"]
coops_collector.server.identification.title

ofrs = coops_collector.server.offerings

print("{}\n{}".format(coops_collector.start_time,
                      coops_collector.end_time))
print(len(ofrs))

# <markdowncell>

# #### Gets a list of the active stations from coops

# <codecell>

from pandas import read_csv
from utilities import sos_request

params = dict(observedProperty=sos_name,
              featureOfInterest='BBOX:{0},{1},{2},{3}'.format(*bounding_box))

url = sos_request(url='http://opendap.co-ops.nos.noaa.gov/ioos-dif-sos/SOS', **params)
obs_loc_df = read_csv(url)
obs_loc_df.drop_duplicates(subset='station_id', inplace=True)

# <codecell>

cols = ['processing_level',
        'reporting_interval (s)',
        'sea_water_temperature (C)',
        'platform_roll_angle (degree)',
        'platform_orientation (degree)',
        'platform_pitch_angle (degree)',
        'orientation', 'sampling_rate (Hz)',
        'bin_size (m)', 'first_bin_center (m)',
        'direction_of_sea_water_velocity (degree)',
        'sea_water_speed (cm/s)', 'sensor_depth (m)',
        'number_of_bins', 'bin (count)', 'bin_distance (m)']
obs_loc_df.drop(cols, axis=1, inplace=True)

make_table(np.r_[obs_loc_df.columns[None, :], obs_loc_df.values])
apply_theme('basic')

# <markdowncell>

# #### Get NDBC Station Data

# <codecell>

from pyoos.collectors.ndbc.ndbc_sos import NdbcSos

ndbc_collector = NdbcSos()
ndbc_collector.start_time = jd_start
ndbc_collector.end_time = jd_stop
ndbc_collector.variables = data_dict["currents"]["sos_name"]
ndbc_collector.server.identification.title
ofrs = ndbc_collector.server.offerings

print("{}\n{}".format(ndbc_collector.start_time,
                      ndbc_collector.end_time))
print(len(ofrs))

# <codecell>

params = dict(offering='urn:ioos:network:noaa.nws.ndbc:all',
              observedProperty=sos_name,
              featureOfInterest='BBOX:{0},{1},{2},{3}'.format(*bounding_box))

url = sos_request(url='http://sdf.ndbc.noaa.gov/sos/server.php', **params)
obs_loc_df = read_csv(url)
obs_loc_df.drop_duplicates(subset='station_id', inplace=True)

# <codecell>

obs_loc_df.columns

# <codecell>

cols = ['sea_water_speed (cm/s)',
        'bin (count)', 'depth (m)',
        'sea_water_temperature (C)',
        'platform_roll_angle (degree)',
        'echo_intensity_beam1 (count)',
        'echo_intensity_beam2 (count)',
        'echo_intensity_beam3 (count)',
        'echo_intensity_beam4 (count)',
        'platform_pitch_angle (degree)',
        'platform_orientation (degree)',
        'pct_rejected (%)', 'pct_bad (%)',
        'upward_sea_water_velocity (cm/s)',
        'correlation_magnitude_beam1 (count)',
        'correlation_magnitude_beam2 (count)',
        'correlation_magnitude_beam3 (count)',
        'correlation_magnitude_beam4 (count)',
        'error_velocity (cm/s)', 'quality_flags',
        'direction_of_sea_water_velocity (degree)',
        'pct_good_3_beam (%)', 'pct_good_4_beam (%)']

obs_loc_df.drop(cols, axis=1, inplace=True)

make_table(np.r_[obs_loc_df.columns[None, :], obs_loc_df.values])
apply_theme('basic')

# <markdowncell>

# #### NDBC Station information

# <markdowncell>

# ```python
# import os
# import folium
# import numpy as np
# import matplotlib.pyplot as plt
# from utilities import service_urls, get_coordinates, inline_map, processStationInfo, get_ncfiles_catalog
# ```

# <markdowncell>

# #### The function only support who date time differences

# <markdowncell>

# <div class="error">
# <strong>Large Temporal Requests Need To Be Broken Down</strong> -
# When requesting a large temporal range outside the SOS limit, the sos
# request needs to be broken down.  See issues in
# [ioos](https://github.com/ioos/system-test/issues/81),
# [ioos](https://github.com/ioos/system-test/issues/101),
# [ioos](https://github.com/ioos/system-test/issues/116)
# and
# [pyoos](https://github.com/ioos/pyoos/issues/35).  Unfortunately currents
# is not available via DAP
# ([ioos](https://github.com/ioos/system-test/issues/116))</div>

# <markdowncell>

# <div class="error">
# <strong>Large Temporal Requests Need To Be Broken Down</strong> -
# Obtaining long time series from COOPS via SOS is not ideal and the opendap
# links are not available, so we use the tides and currents api to get the
# currents in json format. The api response provides in default bin, unless a
# bin is specified (i.e bin=1)</div>

# <markdowncell>

# <div class="warning"><strong>Pyoos</strong> -
# Should be able to use the collector, but does not work?</div>

# <markdowncell>

# <div class="info">
# <strong>Use NDBC DAP endpoints to get time-series data</strong> -
# The DAP server for currents is available for NDBC data, we use that
# to get long time series data.</div>

# <markdowncell>

# <div class="info"><strong>Progress Information For Large Requests</strong> -
# Shows the user a progress bar for each stations as its processed.  Click
# [here]('http://www.tidesandcurrents.noaa.gov/cdata/StationList?type=Current+Data&filter=active')
# to show more information on the CO-OPS locations</div>

# <markdowncell>

# <div class="error"><strong>Processing long time series</strong> -
# The CO-OPS Server responds really slow (> 30 secs, for what should be
# a 5 sec request) to multiple requests, so getting long time series
# data is almost impossible.</div>

# <markdowncell>

# #### get CO-OPS station data

# <codecell>

# Used to define the number of days allowable by the service.
coops_point_max_days = ndbc_point_max_days = 30
print("start & end dates: %s, %s\n" % (jd_start, jd_stop))

for station_index in st_list.keys():
    # Set it so we can use it later.
    st = station_index.split(":")[-1]
    print('[%s]: %s' % (st_list[station_index]['source'], station_index))

    if st_list[station_index]['source'] == 'coops':
        # Coops fails for large requests.
        master_df = []
    elif st_list[station_index]['source'] == 'ndbc':
        # Use the dap catalog to get the data.
        master_df = get_ncfiles_catalog(station_index, jd_start, jd_stop)
    if len(master_df) > 0:
        st_list[station_index]['hasObsData'] = True
    st_list[station_index]['obsData'] = master_df

# <codecell>

# Check theres data in there.
st_list[st_list.keys()[2]]

# <markdowncell>

# #### Plot the pandas data frames for the stations

# <markdowncell>

# <div class="error"><strong>Station Data Plot</strong> -
# There might be an issue with some of the NDBC station data...</div>

# <codecell>

for station_index in st_list.keys():
    df = st_list[station_index]['obsData']
    if len(df) > 1:
        st_list[station_index]['hasObsData'] = True
        print("num rows: %s" % len(df))
        fig = plt.figure(figsize=(18, 3))
        plt.scatter(df.index, df['sea_water_speed (cm/s)'])
        fig.suptitle('Station:'+station_index, fontsize=20)
        plt.xlabel('Date', fontsize=18)
        plt.ylabel('sea_water_speed (cm/s)', fontsize=16)
    else:
        st_list[station_index]['hasObsData'] = False

# <markdowncell>

# #### Find the min and max data values

# <markdowncell>

# <div class="warning"><strong>Station Data Plot</strong> -
# Some stations might not plot due to the data.</div>

# <codecell>

# Build current roses.
filelist = [f for f in os.listdir("./images") if f.endswith(".png")]
for f in filelist:
    os.remove("./images/"+f)

station_min_max = {}
for station_index in st_list.keys():
    all_spd_data = {}
    all_dir_data = {}
    all_time_spd = []
    all_time_dir = []
    df = st_list[station_index]['obsData']
    if len(df) > 1:
        try:
            spd_data = df['sea_water_speed (cm/s)'].values
            spd_data = np.array(spd_data)

            dir_data = df['direction_of_sea_water_velocity (degree)'].values
            dir_data = np.array(dir_data)

            time_data = df.index.tolist()
            time_data = np.array(time_data)

            for idx in range(0, len(spd_data)):
                if spd_data[idx] > 998:
                    continue
                elif np.isnan(spd_data[idx]):
                    continue
                elif dir_data[idx] == 0:
                    continue
                else:
                    dt_year = time_data[idx].year
                    dt_year = str(dt_year)
                    if dt_year not in all_spd_data.keys():
                        all_spd_data[dt_year] = []
                        all_dir_data[dt_year] = []
                    # Convert to knots.
                    knot_val = (spd_data[idx] * 0.0194384449)
                    knot_val = "%.4f" % knot_val
                    knot_val = float(knot_val)

                    all_spd_data[dt_year].append(knot_val)
                    all_dir_data[dt_year].append(dir_data[idx])

                    all_time_spd.append(knot_val)
                    all_time_dir.append(dir_data[idx])

            all_time_spd = np.array(all_time_spd, dtype=np.float)
            all_time_dir = np.array(all_time_dir, dtype=np.float)

            station_min_max[station_index] = {}
            for year in all_spd_data.keys():
                year_spd = np.array(all_spd_data[year])
                year_dir = np.array(all_dir_data[year])
                station_min_max[station_index][year] = {}
                station_min_max[station_index][year]['pts'] = len(year_spd)
                min_spd, max_spd = np.min(year_spd), np.max(year_spd)
                station_min_max[station_index][year]['spd_min'] = min_spd
                station_min_max[station_index][year]['spd_max'] = max_spd
                dir_min, dir_max = np.argmin(year_spd), np.argmax(year_spd)
                yr_dir_min, yr_dir_max = year_dir[dir_min], year_dir[dir_max]
                station_min_max[station_index][year]['dir_at_min'] = yr_dir_min
                station_min_max[station_index][year]['dir_at_max'] = yr_dir_max
            try:
                # A stacked histogram with normed
                # (displayed in percent) results.
                ax = new_axes()
                ax.set_title(station_index.split(":")[-1] +
                             " stacked histogram with normed (displayed in %)"
                             "\nresults (spd in knots), All Time.")
                ax.bar(all_time_dir, all_time_spd, normed=True,
                       opening=0.8, edgecolor='white')
                set_legend(ax)

                fig = plt.gcf()
                fig.set_size_inches(8, 8)
                fname = './images/%s.png' % station_index.split(":")[-1]
                fig.savefig(fname, dpi=100)
            except Exception as e:
                print("Error when plotting %s" % e)
                pass

        except Exception as e:  # Be specific here!
            print("Error: %s" % e)
            pass

# <codecell>

# Plot the min and max from each station.
fields = ['spd_']

for idx in range(0, len(fields)):
    d_field = fields[idx]
    fig, ax = plt.subplots(1, 1, figsize=(18, 5))
    for st in station_min_max:
        x = y_min = y_max = []
        for year in station_min_max[st]:
            x.append(year)
            y_max.append(station_min_max[st][year][d_field+'max'])
        marker_size = station_min_max[st][year]['pts'] / 80
        marker_size += 20
        station_label = st.split(":")[-1]

        ax.scatter(np.array(x), np.array(y_max),
                   label=station_label, s=marker_size,
                   c=np.random.rand(3, 1), marker="o")
        ax.set_xlim([2000, 2015])
        ax.set_title("Yearly Max Speed Per Station, Marker Scaled Per"
                     "Annual Pts (bigger = more pts per year)")
        ax.set_ylabel("speed (knots)")
        ax.set_xlabel("Year")
        ax.legend(loc='upper left')

# <markdowncell>

# #### Produce Interactive Map

# <codecell>

station = st_list[st_list.keys()[0]]
m = folium.Map(location=[station["lat"], station["lon"]], zoom_start=4)
m.line(get_coordinates(bounding_box, bounding_box_type),
       line_color='#FF0000', line_weight=5)

# Plot the obs station.
for st in st_list:
    hasObs = st_list[st]['hasObsData']
    if hasObs:
        fname = './images/%s.png' % st.split(":")[-1]
        if os.path.isfile(fname):
            popup = ('Obs Location:<br>%s<br><img border=120 src="'
                     './images/%s.png" width="242" height="242">' %
                     (st, st.split(":")[-1]))
            m.simple_marker([st_list[st]["lat"], st_list[st]["lon"]],
                            popup=popup,
                            marker_color="green",
                            marker_icon="ok")
        else:
            popup = 'Obs Location:<br>%s' % st
            m.simple_marker([st_list[st]["lat"], st_list[st]["lon"]],
                            popup=popup,
                            marker_color="green",
                            marker_icon="ok")
    else:
        popup = 'Obs Location:<br>%s' % st
        m.simple_marker([st_list[st]["lat"], st_list[st]["lon"]],
                        popup=popup,
                        marker_color="red",
                        marker_icon="remove")
inline_map(m)

# <codecell>

def new_axes():
    fig = plt.figure(figsize=(8, 8), dpi=80, facecolor='w', edgecolor='w')
    rect = [0.1, 0.1, 0.8, 0.8]
    ax = WindroseAxes(fig, rect, axisbg='w')
    fig.add_axes(ax)
    return ax


def set_legend(ax):
    """Adjust the legend box."""
    l = ax.legend()
    plt.setp(l.get_texts(), fontsize=8)

