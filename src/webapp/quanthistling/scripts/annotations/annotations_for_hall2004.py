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

    match_end = re.search("\([^)]*\)?:? ?$", entry.fullentry[:head_end])
    if match_end:
        head_end -= len(match_end.group(0))

    for s, e in functions.split_entry_at(entry, r"(?:/|$)", 0, head_end):
        head = functions.insert_head(entry, s, e)
        heads.append(head)

    return heads


def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    sorted_annotations = [ a for a in entry.annotations if a.value=='newline']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    if len(sorted_annotations) == 0:
        functions.print_error_in_entry(entry, "Could not find newline in entry")
        return

    translation_start = sorted_annotations[0].end
    translation_end = len(entry.fullentry)
    match_quotes = re.search("\"([^\"]*)\"", entry.fullentry[translation_start:])
    if not match_quotes:
        functions.print_error_in_entry(entry, "Could not find quotes")
        return
    else:
        translation_end = translation_start + match_quotes.end(1)
        translation_start = translation_start + match_quotes.start(1)

    for s, e in functions.split_entry_at(entry, r"(?:[;,] |$)", translation_start, translation_end):
        functions.insert_translation(entry, s, e)

 
def main(argv):

    bibtex_key = u"hall2004"
    
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
            annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
