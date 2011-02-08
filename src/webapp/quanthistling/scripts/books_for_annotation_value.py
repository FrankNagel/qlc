# -*- coding: utf8 -*-

# import Python system modules to write files
import sys, os
import re

# add path to script
sys.path.append(os.path.abspath('.'))

# import pylons and web application modules
import pylons.test
from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
from paste.deploy import appconfig
import quanthistling.dictdata.books

from routes import url_for

def main(argv):

    if len(argv) < 2:
        print "call: exportheads.py ini_file"
        exit(1)

    ini_file = argv[1]

    # load web application config
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create database session
    metadata.create_all(bind=Session.bind)


    # database queries for pos
    annotations = model.meta.Session.query(model.Annotation).join(
            (model.Entry, model.Annotation.entry_id==model.Entry.id),
            (model.Dictdata, model.Entry.dictdata_id==model.Dictdata.id),
            (model.Book, model.Dictdata.book_id==model.Book.id)
        ).filter(model.Annotation.value==u"underline").all()
    books = set()
    for a in annotations:
        books.add(a.entry.dictdata.book.bibtex_key)
        
    print books
        
if __name__ == "__main__":
    main(sys.argv)
