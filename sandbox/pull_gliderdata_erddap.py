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
from requests.exceptions import HTTPError


URL = "http://erddap.marine.rutgers.edu/erddap/tabledap"


def convert_dates(date):
    """
    Take a datetime object or an ISO8601 date string and return a formatted
    date string for ERDDAP URLs.

    Examples
    --------
    >>> convert_dates(datetime(2014, 10, 31, 12))
    '2014-10-31T12:00:00Z'
    >>> convert_dates('2011-12-31 23:00:00Z')
    '2011-12-31T23:00:00Z'

    """
    erddap_date_string = "{:%Y-%m-%dT%H:%M:%SZ}".format

    if isinstance(date, str):
        date = iso8601.parse_date(date)
    return erddap_date_string(date)


def download(response, fname):
    """Download file with a progress bar if total_length is known."""
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


def parse_url(url):
    """Return requests object for a ERDDAP URL."""
    r = requests.get(url, stream=True)
    unquoted = requests.utils.unquote(r.url)
    try:
        r.raise_for_status()
    except HTTPError as e:
        e.message += '\n [ERDDAP URL] {}'.format(unquoted)
        raise HTTPError(e.message)
    return r


def glider_request(fname, **kw):
    """
    Return a request object for ERDDAP glider **data** download.

    Parameters
    ----------
    fname : string
            Usually the result of `glider_dataset()`

    kw :  dict
          `MINLON`, `MAXLON`, `MINLAT`, `MAXLAT`,
          `STARTDATETIME`, `ENDDATETIME`.

    Returns
    -------
    r : requests object
        Valid downloaded ERDDAP URL.
    """

    kw['STARTDATETIME'] = convert_dates(kw['STARTDATETIME'])
    kw['ENDDATETIME'] = convert_dates(kw['ENDDATETIME'])

    url = '/'.join(s.strip('/') for s in [URL, fname])
    params = ("?time,latitude,longitude,depth,pressure,profile_id,"
              "salinity,temperature"
              "&longitude>={MINLON}"
              "&longitude<={MAXLON}"
              "&latitude>={MINLAT}"
              "&latitude<={MAXLAT}"
              "&time>={STARTDATETIME}"
              "&time<={ENDDATETIME}".format)

    url += params(**kw)
    r = parse_url(url)

    content = r.headers['Content-Type']
    if 'download' in content:
        return r
    else:
        raise ValueError('No data found in URL {}'.format(r.url))


def glider_dataset(fname='allDatasets.json', **kw):
    """
    Return a list of glider data files, suitable for glider_request, within the
    requested parameters.

    Parameters
    ----------
    fname : string
            Hardcoded to 'allDatasets.json'!

    kw :  dict
          `MINLON`, `MAXLON`, `MINLAT`, `MAXLAT`,
          `STARTDATETIME`, `ENDDATETIME`.

    Returns
    -------
    fnames : list
             List of file names.
    """

    kw['STARTDATETIME'] = convert_dates(kw['STARTDATETIME'])
    kw['ENDDATETIME'] = convert_dates(kw['ENDDATETIME'])

    url = '/'.join(s.strip('/') for s in [URL, fname])
    params = ("?datasetID"
              "&maxLongitude>={MINLON}"
              "&minLongitude<={MAXLON}"
              "&maxLatitude>={MINLAT}"
              "&minLatitude<={MAXLAT}"
              "&maxTime>={STARTDATETIME}"
              "&minTime<={ENDDATETIME}".format)

    url += params(**kw)
    r = parse_url(url)

    if 'json' in r.headers['Content-Type'].lower():
        table = json.loads(r.content)
        fnames = table['table']['rows']
        fnames = [item for sublist in fnames for item in sublist]  # Flat list.
        return fnames
    else:
        raise ValueError('Cannot find data table in  URL {}'.format(r.url))


def main(args):
    defaults = dict(MINLON=-80.0,
                    MAXLON=-59.8,
                    MINLAT=+32.0,
                    MAXLAT=+46.0,
                    STARTDATETIME=datetime.now() - timedelta(days=14),
                    ENDDATETIME=datetime.now() - timedelta(days=7))

    bbox = args.get('--bbox', None)
    if bbox:
        MINLON, MAXLON, MINLAT, MAXLAT = bbox.split(',')
        defaults.update(MINLON=MINLON, MAXLON=MAXLON,
                        MINLAT=MINLAT, MAXLAT=MAXLAT)

    time = args.get('--time', None)
    if time:
        STARTDATETIME, ENDDATETIME = time.split(',')
        defaults.update(STARTDATETIME=STARTDATETIME, ENDDATETIME=ENDDATETIME)

    fnames = glider_dataset(**defaults)
    for fname in fnames:
        fname += '.mat'
        r = glider_request(fname=fname, **defaults)
        download(r, fname)

if __name__ == "__main__":
    if True:
        args = docopt(__doc__, version='0.1.0')
        main(args)
