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
from manualannotations_for_aguiar1994 import manual_entries

def annotate_everything(entry):
    # delete head annotations
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='translation' or a.value=='pos' or a.value=='phonology' ]
    for a in annotations:
        Session.delete(a)

    tab_annotations = [ a for a in entry.annotations if a.value=='tab' ]
    newline_annotations = [ a for a in entry.annotations if a.value=='newline' ]
    translation_end = ""
    if len(newline_annotations) == 1:
        translation_end = " " + entry.fullentry[newline_annotations[0].start:]

    heads = []
    
    if len(tab_annotations) != 3:
        print "not 3 tabs in entry " + entry.fullentry.encode("utf-8")
    else:
        head = re.sub(u"-", u"", entry.fullentry[0:tab_annotations[0].start])
        inserted_head = functions.insert_head(entry, 0, tab_annotations[0].start, head)
        entry.append_annotation(tab_annotations[0].start, tab_annotations[1].start, u'pos', u'dictinterpretation')
        translation = entry.fullentry[tab_annotations[1].start:tab_annotations[2].start] + translation_end
        functions.insert_translation(entry, tab_annotations[1].start, tab_annotations[2].start, translation)
        
        if len(newline_annotations) == 1:
            entry.append_annotation(tab_annotations[2].start, newline_annotations[0].start, u'phonology', u'dictinterpretation')
        else:
            entry.append_annotation(tab_annotations[2].start, len(entry.fullentry), u'phonology', u'dictinterpretation')
        #entry.append_annotation(start, end, u'head', u'dictinterpretation')
        heads.append(inserted_head)
        
    return heads

def main(argv):
    bibtex_key = u"aguiar1994"
    
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

    
    entry = Session.query(model.Entry).filter_by(startpage=345,pos_on_page=21).first()
    if entry:
        for a in entry.annotations:
            Session.delete(a)
        Session.delete(entry)
        Session.commit()

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

    for e in manual_entries:
        dictdata = model.meta.Session.query(model.Dictdata).join(
            (model.Book, model.Dictdata.book_id==model.Book.id)
            ).filter(model.Book.bibtex_key==bibtex_key).filter("startpage<=:pagenr and endpage>=:pagenr").params(pagenr=int(e["startpage"])).first()
        
        entry_db = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id, startpage=e["startpage"], pos_on_page=e["pos_on_page"]).first()
        ratio = difflib.SequenceMatcher(None, e["fullentry"].decode('utf-8'), entry_db.fullentry).ratio()
        if ratio > 0.80:
            entry_db.fullentry = e["fullentry"].decode('utf-8')
            # delete all annotations in db
            for a in entry_db.annotations:
                Session.delete(a)
            # insert new annotations
            for a in e["annotations"]:
                entry_db.append_annotation(a["start"], a["end"], a["value"].decode('utf-8'), a["type"].decode('utf-8'), a["string"].decode('utf-8'))
        else:
            print "We have a problem, manual entry on page %i pos %i seems not to be the same entry as in db, it was not inserted to db. Please correct the problem. (ratio: %f)" % (e["startpage"], e["pos_on_page"], ratio)

    Session.commit()
    

if __name__ == "__main__":
    main(sys.argv)