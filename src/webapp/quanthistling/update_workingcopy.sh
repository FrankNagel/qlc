#!/bin/bash

cd /media/Daten/Projects/svn-strato/quanthistling/python/quanthistling
python scripts/importdictdata.py development.ini
python scripts/updateversion.py development.ini