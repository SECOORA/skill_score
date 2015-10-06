# Model Skill Assessment -- Fourth Quarter Report
## (February 28, 2014 -- May 31, 2014)

This report outlines the tasks performed in the fourth quarter for the Southeast Coastal Ocean Observing Regional Association (SECOORA) Model Skill Assessment.

## Task 1: Continued run/update of weekly data acquisition

SECOORA serves terabytes of model and data online every month.
It is virtually impossible to browse and evaluate any of those model without an automate tool.

In order to help users find the best available simulation for a certain time/region we evaluate the Numerical Ocean Models (NOC) by reducing them to a statistically meaningful measure of model performance (or  skill).

To calculate the skill we fetch model state variables and the matching observations for:
Sea Surface Height (SSH), Temperature (SST), Salinity (SSS), and Velocity (SSV).
The observed data are paired with the nearest water grid point of various NOCs.
The paired data are run through a simple Quality Assurance and Quality Control (QA/QC) routine and then stored in time-series of station-like weekly.
The QA/QC consists of spikes removal and clipping the data to minimum and maximum expected threshold.
Finally the models performance are assessed and the data is represented as time-series,
horizontal or vertical slices in an interactive map (Figure 1).

![Figure 1: Interactive map.](images/ssh_map.png)
Figure 1: Interactive map showing all SECOORA stations.
The observed and modeled series, and the skill  are shown when clicked.

Depending on the model, the horizontal coordinate of the output data may be on a regular,
curvilinear, or unstructured grid,
while the vertical coordinates may be on a uniform or non-dimensional grid with a number of different possibilities (e.g., sigma, s-coordinate, isopycnal, etc).
That complex matrix of possibilities can only be tackled by leveraging with the Data Management and Communications (DMAC) Subsystem for discoverable and accessible data,
and information across all the Regional Associations that forms the Integrated Ocean Observing System (IOOS).
Thanks to IOOS technologies and standards, a
nd making use of Common Data Models (CDM) the user inputs are reduced to the date range,
bounding box, and variable name only.
All the data is automatically discovered and downloaded in the `00-fetch_data.ipynb` notebook.

The CDM interpreter of choice is the UK Met Office Iris (@Iris_2010).
Iris can read and load into its CDM format any data that abides to the CF-1.6 conventions.
However, Iris performance with ocean models grids and non-dimension vertical coordinates are lacking.
To increase the interoperability we created a wrapper module named `tardis` which allows to access the output of various models with minimal code customization.

