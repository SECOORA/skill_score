# -*- coding: utf-8 -*-
#
# glider_erddap_example.py
#
# purpose:  Download glider data from ERDDAP
# author:   Filipe P. A. Fernandes
# e-mail:   ocefpaf@gmail
# web:      http://ocefpaf.github.io/
# created:  31-Oct-2014
# modified: Fri 31 Oct 2014 10:50:30 AM BRT
#
# obs:
#

from datetime import datetime, timedelta
from pull_gliderdata_erddap import glider_dataset, glider_request

STARTDATETIME = datetime.now() - timedelta(days=14)
ENDDATETIME = STARTDATETIME + timedelta(days=7)

params = dict(MINLON=-80,
              MAXLON=-59.8,
              MINLAT=32,
              MAXLAT=46,
              STARTDATETIME=STARTDATETIME,
              ENDDATETIME=ENDDATETIME)

fnames = glider_dataset(**params)

for fname in fnames:
    fname += '.ncCFMA'
    r = glider_request(fname=fname, **params)
    fname = ''.join(fname.split('.')[:-1]) + '.nc'
    with open(fname, 'wb') as f:
        print(fname)
        f.write(r.content)
