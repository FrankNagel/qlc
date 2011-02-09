1. Setup
--------

After downloading the qlc scripts and libraries you have to add the library
to your Python path first. Otherwise Python won't find the module "qlc". To
do this, you have to add the path to the "src" folder to the environment
variable "PYTHONPATH".

You can run all scripts from the command line within the main "qlc" folder. So
you may add a relative path, like this on Mac or Unix:
  
$ export PYTHONPATH=$PYTHONPATH:./src

You can also add this string to your .profile file on Mac (located it, e.g.: /Users/Ramon/, so that the PYTHONPATH will 
be set when you open Terminal:

export PYTHONPATH=${PYTHONPATH}:/Users/Ramon/path-to-your-qlc-folder/src/

On Windows:

> set PYTHONPATH=%PYTHONAPTH%:./src

Then you can run, for example:
  
$ python bin/heads_with_translations.py data

This is one of the example scripts that create list of all heads with
corresponding translations. You have to download all dictionary .csv files
to the "data" folder first.

2. Usage
--------

First, download the dictionary .csv files. The current link is alway available
in the project's Trac wiki (right now the data is not publically available, due
to unresolved licensing issues). Unpack all files from the csv.zip to the
"data" folder.

Then, start a Python command prompt and import the CorpusReader module:

$ python
Python 2.6.6 (r266:84292, Sep 15 2010, 16:22:56) 
[GCC 4.4.5] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import qlc.CorpusReader

Then, try to create an object from CorpusReaderDict and access its API:

>>> cr = qlc.CorpusReader.CorpusReaderDict("data")
>>> heads_with_translations = cr.headsWithTranslations()
>>> heads_with_translations
{u'40135': {'translations': [u'misu\u0301 kui\u0301nkatin'], 'dictdata_st...

This will print out a long list of entries with their heads and translations.
You can always find help about any class with the "help()" function:

>>> help(qlc.CorpusReader.CorpusReaderDict)

Quit the Python prompt and be happy:

>>> quit()
