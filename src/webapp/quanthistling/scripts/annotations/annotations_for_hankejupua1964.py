# -*- coding: utf8 -*-

import sys
import os
sys.path.append(os.path.abspath('.'))

# Pylons model init sequence
import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

from paste.deploy import appconfig

import functions


def annotate_everything(entry):
    # delete head annotations
    head_annotations = [a for a in entry.annotations if a.value == 'head' or 
                        a.value == 'iso-639-3' or a.value == 'doculect' or 
                        a.value == 'translation']
    for a in head_annotations:
        Session.delete(a)

    head = None
    heads = []

    tabs = functions.get_list_ranges_for_annotation(entry, 'tab')
    if len(tabs) == 0:
        functions.print_error_in_entry(entry, 'No clear separation between '
                                              'head word and translation.')
        exit(1)

    head_end = tabs[0][0]
    trans_start = tabs[0][1]

    head = functions.insert_head(entry, 0, head_end)
    heads.append(head)

    functions.insert_translation(entry, trans_start, len(entry.fullentry))
    
    return heads

 
def main(argv):

    bibtex_key = u'hankejupua1964'
    
    if len(argv) < 2:
        print "call: annotations_for_%s.py ini_file" % bibtex_key
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=105,pos_on_page=2).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_everything(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())

        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
