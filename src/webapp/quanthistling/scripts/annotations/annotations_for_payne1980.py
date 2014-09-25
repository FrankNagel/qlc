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

def _add_head_with_comma(entry, s, e):
    start = s
    heads = []
    for match_comma in re.finditer("(?:, ?|$)", entry.fullentry[s:e]):
        end = s + match_comma.start(0)
        start, end, string = functions.remove_parts(entry, start, end)
        string = string.replace('/', '')
        head = functions.insert_head(entry, start, end, string)
        if head:
            heads.append(head)
        start = s + match_comma.end(0)
    return heads


def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in head_annotations:
        Session.delete(a)
        
    # Delete this code and insert your code
    head = None
    heads = []
    
    bolds = functions.get_list_bold_ranges(entry)
    last_bold_end = 0
    for b in bolds:
        between = entry.fullentry[last_bold_end:b[0]]
        # remove brackets
        between = re.sub("\([^)]*\)", "", between)
        between = re.sub(",", "", between)
        between = re.sub("\s+", "", between)
        if between != "":
            break
        heads += _add_head_with_comma(entry, b[0], b[1])
        last_bold_end = b[1]

    return heads



def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    translation_start = functions.get_head_end(entry)
    
    # remove brackets at start
    match = re.match(" ?\([^)]*\) ?", entry.fullentry[translation_start:])
    while match:
        translation_start += len(match.group(0))
        match = re.match(" ?\([^)]*\) ?", entry.fullentry[translation_start:])

    start = translation_start
    for match in re.finditer("(?:, ?| ?\([^)]*\) ?|$)", entry.fullentry[translation_start:]):
        end = translation_start + match.start(0)
        functions.insert_translation(entry, start, end)
        start = translation_start + match.end(0)

 
def main(argv):

    bibtex_key = u"payne1980"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=42,pos_on_page=18).all()

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
