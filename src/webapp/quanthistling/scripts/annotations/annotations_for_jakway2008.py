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
from manualannotations_for_jakway2008 import manual_entries

def get_bold_annotations(entry):
    sorted_annotations = [ a for a in entry.annotations if a.value=='bold']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    last_bold_end = -1
    at_start = True
    last_bold_start = sorted_annotations[0].start
    head_starts = []
    head_ends = []
    for a in sorted_annotations:
        if (a.start <= (last_bold_end + 1)):
            last_bold_end = a.end
        else:
            head_starts.append(last_bold_start)
            head_ends.append(last_bold_end)
            last_bold_start = a.start
            last_bold_end = a.end
    head_starts.append(last_bold_start)
    head_ends.append(last_bold_end)
    return head_starts, head_ends
    

def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in head_annotations:
        Session.delete(a)

    head = None
    heads = []
    
    sorted_annotations = [ a for a in entry.annotations if a.value=='bold']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))

    head_starts, head_ends = get_bold_annotations(entry)    
    heads = []

    for i in range(len(head_starts)):
        head_start_pos = head_starts[i]
        head_end_pos = head_ends[i]
        #head_end_pos = functions.get_last_bold_pos_at_start(entry)
        #head_start_pos = 0
    
        if head_end_pos > -1:
            start = head_start_pos
            substr = entry.fullentry[head_start_pos:head_end_pos]
            for match in re.finditer(r', ?', substr):
                end = match.start(0) + head_start_pos
                inserted_head = functions.insert_head(entry, start, end)
                #entry.append_annotation(start, end, u'head', u'dictinterpretation')
                heads.append(inserted_head)
                start = match.end(0) + head_start_pos
            end = head_end_pos
            inserted_head = functions.insert_head(entry, start, end)
            #entry.append_annotation(start, end, u'head', u'dictinterpretation')
            heads.append(inserted_head)
        else:
            print "no head"
            print entry.fullentry.encode('utf-8')
        
    return heads


def annotate_head_without_comma(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head']
    for a in head_annotations:
        Session.delete(a)

    head = None
    heads = []
    
    sorted_annotations = [ a for a in entry.annotations if a.value=='bold']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))

    head_starts, head_ends = get_bold_annotations(entry)    

    heads = []

    for i in range(len(head_starts)):
        head_start_pos = head_starts[i]
        head_end_pos = head_ends[i]
        #head_end_pos = functions.get_last_bold_pos_at_start(entry)
        #head_start_pos = 0
    
    
        if head_end_pos > -1:
            inserted_head = functions.insert_head(entry, head_start_pos, head_end_pos)
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

    #head_end_pos = functions.get_last_bold_pos_at_start(entry)
    head_starts, head_ends = get_bold_annotations(entry)

    for i in range(len(head_starts)):
        trans_start_pos = head_ends[i]
        if len(head_starts) > i+1:
            trans_end_pos = head_starts[i+1]
        else:
            trans_end_pos = len(entry.fullentry)

        if trans_start_pos > -1:
            substr = entry.fullentry[trans_start_pos:trans_end_pos]
            start = trans_start_pos
            for match in re.finditer(r'(?:, ?|; ?|\d\) )', substr):
                mybreak = False
                # are we in a bracket?
                for m in re.finditer(r'\(.*?\)', substr):
                    if match.start(0) >= m.start(0) and match.end(0) <= m.end(0):
                        mybreak = True
                    
                if not mybreak:
                    end = match.start(0) + trans_start_pos
                    if end > start and not re.match(r' +$', entry.fullentry[start:end]):
                        functions.insert_translation(entry, start, end)
                    start = match.end(0) + trans_start_pos
                    
            end = trans_end_pos
            if end > start and not re.match(r'^ +$', entry.fullentry[start:end]):
                functions.insert_translation(entry, start, end)

def main(argv):
    bibtex_key = u"jakway2008"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=109,pos_on_page=18).all()
        #entries = []

        startletters = set()
    
        for e in entries:
            if dictdata.startpage == 129:
                heads = annotate_head_without_comma(e)
            else:
                heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

    for e in manual_entries:
        dictdata = model.meta.Session.query(model.Dictdata).join(
            (model.Book, model.Dictdata.book_id==model.Book.id)
            ).filter(model.Book.bibtex_key==bibtex_key).filter("startpage<=:pagenr and endpage>=:pagenr").params(pagenr=int(e["startpage"])).first()
        
        entry_db = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id, startpage=e["startpage"], pos_on_page=e["pos_on_page"]).first()
        if difflib.SequenceMatcher(None, e["fullentry"].decode('utf-8'), entry_db.fullentry).ratio() > 0.95:
            entry_db.fullentry = e["fullentry"].decode('utf-8')
            # delete all annotations in db
            for a in entry_db.annotations:
                Session.delete(a)
            # insert new annotations
            for a in e["annotations"]:
                entry_db.append_annotation(a["start"], a["end"], a["value"].decode('utf-8'), a["type"].decode('utf-8'), a["string"].decode('utf-8'))
        else:
            print "We have a problem, manual entry on page %i pos %i seems not to be the same entry as in db, it was not inserted to db. Please correct the problem." % (e["startpage"], e["pos_on_page"])

    Session.commit()

if __name__ == "__main__":
    main(sys.argv)