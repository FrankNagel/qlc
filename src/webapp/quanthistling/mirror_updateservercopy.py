from zipfile import ZipFile
from subprocess import call 

call("svn", "update")

print("Extracting dump file...")
myzip = ZipFile("/var/www/quanthistling-new/quanthistling/public/downloads/pgdump_quanthistling.zip", "r")
myzip.extractall("/var/www/quanthistling-new/quanthistling/public/downloads/")
myzip.close()

r = re.compile("pbouda")
in_file = codecs.open("/var/www/quanthistling-new/quanthistling/public/downloads/pgdump_quanthistling.sql", "r", "utf-8")
out_file = codecs.open("/var/www/quanthistling-new/quanthistling/public/downloads/pgdump_quanthistling2.sql", "w", "utf-8")
for line in in_file:
    new_line = r.sub("postgres", line)
    out_file.write(new_line)
in_file.close()
out_file.close()

print("Inserting data into database...")
call([os.path.join(POSTGRES_BIN_PATH, "psql"), "-hlocalhost", "quanthistling"], stdin=open("/var/www/quanthistling-new/quanthistling/public/downloads/pgdump_quanthistling2.sql", "r"))

#sudo -u postgres psql quanthistling < /var/www/quanthistling-new/quanthistling/public/downloads/pgdump_quanthistling.sql