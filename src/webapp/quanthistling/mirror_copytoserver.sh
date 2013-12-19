#!/bin/sh
QUANTHISTLINGPATH=/Users/pbouda/Projects/svn-googlecode/qlc/src/webapp/quanthistling

cd $QUANTHISTLINGPATH/quanthistling/public/downloads
scp -i ~/.ssh/id_rsa.strato2 *.zip pbouda@h1951206.stratoserver.net:/var/www/quanthistling-new/quanthistling/public/downloads/
scp -i ~/.ssh/id_rsa.strato2 xml/*.zip pbouda@h1951206.stratoserver.net:/var/www/quanthistling-new/quanthistling/public/downloads/xml/
scp -i ~/.ssh/id_rsa.strato2 csv/*.zip pbouda@h1951206.stratoserver.net:/var/www/quanthistling-new/quanthistling/public/downloads/csv/
scp -i ~/.ssh/id_rsa.strato2 csv/*.csv pbouda@h1951206.stratoserver.net:/var/www/quanthistling-new/quanthistling/public/downloads/csv/
scp -i ~/.ssh/id_rsa.strato2 txt/*.zip pbouda@h1951206.stratoserver.net:/var/www/quanthistling-new/quanthistling/public/downloads/txt/
cd $QUANTHISTLINGPATH
