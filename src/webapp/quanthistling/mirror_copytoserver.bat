set QUANTHISTLINGPATH=h:\ProjectsWin\svn-googlecode\qlc\src\webapp\quanthistling
set PATH=%PATH%;c:\Program Files (x86)\PuTTY

cd %QUANTHISTLINGPATH%
cd %QUANTHISTLINGPATH%\quanthistling\public\downloads
call pscp *.zip  h1951206.stratoserver.net:/var/www/quanthistling-new/quanthistling/public/downloads/
call pscp xml\*.zip h1951206.stratoserver.net:/var/www/quanthistling-new/quanthistling/public/downloads/xml/
call pscp csv\*.zip h1951206.stratoserver.net:/var/www/quanthistling-new/quanthistling/public/downloads/csv/
call pscp csv\*.csv h1951206.stratoserver.net:/var/www/quanthistling-new/quanthistling/public/downloads/csv/
cd %QUANTHISTLINGPATH%

rem shutdown /s