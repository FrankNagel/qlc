set QUANTHISTLINGPATH=h:\ProjectsWin\svn-googlecode\qlc\src\webapp\quanthistling
set PATH=%PATH%;c:\Program Files (x86)\PostgreSQL\8.4\bin;c:\Program Files (x86)\PuTTY;c:\Program Files\7-Zip

cd %QUANTHISTLINGPATH%
python scripts/export_all_static_data.py development.ini
call scripts/exportcsv.bat

cd %QUANTHISTLINGPATH%\quanthistling\public\downloads
call pg_dump.exe -h localhost -U postgres -c quanthistling > pgdump_quanthistling.sql
call 7z.exe u -tzip pgdump_quanthistling.zip pgdump_quanthistling.sql
call pscp -r *.zip peterbouda.de:/var/www/quanthistling-new/quanthistling/public/downloads/
cd %QUANTHISTLINGPATH%