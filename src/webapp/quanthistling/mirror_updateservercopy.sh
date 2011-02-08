#!/bin/bash

cd /var/www/quanthistling
svn update

sudo -u postgres psql quanthistling < /var/www/quanthistling/quanthistling/public/pgdump_quanthistling.sql
