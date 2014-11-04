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

    head = functions.insert_head(entry, 0, head_end)
    heads.append(head)

    return heads


def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    translation_start = functions.get_last_bold_pos_at_start(entry) + 1
    translation_end = functions.get_first_bold_start_in_range(entry, translation_start, len(entry.fullentry))
    if translation_end == -1:
        translation_end = len(entry.fullentry)

    match_bracket = re.search("^ ?\([^\)]*\) ?", entry.fullentry[translation_start:translation_end])
    if match_bracket:
        translation_start += len(match_bracket.group(0))

    match_capitals = re.search("^ ?(?:PI|PE) ?", entry.fullentry[translation_start:translation_end])  
    if match_capitals:
        translation_start += len(match_capitals.group(0))

    start = translation_start
    for t_start, t_end in functions.split_entry_at(entry, r'[,;] |/|$', translation_start, translation_end):
        t_start, t_end, translation = functions.remove_parts(entry, t_start, t_end)
        match = re.match(r'\(vr-[it]\.( irr\.)?\)|\(vt\.\)', translation)
        if match:
            translation = translation[len(match.group()):]
        functions.insert_translation(entry, t_start, t_end, translation)

 
def main(argv):

    bibtex_key = u"payne1989"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=381,pos_on_page=28).all()

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
