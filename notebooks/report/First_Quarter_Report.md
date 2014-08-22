# Model Skill Assessment -- First Quarter Report
## (May 1, 2014 -- July 31, 2014)
### Filipe Pires Alvarenga Fernandes

This report outlines the tasks and work performed for SECOORA Model
Skill Assessment project.

## Task 1: Create a github SECOORA repository/wiki/page for the project

A [github](https://github.com/ioos/secoora) repository, a
[wiki](https://github.com/ioos/secoora/wiki) notes page, and a results
[web-page](http://ocefpaf.github.io/secoora) was created for the project.
The repository contains all the code generated for the project.  The
[issue page](https://github.com/ioos/secoora/issues) shows all the raised
issues, the discussions, and the implemented the solutions for the project.
The [wiki](https://github.com/ioos/secoora/wiki)
contains notes and instructions on how to run the code and reproduce the
results.  The results are display in a
[web-page](http://ocefpaf.github.io/secoora) for better visualization.


## Task 2) Sea-surface height data discovery and plotting

The goal was to identify the type of service protocols/endpoints to access
the *in-situ* SECOORA data, and list the total number of variables/data sets
available in each catalog for SECOORA.

Observational datasets containing sea surface elevations were found,
accessed, and plotted for SECOORA stations and various ocean circulation
models, including SECOORA run SABGOM.  Data was limited to 7 days for better
visualization ($\pm$ 3 days centered at the requested date).
Model datasets were plotted only for points near the observation stations.

The Catalog search allows for dynamic discovery, access and comparisons as new
datasets become available (or inactive).  Data from both OPeNDAP-CF and SOS
endpoints can be discovered, accessed and used.
[*pyoos*](https://github.com/ioos/pyoos),
[*iris*](http://scitools.org.uk/iris/) [@Iris] python modules
allowed the extraction of observed data and model output for both unstructured
and structured grids.

Model and observational data were performed via a time
[series plot](http://ocefpaf.github.io/secoora/notebooks/inundation/2014-08-01/inundation_map.html).
Model data was taken from the nearest model grid point up to $\approx$ 4 km.

An inline interactive map interface displays the locations of observation data
and corresponding model grid points.  When selected they show the time series
[plots](http://ocefpaf.github.io/secoora/notebooks/inundation/2014-08-01/inundation_map.html).

### Challenges Identified and Resolved:

- Standardized access to *SOS*, *OPeNDAP-CF* observations and models.  All the
  endpoints found are printed in the notebook for future reference.  Both are
  read by either *iris* as a *cube* or *panda* as a *DataFrame*.  The
  conversion between these two formats is seamless using *iris.pandas* and the
  CF helper functions.
- Standardized loading and plotting of models with a variety of grids standards
  (structured,  unstructured), grids shape, variable units, and more.
- Find nearest, non-land, model grid point to every observed station use a
  KDTree for every model grid.
- Not all observed station return data in the datum requested (NAVD).
  When a different datum is found, the data is removed from the comparison.

### Longer-term Challenges Identified:

- The non-*NAVD* datum stations will be included in the comparison via some
  conversion to the proper datum.
- The observed and model data will be compared via simple regression and an
  offset bias calculation.
- The framework implemented for sea surface height can be applied to other
  scalar observation (i.e., temperature, salinity,
  nutrients, and etc).

## Task 3) HF-Radar discovery and plotting

The first step is very similar to the sea surface height exercise.  However,
here I used the *HFRNET* and hard-coded the *SABGOM* ROMS model instead of
executing a catalog discovered.  The reason for that is detailed in the github
[issues](https://github.com/ioos/secoora/issues)
[discussions](https://github.com/ioos/secoora/issues/9).
The data for both model and velocity components is plotted as an interactive
map.

### Challenges Identified and Resolved:

- The units for current speeds may not be consistent across model and observed
  data.  To prevent  units mismatch I convert all the data to m s$^{-1}$ using
  *iris.Unit*.
- The ROMS model data grid for storing *u* and *v* is not consistent.  ROMS
  *u*and *v* components are stored in 4 dimensions (coordinates: *time_run*,
   *time*, *s_rho*, *eta*, *xi*) and the *u*- and *v*- components are on
  separate lat lon grids (*eta_u*, *eta_v*, *xi_u*, *xi_v*).  *Iris* cannot
  handle this in an elegant way, so I implemented Signell's helper functions
  to rotate and average both *u* and *v* at their center points.


### Longer-term Challenges Identified:

- It can be difficult to distinguish between model and observed current from
  HF Radar.  Some distinction must be done if a catalog search is performed.
- Iris cannot handle elegantly all the different grid forms for velocity data.
  More helper functions to standardize them are needed to proceed.
- There is no time-series comparison with at the moment.  This will be needed
  when searching for mooring/buoys velocity observation observation.
- SECOORA HF Radar operators will be consulted to resolve the data access
  points for HF Radar to drop the hard coded *HFRNET* endpoint.

## Task 4) Implemented SABGOM *ocean_sigma* coordinates in iris

Iris has a poor handling of the various CF ocean vertical non-dimension
coordinates.  All the future notebooks will need a better handling of the
vertical coordinates to proceed and have implemented that capability.  There
is ongoing progress on standing
[*Pull Request*](https://github.com/SciTools/iris/pull/1166) for that.


# References

<!--
git --no-pager log --author=ocefpaf --format='"%ci","%s"' --no-merges --until="1-Aug-2014" > secoora.csv
-->


<!-- geometry: margin=1in -->

<!--
pandoc --standalone --smart \
       --reference-docx=reference.docx \
       --bibliography ../../references/references.bib \
       --from markdown First_Quarter_Report.md \
       --to docx \
       --output First_Quarter_Report.docx
-->

<!--
pandoc --standalone --smart \
       --latex-engine=xelatex \
       --bibliography ../../references/references.bib \
       --from markdown First_Quarter_Report.md \
       --to latex \
       --output First_Quarter_Report.pdf
-->
