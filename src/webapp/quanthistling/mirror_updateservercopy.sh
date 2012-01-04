#!/bin/bash

cd /var/www/quanthistling-new
svn update

unzip -fo /var/www/quanthistling-new/quanthistling/public/downloads/pgdump_quanthistling.zip -d /var/www/quanthistling-new/quanthistling/public/downloads/
sudo -u postgres psql quanthistling < /var/www/quanthistling-new/quanthistling/public/downloads/pgdump_quanthistling.sql
