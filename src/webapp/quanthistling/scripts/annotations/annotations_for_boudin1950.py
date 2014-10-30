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


def _split_translations(entry, s, e):
    #get brackets
    match_brackets = re.search(r'\(.*\)$', entry.fullentry[s:e])
    if match_brackets is not None:
        bracket_start = s + match_brackets.start(0)
    else:
        bracket_start = e

    start = s
    for match_comma in re.finditer("(?:, ?|$)", entry.fullentry[s:e]):
        end = s + match_comma.start(0)
        if end < bracket_start or end == e:
            functions.insert_translation(entry, start, end)
            start = s + match_comma.end(0)

def insert_head(entry, start, end, heads):
    start, end, string = functions.remove_parts(entry, start, end)
    string = string.replace('-', '')
    head = functions.insert_head(entry, start, end, string)
    if head:
        heads.append(head)

def annotate_everything(entry):
    # delete head annotations
    annotations = [a for a in entry.annotations if a.value=='head' or
                                                   a.value=='translation'or
                                                   a.value=='doculect' or
                                                   a.value=='iso-639-3']

    for a in annotations:
        Session.delete(a)

    heads = []

    tabs = functions.get_list_ranges_for_annotation(entry, 'tab')

    if len(tabs) > 0:
        #head annotation
        trans_start = head_end = tabs[0][0]

        match = re.compile(r' \(([^)]*)\)').search(entry.fullentry, 0, head_end)
        if match:
            head_end = match.start()
            if match.group(1).strip() not in ['prefixo', 'sufixo', 'infixo'] and ':' not in match.group(1):
                insert_head(entry, match.start(1), match.end(1), heads)
        insert_head(entry, 0, head_end, heads)

        #translation annotation
        newlines = functions.get_list_ranges_for_annotation(entry, 'newline', trans_start)
        if len(newlines) > 0:
            trans_end = newlines[0][0]
        else:
            trans_end = len(entry.fullentry)

        _split_translations(entry, trans_start, trans_end)
    return heads


def main(argv):
    bibtex_key = u"boudin1950"
    
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=573,pos_on_page=2).all()

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
