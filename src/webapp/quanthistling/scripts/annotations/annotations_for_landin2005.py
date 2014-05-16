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

def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in head_annotations:
        Session.delete(a)
        
    # Delete this code and insert your code
    heads = []

    sorted_annotations = [a for a in entry.annotations if a.value=='tab']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))

    if len(sorted_annotations) > 0:
        head_end = sorted_annotations[0].start
    else:
        head_end = 0

    temp_head = entry.fullentry[0:head_end]
    if not (re.match('\d*', temp_head) and len(temp_head)) == 1:
        head = functions.insert_head(entry, 0, head_end)
        heads.append(head)

    return heads

def annotate_pos(entry):
    #delete pos annotations
    pos_annotations = [a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)

    start_bracket_pos = entry.fullentry.find('(')
    end_bracket_pos = entry.fullentry.find(')')
    if start_bracket_pos != -1 and end_bracket_pos != -1:
        functions.insert_pos(entry, start_bracket_pos + 1, end_bracket_pos)

def annotate_translation(entry):
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    end_bracket_pos = entry.fullentry.find(')')
    if end_bracket_pos != -1:
        trans_start = end_bracket_pos + 1
    else:
        trans_start = 0

    trans = entry.fullentry[trans_start:]
    
    for split in trans.split(','):
        trans_end = trans_start + len(split)
        functions.insert_translation(entry, trans_start, trans_end)
        trans_start = trans_end + 1

def main(argv):

    bibtex_key = u"landin2005"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=6,pos_on_page=1).all()
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=6,pos_on_page=2).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_translation(e)
            annotate_pos(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
