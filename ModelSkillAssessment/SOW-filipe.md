---
title: STATEMENT OF SERVICES REQUIRED
author:
    - Filipe Pires Alvarenga Fernandes, MSc
    - Prof. at Centro Universitário Monte Serrat
header-includes:
    - \usepackage{fancyhdr}
    - \pagestyle{fancy}
    - \fancyhead[CO,CE]{}
    - \fancyfoot[CO,CE]{}
    - \fancyfoot[LE,RO]{\thepage}
...
<!-- geometry: margin=1in -->

## Statement of Work


The following statement of work describes the activities, deliverables, and
timeline for the development of a draft on-line framework to assess the
numerical model skill.

1. Identify, select and work out the access to the numerical models and
   observations in the SECOORA region in a standardized fashion.  This
   includes *in-situ* and HF Radar observations and other available such as
   gliders, and model data.
2. Development of Work Flow and discuss the same with SECOORA RCOOS Manager
   and SECOORA RCOOS PIs via SECOORA RCOOS PIs May Meeting (May 13, 2014 ).
3. Provide a comprehensive skill assessment error metrics for both observations
   and models in a similar manner as  @Wilkin_and_Hunter_2013.
4. All the loading and processing will be in the format of IPython notebooks
   making use of cf-compliant data and observation in order to produce
   reproducible results.
5. All deliverables will be in the format of version controlled code hosted at:
   https://github.com/ocefpaf/secoora.git. All code will be properly documented
   and accompanied by examples in a SECOORA website.
6. Occasional agreed upon participation in SECOORA monthly RCOOS PIs (Once a
   Quarter) calls and a monthly call with SECOORA RCOOS Manager to demonstrate
   the progress on the work.

The period of performance of above activities will be from May 1, 2014 to April
30, 2015.

<!--
pandoc --standalone --smart \
       --bibliography ../references/references.bib \
       --from markdown SOW-filipe.md \
       --to docx \
       --output SOW-filipe.docx
-->

<!--
pandoc --standalone --smart \
       --latex-engine=xelatex \
       --bibliography ../references/references.bib \
       --from markdown SOW-filipe.md \
       --to latex \
       --output SOW-filipe.pdf
-->
