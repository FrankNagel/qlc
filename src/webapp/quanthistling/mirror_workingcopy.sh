#!/bin/bash

cd /media/Daten/Projects/svn-strato/quanthistling/python/quanthistling
python scripts/export_all_static_data.py development.ini
bash scripts/exportcsv.sh
cd /media/Daten/Projects/svn-strato/quanthistling/python/quanthistling/quanthistling/public
pg_dump -h localhost -U postgres -c quanthistling > pgdump_quanthistling.sql
svn commit -m "Automatic update of public folder (mirror_workingcopy.sh)"