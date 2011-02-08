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
#from manualannotations_for_kneeland1979 import manual_entries

def annotate_everything(entry):
    # delete head annotations
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='translation' or a.value=='example-src' or a.value=='example-tgt' ]
    for a in annotations:
        Session.delete(a)

    newline_positions = [ a.start for a in entry.annotations if a.value=='newline' ]
    newline_positions.append(len(entry.fullentry))

    heads = []
    
    head = ""
    head_start = 0
    head_end = 0

    translation = ""
    translation_start = 0
    translation_end = 0
    
    example_src = ""
    example_src_start = 0
    example_src_end = 0
    example_tgt = ""
    example_tgt_start = 0
    example_tgt_end = 0

    line_start = 0
    
    in_examples = False
    
    # process first line
    line_end = newline_positions[0]
    tab_annotations = [ a.start for a in entry.annotations if a.value=='tab' and a.start > line_start and a.end < line_end ]
    if len(tab_annotations) != 4:
        functions.print_error_in_entry(entry, "not 4 tabs in entry")
        
    head_end = tab_annotations[0]
    head = entry.fullentry[0:tab_annotations[0]]
    
    translation_start = tab_annotations[2]
    translation_end = line_end
    translation = entry.fullentry[tab_annotations[2]:line_end]
    
    line_start = line_end
    for line_end in newline_positions[1:]:
        tab_annotations = [ a.start for a in entry.annotations if a.value=='tab' and a.start > line_start and a.end < line_end ]
        if len(tab_annotations) == 4:
            # is there a part of the translation?
            if not re.match(r"\s*$", entry.fullentry[tab_annotations[2]:line_end]):
                translation_end = line_end
                translation = translation + entry.fullentry[tab_annotations[2]:line_end]
        elif len(tab_annotations) == 1:
            if example_tgt != "":
                entry.append_annotation(example_src_start, example_src_end, u'example-src', u'dictinterpretation')
                entry.append_annotation(example_tgt_start, example_tgt_end, u'example-tgt', u'dictinterpretation')
                example_src = ""
                example_tgt = ""
                example_src_start = 0
                example_tgt_start = 0
            in_examples = True
            example_src = example_src + entry.fullentry[tab_annotations[0]:line_end]
            if example_src_start == 0:
                example_src_start = tab_annotations[0]
            example_src_end = line_end
        elif len(tab_annotations) == 2 and in_examples:
            example_tgt = example_tgt + entry.fullentry[tab_annotations[1]:line_end]
            if example_tgt_start == 0:
                example_tgt_start = tab_annotations[1]
            example_tgt_end = line_end            
        line_start = line_end
        
    inserted_head = functions.insert_head(entry, head_start, head_end)
    heads.append(inserted_head)
    translation = re.sub(u"\. ?$", "", translation)
    functions.insert_translation(entry, translation_start, translation_end, translation)
    if example_tgt != "":
        entry.append_annotation(example_src_start, example_src_end, u'example-src', u'dictinterpretation')
        entry.append_annotation(example_tgt_start, example_tgt_end, u'example-tgt', u'dictinterpretation')

    return heads


def main(argv):
    bibtex_key = u"kneeland1979"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=210,pos_on_page=11).all()
        
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
#            entry_db.fullentry = e["fullentry"].decode('utf-8')
#            # delete all annotations in db
#            for a in entry_db.annotations:
#                Session.delete(a)
#            # insert new annotations
#            for a in e["annotations"]:
#                entry_db.append_annotation(a["start"], a["end"], a["value"].decode('utf-8'), a["type"].decode('utf-8'), a["string"].decode('utf-8'))
#        else:
#            print "We have a problem, manual entry on page %i pos %i seems not to be the same entry as in db, it was not inserted to db. Please correct the problem. (ratio: %f)" % (e["startpage"], e["pos_on_page"], ratio)
#
#    Session.commit()
    

if __name__ == "__main__":
    main(sys.argv)