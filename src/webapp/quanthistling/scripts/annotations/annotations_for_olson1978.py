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
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=="iso-639-3" or a.value=="doculect" or a.value=='translation']
    for a in head_annotations:
        Session.delete(a)
        
    heads = []

    sorted_annotations = [ a for a in entry.annotations if a.value=='tab']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))

    if len(sorted_annotations) < 1:
        functions.print_error_in_entry(entry, "No tabs found. Assuming head only.")
        head_end = len(entry.fullentry)
        trans_start = len(entry.fullentry)
    else:
        head_end = sorted_annotations[0].start
        trans_start = sorted_annotations[0].end

    #heads
    for h_start, h_end in functions.split_entry_at(entry, r',|$', 0, head_end):
        head = functions.insert_head(entry, h_start, h_end)
        if head:
            heads.append(head)

    #translations
    quotation_start = entry.fullentry.find('"', trans_start)
    if quotation_start != -1:
        trans_end = quotation_start
    else:
        trans_end = len(entry.fullentry)

    for t_start, t_end in functions.split_entry_at(entry, r',|/| - |$', trans_start, trans_end):
        functions.insert_translation(entry, t_start, t_end)
    
    return heads


def main(argv):

    bibtex_key = u"olson1978"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=9,pos_on_page=34).all()
        
        startletters = set()
    
        for e in entries:
            heads = annotate_everything(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            #annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
