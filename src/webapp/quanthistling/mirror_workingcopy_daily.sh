#!/bin/bash
QUANTHISTLINGPATH=/home/pbouda/Projects/svn-googlecode/qlc/src/webapp/quanthistling

cd $QUANTHISTLINGPATH
#python scripts/filter_entries.py development.ini
python scripts/export_all_static_data.py development.ini

cd $QUANTHISTLINGPATH/quanthistling/public/downloads
pg_dump -U postgres -c quanthistling > pgdump_quanthistling.sql
zip -uj pgdump_quanthistling.zip pgdump_quanthistling.sql

cd $QUANTHISTLINGPATH