The data endpoints for the download are discovered using the NOAA Catalog Service Web ([CSW](http://www.ngdc.noaa.gov/geoportal/csw)).
Using the CSW endpoints helped normalize service specifications.
Note that we do hard-code some of the SECOORA endpoints to ensure they are always downloaded.

Once the endpoints are found we choose to download model data via the more robust OPeNDAP (Open-source Project for a Network Data Access Protocol).
The observations are downloaded via a mix of SOS (Sensor Observational Service) and OPeNDAP endpoints from the SECOORA Thematic Real-time Environmental Distributed Data Services (THREDDS) catalog.


### Issues found

- The catalog search cannot tell the difference between model and satellite products due to the misuse of the `coverage_content_type` metadata.
  Most of satellite data are wrongly tagged as `modelResult` making it difficult to create horizontal slices comparisons.
  (See https://github.com/ioos/secoora/issues/184).
- The glider data available in the Glider DAC is usually not available at the same times of the weekly runs.
- HF-radar is fetched using the HFRNet endpoints for 6 km data (http://hfrnet.ucsd.edu/thredds/dodsC/HFRNet/USEGC/6km/hourly/RTV).
  The comparisons are visual overlays of model and HF-radar data for horizontal slices.
  The SSV time-series on the other hand do discover any other source of velocity data available.

### Next steps

- We propose to create a list of satellite data endpoints available and hard-code them in the same fashion used for the SECOORA platform THREDDS,
  avoid bogus model comparisons.
- The notebooks for fetching, and plotting glider data are ready.
  However, the matching logic must be reversed to find model at the glider times and not for the weekly runs.
- The HF-radar data horizontal slices comparisons are limited to models with rectangular grids (`rgrid`).
  Models that use unstructured grids (ugrid), like FVCOM and staggered grids (sgrid),
  like ROMS, still need some work to yield valid velocity comparison.

## Task 2) Calculation of the scores

Model and observations are only considered for comparison when the distance between the station and the nearest model grid point is less than 5 km.
The skill scores computed are the Model Bias (MB),
Centered Root Mean Square Error (CRMSE),
and Cross Correlation (R2) akin to @Wilkin_and_Hunter_2013 (See notebook `01-skill_score.ipynb` for the code details).
The results are saved as HTML tables and displayed in the interactive map (Figure 2).

![Figure 2: HTML table example displaying the SSH bias.](images/bias.png)
Figure 2: HTML table example displaying the SSH bias.

Model skill may be low because of high noise in the data,
or it may artificially high due to correlated properties in the model and data,
e.g. tides for example (@Hetland_2006).
To avoid hindering phenomena like storm surges, we computed the skills twice:
first against the original series, then again using a low-pass 40 hours Lanczos filter to remove the tides (@Duchon_1979).
All the series are re-sampled at 3 hours intervals to reduce the noise in the observations and create a consistent time interval for all models.
Because most coastal ocean models are quite skillful to predict tides,
due to the use of independent tidal harmonic as boundary conditions,
only the filtered skill score is reported in the interactive map.

In addition to the scores the notebook outputs a Taylor Diagram (TD) (@Taylor_and_Karl_2001).
TD helps to summarize the scores and facilitate the comparison of various the models at a certain station (Figure 3).

![Figure 3: Taylor diagram example.](images/8727520.png)
Figure 3: Taylor diagram example.

### Issues found

- A small portion of the models are only available in time intervals greater than 3 hours,
  rendering the comparisons against a 3-hours binned useless.
- The Lanczos filter might be filtering some signals of interested,
  like inertial oscillations.
  A harmonic analysis would be more adequate for filtering the tides.
  However, because the weekly series are too short, we cannot perform harmonic analysis.

### Next steps

- Find each model time resolution and calculate the skill against the minimum possible time interval.
- Save longer time-series (> 30 days) and filter the tides using harmonic analysis instead of a Lanczos filter.
- Create a skill based on the rotatory spectra to evaluate the inertial oscillations in the model.

## Task 3) Interactive web-page

The interactive web-page is hosted in the URL: http://ocefpaf.github.io/secoora.
It is still a proof of concept maintained as an exercise on how to display future results.
The user cannot control data-fetching right now due to the high bandwidth demand of the auto-discovered data.
We can increase the pre-fetched data time-range to allow for some online users interactivity.

### Issues found

- The interactivity is limited to choosing stations and hovering/zooming in the data.
  The skill, time-range, and data variable is pre-selected.
  A proof of concept for more interactivity can be see here in the `Interaction.ipynb` notebook (Figure 4).

![Figure 4: Proof of concept for the interactive widget.](images/mockup.png)
Figure 4: Proof of concept for the interactive widget.

### Next steps

- Improve the user interactivity creating a Flask App version of the `Interaction.ipynb`.
- Integrate the results site into the SECOORA portal and adapt the CSS layout to match that of the other SECOORA products.
- Integrate the scores calculation with `sci-wms` for more online interactivity.

## Summary

During this project a model scoring with automatic discovery of data was developed.
In addition two standalone python libraries (`tardis` and `utilities`) were developed to facilitate the data discovery,
cleaning and processing steps, and an interactive website is used to display the results.
The next step is to coordinate with Axiom as to integrate the skill score webpage into SECOORA website.

# References
