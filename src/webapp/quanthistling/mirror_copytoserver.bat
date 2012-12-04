set QUANTHISTLINGPATH=h:\ProjectsWin\svn-googlecode\qlc\src\webapp\quanthistling
set PATH=%PATH%;c:\Program Files (x86)\PuTTY

cd %QUANTHISTLINGPATH%
cd %QUANTHISTLINGPATH%\quanthistling\public\downloads
call pscp -r *.zip xml\*.zip csv\*.zip peterbouda.de:/var/www/quanthistling-new/quanthistling/public/downloads/
cd %QUANTHISTLINGPATH%