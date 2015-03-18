# Model Skill Assessment -- Third Quarter Report
## (October 31, 2014 -- January 31, 2014)
### Filipe Pires Alvarenga Fernandes

This report outlines the tasks performed in the third quarter for the
SECOORA Model Skill Assessment project.

## Task 1: Continued run/update of weekly time-series data

Sea Surface Height (SSH), Sea Surface Temperature (SST), and Sea Surface
Salinity (SSS) observations are fetched and automatically paired with the
nearest water grid point of several numerical models.  Model data is only
compared with observations when the distance does not exceed 5 km.  The
comparisons are saved in HTML tables and displayed both in the interactive map
and as a standalone table.  The SSH has a second comparison metric regarding
the vertical bias of the elevations versus to the North American Vertical Datum
of 1988 (NAVD88).

The data endpoints for the download are discovered using the NOAA Catalog
Service Web (CSW - http://www.ngdc.noaa.gov/geoportal/csw).  Models are
downloaded via the more robust OPeNDAP endpoint.  Observations, on the other
hand, are downloaded via a mix of SOS endpoints and SECOORA
[THREDDS server](http://129.252.139.124/thredds/catalog_platforms.html).

The results web-page is hosted in the URL: http://ocefpaf.github.io/secoora.
It is still a proof of concept maintained as an exercise on how to display
future results.  Right now the user has little control of the date extension,
but the pre-fetched time-series can be extended to be longer and the users
could choose any dates backwards from the present.

The notebooks,
[00-salinity_secoora.ipynb](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/master/notebooks/timeSeries/sss/00-salinity_secoora.ipynb)
[00-inundation_secoora.ipynb](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/master/notebooks/timeSeries/ssh/00-inundation_secoora.ipynb)
[00-temperature_secoora.ipynb](http://nbviewer.ipython.org/github/ocefpaf/secoora/blob/master/notebooks/timeSeries/sst/00-temperature_secoora.ipynb),
are frozen at the Hurricane Arthur example.  The weekly runs are obtained by
updating the *start* and *stop* dates.



### Issues found:

- The SECOORA moored stations and buoys are not found in the NGDC
  catalog (See the GitHub issue [#150](https://github.com/ioos/secoora/issues/150)).
  Right now they are manually scraped from the SECOORA THREDDS server and
  inserted in the notebook.

## Task 2) Create a reproducible development environment

A SECOORA/IOOS *binstar* channel was generated in order to create a
reproducible development environment.  All the software needed to run the
notebooks in the SECOORA skill score exercise can be installed on Mac, Windows,
and Linux following the instructions at
https://github.com/ioos/conda-recipes/wiki.

## Task 3) Factor out the utilities sub-module

All the notebooks make use of a collection of functions called *utilities*.
These functions are used to find nearest data points in space and time using
high level abstractions.  Several improvements and many bugs were fixed by
factoring this sub-module out as a standalone
[module](https://github.com/pyoceans/utilities).


## Task 4) Develop an equivalent to `nc_genslice` to extract vertical slices

The latest Iris version has implemented the most common Ocean Dimensionless
Vertical Coordinates (ODVC) used by numerical models.  The next step is to
implement *nc_genslice*, in order to compare numerical models and glider
observations using vertical slices.  The proof of concept is shown in
[this](http://nbviewer.ipython.org/gist/ocefpaf/64fe42434065dc98c031)
notebook.


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
       --bibliography ../references/references.bib \
       --from markdown 2nd_Quarter_Report.md \
       --to latex \
       --latex-engine=xelatex \
       --output 2nd_Quarter_Report.pdf
-->
