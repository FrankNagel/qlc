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
#from manualannotations_for_aguiar1994 import manual_entries

def annotate_everything(entry):
    # delete head annotations
    annotations = [ a for a in entry.annotations if (a.value=='head' or a.value=='translation' or a.value=="iso-639-3" or a.value=="doculect") ]
    for a in annotations:
        Session.delete(a)

    heads = []
    
    parts = entry.fullentry.split(" / ")
    
    if len(parts) < 2:
        print "not 3 parts in entry " + entry.fullentry.encode("utf-8")
    else:
        inserted_head = functions.insert_head(entry, 0, len(parts[0]))
        translation_start = len(parts[0])+3
        translation_end = len(parts[0])+3+len(parts[1])
        translation = entry.fullentry[translation_start:translation_end]
        match_bracket = re.search(u" ? \(Orr:.*?\) ?$", translation)
        if match_bracket:
            translation_end = translation_end - len(match_bracket.group(0))
            translation = entry.fullentry[translation_start:translation_end]
            
        start = translation_start
        for match_dot in re.finditer(u'(?:\. ?|$)', translation):
            end = translation_start + match_dot.start(0)
            functions.insert_translation(entry, start, end)
            start = translation_start + match_dot.end(0)
        heads.append(inserted_head)
        
    return heads

def main(argv):
    bibtex_key = u"stark1976"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=105,pos_on_page=16).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_everything(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

#    for e in manual_entries:
#        dictdata = model.meta.Session.query(model.Dictdata).join(
#            (model.Book, model.Dictdata.book_id==model.Book.id)
#            ).filter(model.Book.bibtex_key==bibtex_key).filter("startpage<=:pagenr and endpage>=:pagenr").params(pagenr=int(e["startpage"])).first()
#        
#        entry_db = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id, startpage=e["startpage"], pos_on_page=e["pos_on_page"]).first()
#        ratio = difflib.SequenceMatcher(None, e["fullentry"].decode('utf-8'), entry_db.fullentry).ratio()
#        if ratio > 0.80:
#           entry_db.fullentry = e["fullentry"].decode('utf-8')
#           # delete all annotations in db
#            for a in entry_db.annotations:
#                Session.delete(a)
#           # insert new annotations
#            for a in e["annotations"]:
#                entry_db.append_annotation(a["start"], a["end"], a["value"].decode('utf-8'), a["type"].decode('utf-8'), a["string"].decode('utf-8'))
#        else:
#            print "We have a problem, manual entry on page %i pos %i seems not to be the same entry as in db, it was not inserted to db. Please correct the problem. (ratio: %f)" % (e["startpage"], e["pos_on_page"], ratio)
#
#    Session.commit()
    

if __name__ == "__main__":
    main(sys.argv)