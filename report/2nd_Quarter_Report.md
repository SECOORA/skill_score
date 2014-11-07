# Model Skill Assessment -- First Quarter Report
## (August 1, 2014 -- October 31, 2014)
### Filipe Pires Alvarenga Fernandes

This report outlines the tasks and work performed for the SECOORA Model
Skill Assessment project second quarter.

## Task 1: Run and update a weekly report of the sea surface height notebook bias comparison

The results are uploaded on a weekly basis to the website
http://ocefpaf.github.io/secoora, where a month worth of data is shown online.
Past results are archived since 2014-08-01 to the present.  The only metric
computed is sea surface height bias relative the NAVD88 datum.

The website is still a proof of concept and is being maintained in a temporary
address as an exercise on how to display future comparisons.

The [notebook](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/refactor/notebooks/elevation/01-inundation_secoora.ipynb)
fetches data from SOS stations and queries the CSW catalog for the
models, additional stations with SECOORA buoys and moorings are marked for
future inclusion in the comparison.


## Task 2) Salinity and temperature data discovery and plotting

The goal was to identify the type of service protocols/endpoints to access
the *in-situ* SECOORA data, and list the total number of data-sets
available in each catalog for SECOORA.

Observational data-sets containing sea surface temperature and sea surface
salinity were found, accessed, and plotted for SECOORA stations and various
ocean circulation models, including SECOORA run SABGOM and USEAST.  Similar to
sea surface height the data was limited to 7 days for better visualization.
Model data-sets were plotted only for points near the observation stations.

The observations search for
[temperature](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/refactor/notebooks/temperature/01-temperature_secoora.ipynb) finds a good number of usable SOS
stations,
[salinity](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/refactor/notebooks/salinity/01-salinity_secoora.ipynb) however is very scare (only 3 stations) and outside
the models domain.


Challenges identified:

- Find the proper temperature observations depth to improve the poor
  comparison with the sea surface temperature.
- Search for other data sources (NDBC, regional SECOORA catalogs?) for
  salinity.
- Implement a simple metric like model-data correlation to serve as guidance
  before computing Taylor diagrams with all the data/models.
- Re-factor observation search to find satellite and moored data separately, to
  allow for time-series and horizontal comparisons.

## Task 3) Velocity (moored time-series and horizontal HF-radar snapshots) data discovery and plotting

The HF-Radar data is discoverable via the catalog now (TODO: add link), the
only challenge that remains is to load all the different models grid in a
consistent way for the comparison.  There are examples for ROMS and FVCOM
implement URL1 and URL2 and some tests to plot them in a regular grid URL3.

For the time-series plots both SOS and NDBC were used.  Still, both data
sources were not very [effective](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/refactor/notebooks/velocity/currents_time_series.ipynb) to find enough data with a week interval.

Challenges identified:

- Use HF-radar data as am additional source for the time-series comparison.
- Interpolate model data to the HF-radar grid for the comparisons.

## Task 4) Glider data discovery and plotting

Glide data cannot yet be discovered via the catalog (TODO: confirm this with
@rsignell).  In order to advance the DAC (?) URL is used, in order to prepare
a
[notebook](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/refactor/sandbox/Glider_DAC_test.ipynb) to fetch and plot the data for future comparisons.

## Task 5) Implemented Ocean Dimensionless Vertical coordinates in iris

All the notebook make heavy use of the software iris to load and process the
various URL endpoints.  Iris comes short when handling the various CF ocean
vertical non-dimension coordinates.  There is already a software patch to solve
that at https://github.com/SciTools/iris/pull/1304 and a test at
http://nbviewer.ipython.org/gist/ocefpaf/658904dbc0c9eb4642a3

The only challenged that still needs to be solved is how to handle staggered grid
like the one used by ROMS:

http://nbviewer.ipython.org/urls/gist.githubusercontent.com/ocefpaf/1e8275862cb2853ced47/raw/02ec63713fb54c51bb63d78f3a6069ac79b30250/staggered_grid.ipynb


All the notebook create can be visualized from this URL:
    
http://nbviewer.ipython.org/github/ocefpaf/secoora/tree/refactor/notebooks/


# References

<!-- geometry: margin=1in -->

<!--
pandoc --standalone --smart \
       --reference-docx=reference.docx \
       --bibliography ../../references/references.bib \
       --from markdown 2nd_Quarter_Report.md \
       --to docx \
       --output 2nd_Quarter_Report.docx
-->

<!--
pandoc --standalone --smart \
       --latex-engine=xelatex \
       --bibliography ../../references/references.bib \
       --from markdown 2nd_Quarter_Report.md \
       --to latex \
       --output 2nd_Quarter_Report.pdf
-->
