# Catalog-driven model skill assessment

To assess the performance of ocean forecast models the simulations need to be compared with observed data.
However, finding what models and observations exist at a certain point in time and space has historically been challenging because this information is held and distributed by numerous providers in different formats.
In addition the Integrated Ocean Observing System (IOOS) Regional Associations (RAs) are continuously producing (and serving) terabytes of modeled and observed data.
It would be is virtually impossible to manually browse this data universe.

In order to help with that task IOOS implemented a model-data delivery and access system  in which users can access the data in standardized manner (@Signell_and_Snowden_2014).
The system consists of standard web services and conventions like OPeNDAP (Open-source Project for a Network Data Access Protocol), CF (Climate and Forecast), SOS (Sensor Observational Service).

To bind this together IOOS use the ISO 19119-2 standard and the NcISO tool to of harvest all RAs endpoints and aggregate them in a Catalog Service Web (CSW).
In essence NcISO scans the remote the Thematic Real-time Environmental Distributed Data Services (THREDDS) catalogs and converts the metadata into ISO 19119-2 XML, which is used by the catalog services such as the Geoportal CSW.
Thanks to the CSW we have now a one source point to search and download all the data made available by SECOORA.

We can query the CSW via any Open Geospatial Consortium (OGC) client, like `OWSLib` and `pyoos`.  The query filters can be variables, date ranges, bounding box, etc, and the catalog returns all data endpoints registered (SOS or OPeNDAP).

Depending on the model, the horizontal coordinate of the output data may be on a regular, curvilinear, or unstructured grid, while the vertical coordinates may be on a uniform or non-dimensional grid with a number of different possibilities (e.g., sigma, s-coordinate, isopycnal, etc).
That complex matrix of possibilities can only be tackled by leveraging the CF-1.6 conventions, used to store the data, and a Common Data Model (CDM) interpreter like iris (@Iris_2010) to work with output from different models without any specific code.
Once the URLs endpoints are listed the task consists of downloading the data.


# Skill
In order to help users find the best available simulation for a certain
time/region we evaluate the Numerical Ocean Models (NOC) by reducing them to
a statistically meaningful measure of model performance (or skill).

We objectively assess different forecast models in the SECOORA region, using IOOS community data collected weekly.

The variables assessed Sea Surface Temperature (SST), Sea Surface Salinity (SSS), and Sea Surface Height (SSH) time-series.
The workflow can be easily extended to evaluate horizontal and vertical slices using satellite, CTD, and glider data. However, there are not sufficient data available in the catalog to provide a meaningful skill.

The Observed and Modeled time-series are interpolated (or sub-sampled depending on the original resolution) to a 3-hours resolution.
Model and observations are only considered for comparison when the distance between the station and the nearest model grid point is less than 5 km.
The paired data are run through a simple Quality Assurance and Quality Control (QA/QC) routine and then stored in time-series of station-like every week.
The QA/QC consists of spikes removal and clipping the data to minimum and maximum expected threshold.

The skill scores computed are the Model Bias (MB), Centered Root Mean Square Error (CRMSE), and Cross Correlation (R2) akin to @Wilkin_and_Hunter_2013.

Model skill may be low because of high noise in the data, or it may artificially high due to correlated properties in the model and data, e.g. tides for example (@Hetland_2006).
To avoid hindering phenomena like storm surges, we computed the skills twice: first against the original series, then again using a low-pass 40 hours Lanczos filter to remove the tides (@Duchon_1979).
All the series are re-sampled at 3 hours intervals to reduce the noise in the observations and create a consistent time interval for all models.
Only the filtered skill score is reported in the interactive map because most coastal ocean models are quite skillful to predict tides due to the use of independent tidal harmonic as boundary conditions.

We summarize the in a Taylor Diagram (@Taylor_and_Karl_2001) to facilitate the comparison of various the models at a certain station.

<!--
pandoc --standalone --smart \
       --bibliography ../references/references.bib \
       --reference-docx=reference.docx \
       --from markdown MTS-IEEE.md\
       --to docx \
       --output MTS-IEEE.docx
-->
