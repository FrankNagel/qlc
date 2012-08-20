# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import re

from operator import attrgetter

# Pylons model init sequence
import pylons.test
import logging

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

import quanthistling.dictdata.books

from paste.deploy import appconfig

import functions

def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in head_annotations:
        Session.delete(a)

    head = None
    heads = []
    
    match = re.search(u' ?–', entry.fullentry)

    if match:
        inserted_head = functions.insert_head(entry, 0, match.start(0))
        #entry.append_annotation(0, match.start(0), u'head', u'dictinterpretation')
        heads.append(inserted_head)
    else:
        print "no head"
        print entry.fullentry.encode('utf-8')
        
    return heads

def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    match_dash = re.search(u' ?– ?', entry.fullentry)
    if match_dash:
        substr = entry.fullentry[match_dash.end(0):]
        start = match_dash.end(0)
        for match in re.finditer(r'[,;] ?', substr):
            end = match.start(0) + match_dash.end(0)
            functions.insert_translation(entry, start, end)
            start = match.end(0) + match_dash.end(0)
        end = len(entry.fullentry)
        functions.insert_translation(entry, start, end)

def main(argv):
    bibtex_key = u"larson1966"
    
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

        startletters = set()
    
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)