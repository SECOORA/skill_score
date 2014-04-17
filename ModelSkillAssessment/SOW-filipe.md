<!--
pandoc --standalone --smart \
       --bibliography ../references/references.bib \
       --from markdown SOW.md \
       --to docx \
       --output SOW-filipe.docx
-->

<!--
pandoc --standalone --smart \
       --latex-engine=xelatex \
       --bibliography ../references/references.bib \
       --from markdown SOW.md \
       --to latex \
       --output SOW-filipe.pdf
-->

## STATEMENT OF SERVICES REQUIRED

### Statement of Work

The following statement of work describes the activities, deliverables, and
timeline for the development of a draft on-line framework to assess the
numerical model skill.

1. Load the various models and observations made by SECOORA in a standardized
   fashion.  Including *in-situ* observations like HF-radar, gliders, and
   model outputs.
2. Provide a comprehensive skill assessment error metrics for both observations
   and models in a similar manner as @Wilkin_and_Hunter_2013.
3. All the loading and processing will be in the format of IPython notebooks
   making use of cf-compliant data and observation in order to produce
   reproducible results.
4. All deliverables will be in the format of version controlled code hosted at:
   https://github.com/ocefpaf/secoora.git.  All code will be properly
   documented and accompanied by examples.

The work will be done remotely be the contractor and the period of performance
will be from XX to XX.
