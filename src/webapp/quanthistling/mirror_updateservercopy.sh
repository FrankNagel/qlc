#!/bin/bash

cd /var/www/quanthistling-new
svn update

sudo -u postgres psql quanthistling < /var/www/quanthistling-new/quanthistling/public/downloads/pgdump_quanthistling.sql
