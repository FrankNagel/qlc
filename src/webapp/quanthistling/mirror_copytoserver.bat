set QUANTHISTLINGPATH=h:\ProjectsWin\svn-googlecode\qlc\src\webapp\quanthistling
set PATH=%PATH%;c:\Program Files (x86)\PuTTY

cd %QUANTHISTLINGPATH%
cd %QUANTHISTLINGPATH%\quanthistling\public\downloads
call pscp *.zip Strato2_pbouda:/var/www/quanthistling-new/quanthistling/public/downloads/
call pscp xml\*.zip Strato2_pbouda:/var/www/quanthistling-new/quanthistling/public/downloads/xml/
call pscp csv\*.zip Strato2_pbouda:/var/www/quanthistling-new/quanthistling/public/downloads/csv/
call pscp csv\*.csv Strato2_pbouda:/var/www/quanthistling-new/quanthistling/public/downloads/csv/
cd %QUANTHISTLINGPATH%

shutdown /s