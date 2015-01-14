#!/bin/bash

# TODO: Create a Makefile.

# Remove all iso records from WAF.
rm -rf iso_records

# Remove all records from SQLITE3 database.
# sqlite3 /var/www/pycsw/tests/suites/cite/data/records.db 'delete from records'.
pycsw-admin.py -c delete_records -f default.cfg -y

# Harvest new iso records into WAF.
python get_iso.py

# load new records into database.
pycsw-admin.py -c load_records -p iso_records -f default.cfg -r
