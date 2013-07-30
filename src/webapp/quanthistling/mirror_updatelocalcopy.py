# -*- coding: utf8 -*-

import os
import urllib2
import re
import codecs
from zipfile import ZipFile
from subprocess import call 

POSTGRES_BIN_PATH = "C:\\Program Files (x86)\\PostgreSQL\\8.4\\bin"
#POSTGRES_BIN_PATH = "/usr/local/bin"

print("Downloading dump file...")
response = urllib2.urlopen('http://www.quanthistling.info/data-full/downloads/pgdump_quanthistling.zip')
output = open("pgdump_quanthistling.zip", "wb")
output.write(response.read())
output.close()

print("Extracting dump file...")
myzip = ZipFile("pgdump_quanthistling.zip", "r")
myzip.extractall()
myzip.close()

r = re.compile("pbouda")
in_file = codecs.open("pgdump_quanthistling.sql", "r", "utf-8")
out_file = codecs.open("pgdump_quanthistling2.sql", "w", "utf-8")
for line in in_file:
    new_line = r.sub("postgres", line)
    out_file.write(new_line)
in_file.close()
out_file.close()

print("Inserting data into database...")
call([os.path.join(POSTGRES_BIN_PATH, "psql"), "-Upostgres", "quanthistling"], stdin=open("pgdump_quanthistling2.sql", "r"))