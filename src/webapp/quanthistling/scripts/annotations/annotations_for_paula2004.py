# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import re

from operator import attrgetter
import difflib

# Pylons model init sequence
import pylons.test
import logging

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

import quanthistling.dictdata.books

from paste.deploy import appconfig

import functions

def annotate_everything(entry):
    # delete head annotations
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='pos' or a.value=='translation']
    for a in annotations:
        Session.delete(a)

    tab_annotations = [ a for a in entry.annotations if a.value=='tab' ]
    newline_annotations = [ a for a in entry.annotations if a.value=='newline' ]
    #translation_end = ""
    #if len(newline_annotations) == 1:
     #   translation_end = " " + entry.fullentry[newline_annotations[0].start:]

    translation_end = len(entry.fullentry)

    heads = []
    
    if len(tab_annotations) != 2:
        print "not 2 tabs in entry " + entry.fullentry.encode("utf-8")
    else:
        head = entry.fullentry[0:tab_annotations[0].start]
        inserted_head = functions.insert_head(entry, 0, tab_annotations[0].start, head)
        # waar komt de waarde voor pos vandaan?
        entry.append_annotation(tab_annotations[0].start, tab_annotations[1].start, u'pos', u'dictinterpretation')
        translation = entry.fullentry[tab_annotations[1].end:]
        functions.insert_translation(entry, tab_annotations[1].end, translation_end, translation)
        
        
        #entry.append_annotation(start, end, u'head', u'dictinterpretation')
        heads.append(inserted_head)
        
    return heads

    
 
def main(argv):

    bibtex_key = u"paula2004"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=242,pos_on_page=1).all()

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
