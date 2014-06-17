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

import unicodedata

import functions


def _get_dash_position(entry):
    dash_name = 'EN DASH'
    for i, c in enumerate(entry.fullentry):
        if c == u'-':
            return i
        if unicodedata.name(c) == dash_name:
            return i

    return -1


def annotate_everything(entry):
    # delete head annotations
    annotations = [ a for a in entry.annotations if a.value=='head' or
                                                    a.value=='translation' or
                                                    a.value=='pos'
                                                    or a.value=='doculect' or
                                                    a.value=='iso-639-3']
    for a in annotations:
        Session.delete(a)

    heads = []


    head_end = _get_dash_position(entry)
    tabs = functions.get_list_ranges_for_annotation(entry, 'tab', head_end)
    if head_end == -1:
        if len(tabs) == 0:
            functions.print_error_in_entry(entry, 'No tabs found. Cannot annotate.')
            return []
        head_end = tabs[0][0]

    start = 0
    for match_comma in re.finditer("(?:, ?|$)", entry.fullentry[0:head_end]):
        end = match_comma.start(0)
        head = functions.insert_head(entry, start, end)
        start = 0 + match_comma.end(0)
        heads.append(head)

    #annotate POS

    if len(tabs) == 0:
        functions.print_error_in_entry(entry, 'No tabs after dash. No POS detection possible')
        trans_start = head_end + 1
    else:
        entry.append_annotation(head_end + 1, tabs[0][0], u'pos', u'dictinterpretation')
        trans_start = tabs[0][1]

    #annotate translation
    part_start = trans_start
    for match_semi_colon in re.finditer("(?:[,;] ?|$)", entry.fullentry[trans_start:]):
        part_end = trans_start + match_semi_colon.start(0)
        functions.insert_translation(entry, part_start, part_end)
        part_start = trans_start + match_semi_colon.end(0)

    return heads

def main(argv):
    bibtex_key = u"tuggy1966"
    
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

        entry = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=345,pos_on_page=21).first()
        if entry:
            for a in entry.annotations:
                Session.delete(a)
            Session.delete(entry)
            Session.commit()

        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=1,pos_on_page=1).all()

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