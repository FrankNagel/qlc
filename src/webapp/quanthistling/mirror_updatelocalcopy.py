# -*- coding: utf8 -*-

import os, urllib2
from zipfile import ZipFile
from subprocess import call 

POSTGRES_BIN_PATH = "C:\\Program Files (x86)\\PostgreSQL\\8.4\\bin"
#POSTGRES_BIN_PATH = "/usr/local/bin"

print("Downloading dump file...")
response = urllib2.urlopen('http://www.cidles.eu/quanthistling/downloads/pgdump_quanthistling.zip')
output = open("pgdump_quanthistling.zip", "w")
output.write(response.read())
output.close()

print("Extracting dump file...")
myzip = ZipFile.open("pgdump_quanthistling.zip", "r")
myzip.extractall()
myzip.close()

print("Inserting data into database...")
call([os.path.join(POSTGRES_BIN_PATH, "psql"), "-Upostgres", "quanthistling"], stdin=open("pgdump_quanthistling.sql", "r"))