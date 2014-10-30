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
        
    heads = []

    tabs = [ a for a in entry.annotations if a.value=="tab" ]
    tabs = sorted(tabs, key=attrgetter('start'))

    head_start = tabs[2].start + 1
    head_end = tabs[3].start
    head = entry.fullentry[head_start:head_end]
    match_bracket = re.search("\([^)]*\) ?$", head)
    if match_bracket:
        head_end = head_end - len(match_bracket.group(0))
    
    head = functions.insert_head(entry, head_start, head_end)
    heads.append(head)
    return heads


def annotate_translations(entry):
    head_annotations = [ a for a in entry.annotations if a.value=="translation"]
    for a in head_annotations:
        Session.delete(a)

    tabs = [ a for a in entry.annotations if a.value=="tab" ]
    tabs = sorted(tabs, key=attrgetter('start'))

    # English
    trans_start = tabs[3].start + 1
    trans_end = tabs[4].start
    start = trans_start
    for match in re.finditer(u"(?:[;,] |/|$)", entry.fullentry[trans_start:trans_end]):
        # Are we in bracket?
        in_bracket = False
        for match_bracket in re.finditer("\([^)]*\)", entry.fullentry[trans_start:trans_end]):
            if match_bracket.start(0) < match.start(0) and match_bracket.end(0) > match.end(0):
                in_bracket = True
        if not in_bracket:
            end = trans_start + match.start(0)
            functions.insert_translation(entry, start, end, lang_iso = 'eng', lang_doculect = 'English')
            start = trans_start + match.end(0)
    
    # Spanish
    trans_start = tabs[4].start + 1
    trans_end = len(entry.fullentry)
    start = trans_start
    for match in re.finditer(u"(?:[;,] |/|$)", entry.fullentry[trans_start:trans_end]):
        # Are we in bracket?
        in_bracket = False
        for match_bracket in re.finditer("\([^)]*\)", entry.fullentry[trans_start:trans_end]):
            if match_bracket.start(0) < match.start(0) and match_bracket.end(0) > match.end(0):
                in_bracket = True
        if not in_bracket:
            end = trans_start + match.start(0)
            functions.insert_translation(entry, start, end, lang_iso = 'spa', lang_doculect = 'Spanish')
            start = trans_start + match.end(0)

def main(argv):

    bibtex_key = u"parker2010a"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=15,pos_on_page=5).all()

        startletters = set()
    
        for e in entries:
            #one time data conversion
            if e.fullentry.find('s@') != -1 or e.fullentry.find('c@') != -1:
                e.fullentry = e.fullentry.replace(u's@', u's\u0308').replace(u'c@', u'c\u0308')
                functions.print_error_in_entry(e, 'Replacing s@ and c@.')
                
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
