# Model Skill Assessment -- First Quarter Report
## (August 1, 2014 -- October 31, 2014)
### Filipe Pires Alvarenga Fernandes

This report outlines the tasks and work performed in the second quarter for
the SECOORA Model Skill Assessment project.

## Task 1: Run and update a weekly report of the sea surface height notebook bias

Sea Surface Height (SSH) observations and modeled data are fetched and
processed on a weekly basis using IPython notebooks [@Perez_and_Granger_2007].
The observed time-series are plotted over an interactive map along the nearest
model grid cell.  In addition, all the SECOORA moored stations and buoys are
displayed in the map, even when the data are not found at that position.

The data endpoints for the download are discovered using the NOAA Catalog
Service Web (CSW) `http://www.ngdc.noaa.gov/geoportal/csw`.  Models are
downloaded via the more robust OPeNDAP endpoint, while observations are
downloaded using the SOS endpoints.
<!-- (more @rsignell up-to-date?). -->

The results web-page is hosted in the URL: `http://ocefpaf.github.io/secoora`,
and is still a proof of concept maintained as an exercise on how to display
future results.

The web-page displays "the previous month time-series", where the oldest week
is always rotated with the newest one.  The past results are archived from
2014-08-01 to the present.

At this phase the only comparison metric that is being computed regularity is
the SSH bias relative the North American Vertical Datum of 1988 (NAVD88).

The notebook:
[01-inundation_secoora.ipynb](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/master/notebooks/elevation/01-inundation_secoora.ipynb)
shows an example of the work-flow frozen at the Hurricane Arthur event
(2014-07-07) and the notebook:
[00-generate_page_html.ipynb](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/master/notebooks/elevation/00-generate_page_html.ipynb)
is used to generated the results displayed in the web-page.

### Issues found:

- Both SABGOM and USEAST, the SECOORA run models, are not always discoverable
  via the NOAA CSW.  To circumvent that the notebook tries to find both models
  via the catalog first, if they are not found the URLs are hard-coded into
  the notebook and a warning is issued in the log file.
- Not all the SECOORA moored stations and buoys listed at
  `https://github.com/ocefpaf/secoora/blob/master/notebooks/climatology_data_sources.csv`
  are found in the catalog.  Unlike the models their URLs are not hard-coded
  into the notebook.
<!--   (@vembus: Are there DAP/SOS URLs for those stations that I can use?) -->
- The bias, or any other metric that will be computed in the future, is highly
  sensitive\* to the model grid point (or grid points in case of interpolation)
  that are chosen for the comparison.  There is the need to discuss a strategy
  for choosing and/or validation a grid point for comparison before advancing
  this notebook towards more sophisticated metrics like Taylor diagrams
  [@Taylor_and_Karl_2001] and the methods described in @Wilkin_and_Hunter_2013.

\* Example: a barrier island where the observation is at one side and the model
grid point at another, even though they are close than 4 km they are not
correlated invalidating the comparison.

## Task 2) Salinity and temperature data discovery and plotting

The goal is to identify the type of service protocols and endpoints to access
the *in-situ* SECOORA data for Sea Surface Salinity (SSS) and Sea Surface
Temperature (SST).

Observational data-sets containing SST and SSS were found, accessed, and
plotted for SECOORA stations and various ocean circulation models.  Two
notebooks similar to SSH were created, one notebook showing the weekly
time-series and another example notebook frozen at the Hurricane Arthur event
on 2014-07-07.  Modeled data were plotted only for points at 4 km or less from
the observation location.

The query for temperature date, notebook
[01-temperature_secoora.ipynb](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/master/notebooks/temperature/01-temperature_secoora.ipynb),
finds sufficient observed data locations that can be paired with model grid
points for comparisons.  However, most of the SECOORA stations listed at
`climatology_data_sources.csv` are not found.

The query for salinity observations, on the other hand, returns very few
observed data, and they are not sufficient for any kind, all locations found
are further than 4 km to any model grid point. See the notebook
[01-salinity_secoora.ipynb](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/master/notebooks/salinity/01-salinity_secoora.ipynb).


### Issues found:
- Satellite data for both SSS and SST are discarded for now.  There is the
  need to develop a heuristic method to discern from model and satellite
  gridded data.
