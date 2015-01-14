import logging
import logging.handlers


def start_logging(fname='iso_harvest.log'):
    logger = logging.getLogger('thredds_crawler')
    fh = logging.handlers.RotatingFileHandler(fname, maxBytes=1024*1024*10,
                                              backupCount=5)
    fh.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)
    return logger


def csv2dict(fname):
    with open(fname, mode='r') as f:
        reader = csv.reader(f)
        servers = {rows[0]: rows[1] for rows in reader}
    return servers


if __name__ == '__main__':
    import os
    import csv
    from urllib import urlretrieve
    from thredds_crawler.crawl import Crawl

    logger = start_logging()
    SAVE_DIR = "iso_records"
    THREDDS_SERVERS = csv2dict('THREDDS_SERVERS.csv')

    for subfolder, thredds_url in THREDDS_SERVERS.items():
        logger.info("Crawling %s (%s)" % (subfolder, thredds_url))
        crawler = Crawl(thredds_url, debug=True)
        isos = [(d.id, s.get("url")) for d in crawler.datasets for
                s in d.services if s.get("service").lower() == "iso"]
        filefolder = os.path.join(SAVE_DIR, subfolder)
        if not os.path.exists(filefolder):
            os.makedirs(filefolder)
        for iso in isos:
            try:
                filename = iso[0].replace("/", "_") + ".iso.xml"
                filepath = os.path.join(filefolder, filename)
                logger.info("Downloading/Saving %s" % filepath)
                urlretrieve(iso[1], filepath)
            except BaseException:
                logger.exception("Error!")
