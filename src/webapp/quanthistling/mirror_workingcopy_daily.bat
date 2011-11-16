set QUANTHISTLINGPATH=h:\ProjectsWin\svn-googlecode\qlc\src\webapp\quanthistling
set PATH=%PATH%;c:\Program Files (x86)\PostgreSQL\8.4\bin;c:\Program Files (x86)\PuTTY

cd %QUANTHISTLINGPATH%
python scripts/export_all_static_data_daily.py development.ini
scripts/exportcsv.bat

cd %QUANTHISTLINGPATH%\quanthistling\public\downloads
call pg_dump.exe -h localhost -U postgres -c quanthistling > pgdump_quanthistling.sql
call pscp -r *.zip peterbouda.de:/var/www/quanthistling-new/quanthistling/public/downloads/
call pscp -r pgdump_quanthistling.sql peterbouda.de:/var/www/quanthistling-new/quanthistling/public/downloads/
