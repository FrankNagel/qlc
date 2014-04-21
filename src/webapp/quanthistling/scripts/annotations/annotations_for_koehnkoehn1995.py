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
    head = None
    heads = []
    
    head_end = functions.get_last_bold_pos_at_start(entry)
    head_all = entry.fullentry[:head_end]
    head_all = head_all.rstrip()
    
    head = functions.insert_head(entry, 0, head_end, head_all)        
    heads.append(head)

    return heads


def annotate_pos(entry):
    # delete translation annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)

    head_end = functions.get_head_end(entry)
    italic = functions.get_first_italic_in_range(entry, 0, len(entry.fullentry))
    if italic != -1:
        pos = entry.fullentry[italic[0]:italic[1]]
        if "radical:" in pos:
            new_start = italic[1]
            italic = functions.get_first_italic_in_range(entry, new_start, len(entry.fullentry))
            if italic == -1:
                bold = functions.get_first_bold_in_range(entry, new_start, len(entry.fullentry))
                return bold[1]

    if italic != -1:
        entry.append_annotation(italic[0], italic[1], u'pos', u'dictinterpretation')
        return italic[1]
    else:
        functions.print_error_in_entry(entry, "Could not find italic for POS")
        return -1


def annotate_translations(entry, pos_end):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    translation_start = pos_end
    translation_end = len(entry.fullentry)
    italic = functions.get_first_italic_in_range(entry, translation_start, translation_end)
    if italic != -1:
        translation_end = italic[0] - 1

    bold = functions.get_first_bold_in_range(entry, translation_start, translation_end)
    if bold != -1:
        translation_end = bold[0] - 1

    for s, e in functions.split_entry_at(entry, r"(?:; |$)", translation_start, translation_end):
        functions.insert_translation(entry, s, e)

 
def main(argv):

    bibtex_key = u"koehnkoehn1995"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=105,pos_on_page=2).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            pos_end = annotate_pos(e)
            if pos_end != -1:
                annotate_translations(e, pos_end)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
