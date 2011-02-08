# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

# import pylons and web application modules
import pylons.test
from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model
from paste.deploy import appconfig
from routes import url_for

def main(argv):

    bibtex_key = u"burtch1983"
    
    if len(argv) < 2:
        print "call: annotations_for%s.py ini_file" % bibtex_key
        exit(1)

    ini_file = argv[1]    
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)

    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    dictdatas = Session.query(model.Dictdata).join(
        (model.Book, model.Dictdata.book_id==model.Book.id)
        ).filter(model.Book.bibtex_key==bibtex_key).all()

    for dictdata in dictdatas:

        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=19,pos_on_page=9).all()
        
        for e in entries:
            examples = []
            for a in e.annotations:
                if a.value == 'example-src' or a.value == 'example-tgt':
                    examples.append(a.string)
            if len(examples) > 2:
                if e.is_subentry:
                    url = url_for(controller='book', action='entryid', bibtexkey=bibtex_key, pagenr=e.mainentry().startpage, pos_on_page=e.mainentry().pos_on_page, format='html')
                else:
                    url = url_for(controller='book', action='entryid', bibtexkey=bibtex_key, pagenr=e.startpage, pos_on_page=e.pos_on_page, format='html')
                print e.fullentry.encode("utf-8") + '|' + url

if __name__ == "__main__":
    main(sys.argv)
