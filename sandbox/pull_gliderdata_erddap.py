#!/usr/bin/env python

__doc__ = """
Download glider data.

Usage:
    pull_gliderdata_erddap.py [--bbox=<MINLON>,<MAXLON>,<MINLAT>,<MAXLAT> \
--time=<STARTDATETIME>,<ENDDATETIME>]

    pull_gliderdata_erddap (-h | --help | --version)

Examples:
    pull_gliderdata_erddap.py --bbox=-80,-59.8,32,46
    pull_gliderdata_erddap.py --time=2014-10-09T12:00:00Z,2014-10-16T12:00:00Z
    pull_gliderdata_erddap.py --time=2014-10-09T12:00:00Z,2014-10-16T12:00:00Z\
 --bbox=-80,-59.8,32,46


Options:
  -h --help     Show this screen.
  --version     Show version.
  --bbox=<MINLON>,<MAXLON>,<MINLAT>,<MAXLAT> Bounding Box \
[default: -80,-59.8,32,46].
  --time=<STARTDATETIME>,<ENDDATETIME> [default: Previous Week]
"""

# Standard library.
import sys
import json
from datetime import datetime, timedelta

# Third party.  (Available ad PyPI.)
import iso8601
import requests
from docopt import docopt


def validate_iso(iso_date):
    iso8601.parse_date(iso_date)


def convert_dates(date):
    fmt = "{:%Y-%m-%dT%H:%M:%SZ}".format
    if isinstance(date, str):
        validate_iso(date)
        return date
    elif isinstance(date, datetime):
        return fmt(date)
    else:
        raise ValueError("convert_dates() expects `string` or `datetime`"
                         "objects.  Got {!r}".format(date))


def flatten_list(lista):
    return [item for sublist in lista for item in sublist]


def download(response, fname):
    with open(fname, "wb") as f:
        print("Downloading %s" % fname)
        total_length = response.headers.get('content-length')
        if total_length is None:
            f.write(response.content)
        else:
            dl = 0
            total_length = int(total_length)
            for data in response.iter_content():
                dl += len(data)
                f.write(data)
                done = int(50 * dl / total_length)
                sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)))
                sys.stdout.flush()


def glider_request(url="http://erddap.marine.rutgers.edu/erddap/tabledap",
                   fname=None, **kw):
    """Return an URL for glider **data** request."""
    url = '/'.join(s.strip('/') for s in [url, fname])
    params = ("?time,latitude,longitude,depth,pressure,profile_id,"
              "salinity,temperature"
              "&time<={ENDDATETIME}"
              "&time>={STARTDATETIME}"
              "&latitude>={MINLAT}"
              "&latitude<={MAXLAT}"
              "&longitude>={MINLON}"
              "&longitude<={MAXLON}".format)

    url += params(**kw)
    # TODO: *Future version request will support >=, <=.
    # FIXME: *r = requests.get(url, params=params)
    r = requests.get(url, stream=True)
    if r.status_code != 200:
        print('\n[URL]: {}\n'.format(requests.utils.unquote(r.url)))
        r.raise_for_status()
    content = r.headers['Content-Type']
    if 'download' in content:
        return r
    else:
        raise TypeError('Bad URL {}'.format(r.url))


def glider_dataset(url='http://erddap.marine.rutgers.edu/erddap/tabledap',
                   fname='allDatasets.json',
                   **kw):
    """Return an URL for glider data **info** request."""
    url = '/'.join(s.strip('/') for s in [url, fname])
    params = ("?datasetID"
              "&minTime<={ENDDATETIME}"
              "&maxTime>={STARTDATETIME}"
              "&maxLatitude>={MINLAT}"
              "&minLatitude<={MAXLAT}"
              "&maxLongitude>={MINLON}"
              "&minLongitude<={MAXLON}".format)

    url += params(**kw)
    r = requests.get(url)
    unquoted = requests.utils.unquote(r.url)
    r.raise_for_status()
    if 'json' in r.headers['Content-Type'].lower():
        table = json.loads(r.content)
        fnames = table['table']['rows']
        fnames = flatten_list(fnames)
        return fnames
    else:
        raise TypeError('Bad URL {}'.format(unquoted))


def main(args):
    # Defaults.
    STARTDATETIME = datetime.now() - timedelta(days=14)
    ENDDATETIME = STARTDATETIME + timedelta(days=7)

    defaults = dict(STARTDATETIME=convert_dates(STARTDATETIME),
                    ENDDATETIME=convert_dates(ENDDATETIME),
                    MINLAT=32, MAXLAT=46, MINLON=-80, MAXLON=-59.8)

    # Parse args.
    kw = dict()
    bbox = args.get('--bbox', None)
    time = args.get('--time', None)
    if bbox:
        MINLON, MAXLON, MINLAT, MAXLAT = bbox.split(',')
        kw.update(MINLON=MINLON, MAXLON=MAXLON,
                  MINLAT=MINLAT, MAXLAT=MAXLAT)
    if time:
        STARTDATETIME, ENDDATETIME = time.split(',')
        kw.update(STARTDATETIME=STARTDATETIME, ENDDATETIME=ENDDATETIME)

    defaults.update(kw)  # Handling default with dict().update.

    fnames = glider_dataset(**defaults)
    for fname in fnames:
        fname += '.mat'
        r = glider_request(fname=fname, **defaults)
        download(r, fname)

if __name__ == "__main__":
    if True:
        args = docopt(__doc__, version='0.1.0')
        main(args)

    if False:  # Example to run from another script.
        from pull_gliderdata_erddap import glider_dataset, glider_request
        STARTDATETIME = datetime.now() - timedelta(days=14)
        ENDDATETIME = STARTDATETIME + timedelta(days=7)

        params = dict(STARTDATETIME=convert_dates(STARTDATETIME),
                    ENDDATETIME=convert_dates(ENDDATETIME),
                    MINLAT=32, MAXLAT=46, MINLON=-80, MAXLON=-59.8)

        url = 'http://erddap.marine.rutgers.edu/erddap/tabledap'
        fnames = glider_dataset(url=url, fname='allDatasets.json', **params)
        for fname in fnames:
            fname += '.mat'
            r = glider_request(fname=fname, **params)
            download(r, fname)