<!--   (@rsignell I think there is a CF rule to identify models, right?) -->
- Like Sea Surface Height both temperature and salinity queries, using the
  NOAA CSW, does not return all the SECOORA stations.
- The salinity observations found are insufficient and the notebook needs
  additional data sources (NDBC, regional SECOORA catalogs etc).
- No metric is calculated for the temperature comparisons at this moment.
  That is because a visual comparison of the model and observation time-series
  shows strong disagreement.  The reason for such disparity between model and
  observations is that the modeled data are actually SST, while the
  observations might be sub-surface.  To improve the comparison the notebook
  needs a way to discover the observations actual depth and to interpolate the
  model grid point to that depth instead of using SST.

## Task 3) Velocity (moored time-series and horizontal HF-radar snapshots) data discovery and plotting

The HF-Radar data can now be discoverable via the catalog (github issue
[93](https://github.com/ioos/system-test/issues/93)).  The only challenge that
remains is to load the various models grid in a consistent way for the
comparison.  There are examples notebooks implemented for
[ROMS](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/master/notebooks/HF_radar/HFR_comparison.ipynb)
and [FVCOM](http://nbviewer.ipython.org/github/rsignell-usgs/notebook/blob/master/UGRID/FVCOM_depth_and_velocity-gom3.ipynb),
and corresponding tests to plot them onto a regular grid.

The velocity time-series notebook,
[currents_time_series.ipynb](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/master/notebooks/velocity/currents_time_series.ipynb),
uses both SOS and NDBC data endpoints, still both sources were are not
sufficient for a near real time (past week data) comparison.  SOS finds only
one observed location while all NDBC data found is older than the past week.
<!-- (@vembus I believe that only HF-Radar will be, right?) -->

### Issues found:

- Use HF-Radar data as am additional source for the time-series comparison.
- Interpolate model data to the HF-radar grid for the comparisons.
- Change the strategy for the comparison using longer time-series than
  "last week data."

## Task 4) Glider data discovery and plotting

Glider data cannot yet be discovered via the catalog.  In order to advance an
example notebook for glider platforms,
[Glider_DAC_test.ipynb](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/master/sandbox/Glider_DAC_test.ipynb),
was created without data discovery.  This notebook uses the DAC to fetch and
plot the data.


### Issues found:

- Glider data are very challenging to compare with models as it needs a 4D
  model slice at the glider path coordinates (`x`, `y`, `z`, `t`).  Right now
  that is not possible using iris [@Iris].  The next version of iris will
  implement additional Ocean Dimensionless Vertical Coordinates (ODV)
  facilitating the creation of such 4D slices.

## Task 5) Implemented Ocean Dimensionless Vertical coordinates for iris

All the notebooks make heavy use of the python library iris to load and
process the URL endpoints as well as local files.  However, iris comes short
when handling the CF Ocean Dimensionless Vertical Coordinates.  A software
patch was created to solve the problem,

`https://github.com/SciTools/iris/pull/1304`

and here is a test of the patch:

`http://nbviewer.ipython.org/gist/ocefpaf/65894dbc0c9eb4642a3`.

In order to merge this patch with the main iris code the patch needs to handle
staggered grids, like the ones used in
[ROMS models](http://nbviewer.ipython.org/urls/gist.githubusercontent.com/ocefpaf/1e8275862cb2853ced47/raw/02ec63713fb54c51bb63d78f3a6069ac79b30250/staggered_grid.ipynb).

There is an ongoing discussion on how to proceed with that here:

`https://github.com/SciTools/iris/issues/1164#issuecomment-56654400`

# References

<!-- geometry: margin=1in -->

<!--
pandoc --standalone --smart \
       --bibliography ../references/references.bib \
       --reference-docx=reference.docx \
       --from markdown 2nd_Quarter_Report.md \
       --to docx \
       --output 2nd_Quarter_Report.docx
-->

<!--
pandoc --standalone --smart \
       --latex-engine=xelatex \
       --bibliography ../references/references.bib \
       --from markdown 2nd_Quarter_Report.md \
       --to latex \
       --output 2nd_Quarter_Report.pdf
-->
