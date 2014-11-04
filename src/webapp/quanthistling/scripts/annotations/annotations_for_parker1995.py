# -*- coding: utf8 -*-

import sys, os
sys.path.append(os.path.abspath('.'))

import re

from operator import attrgetter
from operator import itemgetter

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
        
    head = None
    heads = []

    in_brackets = functions.get_in_brackets_func(entry)
    bolds = functions.get_list_bold_ranges(entry)
    bolds += functions.get_list_italic_ranges(entry)

    for b in bolds:
        if in_brackets(*b):
            continue
        start = b[0]
        for match_comma in re.finditer("(?:[,;:] ?|$)", entry.fullentry[b[0]:b[1]]):
            end = b[0] + match_comma.start(0)
            start, end, translation = functions.remove_parts(entry, start, end)
            if translation.startswith(u'e\u0301l/ella'):
                start += 4
                translation = translation[4:]
            head = functions.insert_head(entry, start, end, translation)
            heads.append(head)
            start = b[0] + match_comma.end(0)

    return heads


def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    in_brackets = functions.get_in_brackets_func(entry)
    heads = [x for x in functions.get_list_bold_ranges(entry) if not in_brackets(*x)]
    heads += functions.get_list_italic_ranges(entry)

    heads = sorted(heads, key=itemgetter(1))

    translation_start = -1
    translation_end = -1
    for i, h in enumerate(heads):
        translation_start = h[1]
        if i < (len(heads) - 1):
            translation_end = heads[i+1][0]
        else:
            translation_end = len(entry.fullentry)

        if not (translation_end > 0 and (translation_end - translation_start) > 1):
            continue

        for t_start, t_end in functions.split_entry_at(entry, r',|;|$', translation_start, translation_end):
            functions.insert_translation(entry, t_start, t_end)


def main(argv):

    bibtex_key = u"parker1995"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=26,pos_on_page=23).all()

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
