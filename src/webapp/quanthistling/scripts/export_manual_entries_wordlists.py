# -*- coding: utf8 -*-

# import Python system modules to write files
import sys, os, glob
import re
import tempfile
import shutil

from zipfile import ZipFile

# add path to script
sys.path.append(os.path.abspath('.'))

# import pylons and web application modules
import pylons.test
from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
from paste.deploy import appconfig

import quanthistling.dictdata.wordlistbooks

from routes import url_for

def main(argv):

    if len(argv) < 2:
        print "call: exportbookdata.py ini_file"
        exit(1)

    ini_file = argv[1]
    
    bibtex_key_param = None
    if len(argv) >= 3:
        bibtex_key_param = argv[2]

    # load web application config
    conf = appconfig('config:' + ini_file, relative_to='.')
    config = None
    if not pylons.test.pylonsapp:
        config = load_environment(conf.global_conf, conf.local_conf)

    # Create database session
    metadata.create_all(bind=Session.bind)
    
    for b in quanthistling.dictdata.wordlistbooks.list:
        if bibtex_key_param != None and bibtex_key_param != b['bibtex_key']:
            continue
        book = model.meta.Session.query(model.Book).filter_by(bibtex_key=b['bibtex_key']).first()
        if book:
            
            print "Exporting data for %s..." % b['bibtex_key']

            for wordlistdata in book.wordlistdata:
                entries = model.meta.Session.query(model.WordlistEntry).join(
                        (model.Wordlistdata, model.WordlistEntry.wordlistdata_id==model.Wordlistdata.id)
                    ).filter(model.Wordlistdata.id==wordlistdata.id).filter(model.WordlistEntry.has_manual_annotations==True).all()
                
                # write heads to file
                if len(entries) > 0:
                    for i in range(0,len(entries)):
                        fullentry = entries[i].fullentry
                        url = url_for(controller='book', action='entryid_wordlist', bibtexkey=b['bibtex_key'], concept=entries[i].concept.concept, language_bookname=wordlistdata.language_bookname, format='html')
                        print(fullentry.encode('utf-8') + "\thttp://www.cidles.eu/quanthistling" + url + "\n")



if __name__ == "__main__":
    main(sys.argv)
