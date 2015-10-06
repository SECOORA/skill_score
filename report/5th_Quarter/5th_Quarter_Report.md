# System-test -- First Quarter Report
## (June 1, 2015 -- August 31, 2015)

This report outlines the tasks performed in the first quarter.

## Task 1: IOOS System Integration Test webpage/blog

The System Integration Test (SIT) webpage [1] is online and the first post explaining the page goals is up [2].
The posts will be added on a weekly basis and the next three are ready to be uploaded.
The basic workflow is to parse the IPython notebooks created during the SIT and then publish those them files as a GitHub project page.
The notebooks are converted to HTML using IPython's own `nbconvert` and the HTML is parsed by a static blog generator, Pelican, via a Pelican IPython-notebooks plug-in.
The site configuration can be tweaked by changing the `pelicanconf.py` file and the publishing options in the `publishconf.py`.
Note that while the actual publish HTML is hosted on GitHub its version control is meaningless.
The HTML is overwritten at every new push.
One should follow the changes of the notebooks and configuration on the master branch to keep track of the changes.

The main difficulty found while creating the page was to update and run the old SIT notebooks.
The problems ranged from Software version changes, convoluted coding, long notebooks with unclear goals, etc.
The notebooks have to be re-written in order to be converted into a clean and meaningful webpage.
The blog version of the notebooks will be broken into smaller pieces to better convey a code/story information.

To avoid similar problems in the future we created a single `environment.yml` [3] that generates a ready-to-deploy `conda` environment.
The environment is easy to install and has pinned-down versions that are known to work for both the notebooks and the blog creation.
In addition to the single run-environment we are creating a Python IOOS module [4].
The goal is to gather all the classes, functions, and code snippets created during the SIT and make them available in a single Python module.
This practice avoid code fragmentation, improve bug fixes, ensure code provenance, and will help the user to run the notebooks.

In order to make this reproducible we version control the notebooks, the environment, and the IOOS Python module.
Still, many notebooks result will vary due to data availability at the run time.
Not to mention notebooks that fetch data using a relative date.
To reduce this issue all the notebooks will be committed with a run date, log, and the results (figures, data, etc).
This practice is not ideal, but allow some comparison between different runs.

The notebooks in the webpage are executable online.
Users can run and make changes without any prerequisite but a web-browser.
The aim is to reduce the entry level.  However, installing the whole software stack in a local machine is still an option.
(Installation and setting an environment up will be addressed in future post.)

Running the notebooks online is possible via an experimental service named `binder` [5].
To try binder out just click on the link below and run the next post.
It is important to note that binder uses the same `environment.yml` created for the project.
Everything is installed using conda and the IOOS channel in a temporary docker instance.
That way we can assure that the online version will be identical to any environment create locally.
Binder is an open source project, meaning that, if their service is interrupted we can/should consider hosting our own instance.

[1] http://ioos.github.io/system-test/
[2] https://ioos.github.io/system-test/blog/2015/09/28/OpeningPost/
[3] https://github.com/ioos/system-test/blob/master/environment.yml
[4] https://github.com/pyoceans/utilities/blob/master/utilities/ioos.py
[5] http://mybinder.org/repo/ioos/system-test/

## Task 2: Support current and continue developing important software packages to the IOOS enterprise

The IOOS enterprise is concerned with the software stack sustainability.
To address that we started a GitHub repository to discuss the state of the software APIs developed under the IOOS umbrella [1].
Two projects already start due to the discussions that took place. The Ocean Dimensionless Vertical Coordinates (odvc) [2] and Isosurfaces (iso) [3].
Both projects have a single goal: provide a the simplest, and in the most canonical possible way, to perform a single purpose task.
The `odvc` module contains ocean vertical coordinates equations to compute the dimensioned version of the coordinates whereas `iso` provides means to
perform horizontal slices in any kind of ocean model grid.

Two other projects that started before APIRUS but have the same goals are `tardis` [4] and `cf_units` [5].
The `cf_units` provides an interface to units CF-conventions via UDUNITS.
The module can be considered stable and is ready for production and it is used by IOOS `compliance-checker`.
The latest version extended support to Python 3, making it possible for more third party modules to use `cf_units`.
The `tardis` main objective is to provide means for arbitrary time/space slices, like virtual glider trajectories, in ocean model results.
These three projects are not ready for production and there is ongoing discussion regarding the API and how to use them as plug-in in CDMs.


To maximize external contributions we are planning and testing the new modules in `APIRUS`.
It is worth mentioning that some of the projects got the attention of external developer.
The UK Met office iris developers, for example, are interested and a collaborating to foster some these modules.

Issues that need resolving:

- Re-write the iso surface Fortran code or find a proper way to license the current code;
- Implement a grid agnostic way for tardis to find and plot glider trajectories;
- Find a clear API to tie together pysgrid, pyugrid and odvc to provide a dimensioned z-coordinate in all grids;

The IOOS enterprise needs a sustainable way to not only develop, but also deploy its software stack.
In an effort to ensure a deployment sustainability we developed and maintain a continuous distribution of packages binaries [6].
The packages are built for OSX, Linux-64, and Windows 32/64 platforms.
The distribution is in the form of the popular python packaging system anaconda [7].
The channel is update constantly to host the latest versions of the software stack.
Each binary is tested against its dependencies before making its way to the channel to secure stability.
At the moment all builds are automated and managed via GitHub PRs.


[1] https://github.com/ioos/APIRUS
[2] https://github.com/pyoceans/odvc
[3] https://github.com/pyoceans/iso
[4] https://github.com/pyoceans/tardis
[5] https://github.com/SciTools/cf_units
[6] https://github.com/ioos/conda-recipes/pulls
[7] http://anaconda.org/ioos

## Task 3: Perform documentation/planning/testing to further mature the projects and maximize the likelihood of external contributions

This task is an intrinsic part of tasks 1 and 2.
The SIT webpage creation is self-documented and its main goal is to maximize external contributions.
The APIRUS repository was created with the intention to be a place for planning and testing software.
All the modules that already originated from this effort are fully documented with docstrings and, once they are complete, the creation of manual pages will be trivial.
However, since we know that documentation alone is not enough, we will be posting usage examples in the SIT webpage.

<!-- geometry: margin=1in -->

<!--
pandoc --standalone --smart \
       --bibliography ../references/references.bib \
       --reference-docx=reference.docx \
       --from markdown 5th_Quarter_Report.md \
       --to docx \
       --output 5th_Quarter_Report.docx
-->

<!--
pandoc --standalone --smart \
       --bibliography ../references/references.bib \
       --from markdown 5th_Quarter_Report.md \
       --to latex \
       --latex-engine=xelatex \
       --output 5th_Quarter_Report.pdf
-->
