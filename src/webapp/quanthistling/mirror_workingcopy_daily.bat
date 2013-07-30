set QUANTHISTLINGPATH=h:\ProjectsWin\svn-googlecode\qlc\src\webapp\quanthistling
set PATH=%PATH%;c:\Program Files (x86)\PostgreSQL\8.4\bin;c:\Program Files (x86)\PuTTY;c:\Program Files\7-Zip

cd %QUANTHISTLINGPATH%
c:\python27-64\python.exe scripts/export_all_static_data.py development.ini

cd %QUANTHISTLINGPATH%\quanthistling\public\downloads
call pg_dump.exe -h localhost -U postgres -c quanthistling > pgdump_quanthistling.sql
call 7z.exe u -tzip pgdump_quanthistling.zip pgdump_quanthistling.sql
cd %QUANTHISTLINGPATH%

rem shutdown /s