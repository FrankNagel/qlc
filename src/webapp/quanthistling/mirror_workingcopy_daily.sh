#!/bin/bash

cd /media/Daten/Projects/svn-googlecode/qlc/src/webapp/quanthistling
python scripts/export_all_static_data_daily.py development.ini
bash scripts/exportcsv.sh

cd /media/Daten/Projects/svn-googlecode/qlc/src/webapp/quanthistling/quanthistling/public/downloads
pg_dump -h localhost -U postgres -c quanthistling > pgdump_quanthistling.sql
scp -r * peterbouda.de:/var/www/quanthistling-new/quanthistling/public/downloads/
