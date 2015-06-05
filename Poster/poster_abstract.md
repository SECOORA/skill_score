Title: An end-to-end Workflow for Assessing Sea Surface Temperature, Salinity and
Water Level Predicted by Coastal Ocean Models.

Authors: Filipe Fernandes, Richard Signell, Vembu Subramanian, Debra Hernandez

Abstract

To assess the performance of ocean forecast models, simulations need to be
compared with data.  Finding what models and data exist at a certain point in
time and space has historically been challenging because this information is
held and distributed by numerous providers in different formats.  Accessing data
has been challenging because ocean models produce terabytes of information, is
usually stored in binary data formats like HDF or NetCDF, while ocean
observations are often stored in scientific data formats or in databases.  To
solve this problem, the Southeast Coastal Ocean Observing Regional Association
(SECOORA) has been building a distributed information system based on standard
IOOS-supported web services for discovery and access.

An end-to-end (search-access-analyze-visualize) workflow for assessing SST,
SSS, and SSH is shown in the poster.  The time-series are sampled at every
30 min and the assessment is performed via linear Pearson correlations.  The
SSH is also compared to a mean surface bias, in order to access which models
can be compared to a NAVD88 datum.

The SECOORA skill score assessment uses automatic discoverable data to create
weekly time-series of Sea Surface Temperature (SST), Sea Surface Salinity (SSS),
and Sea Surface Height (SSH) comparisons of modeled and observed data.  The
data is acquired using OWSLib for CSW Catalog access, Iris for ocean model
access and pyoos for Sensor Observation Service data access.

Analysis and visualization is done with Pandas (time-series) and Folium
(interactive maps), and the entire workflow is shared as in IPython Notebooks.
