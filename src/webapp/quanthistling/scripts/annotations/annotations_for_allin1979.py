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

def insert_head(entry, start, end):
    str_head = entry.fullentry[start:end]
    if str_head.startswith("-"):
        #entry.append_annotation(start, start+1, u'boundary', u'dictinterpretation', u"morpheme boundary")
        start += 1
    if str_head.endswith("-"):
        #entry.append_annotation(end-1, end, u'boundary', u'dictinterpretation', u"morpheme boundary")
        end -= 1

    str_head = entry.fullentry[start:end]
    for match in re.finditer(u"-", str_head):
        entry.append_annotation(match.start(0), match.end(0), u'boundary', u'dictinterpretation', u"compound boundary")

    str_head = re.sub("-", "", str_head)
    return functions.insert_head(entry, start, end, str_head)


def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in head_annotations:
        Session.delete(a)

    if entry.fullentry.startswith("dl: ") or entry.fullentry.startswith("pl: "):
        return []

    tabs = [ a for a in entry.annotations if a.value=="tab" ]
    tabs = sorted(tabs, key=attrgetter('start'))

    if len(tabs) != 1:
        functions.print_error_in_entry(entry, "number of tabs is not 1")
        return []

    # Delete this code and insert your code
    head = None
    heads = []
    
    head = insert_head(entry, 0, tabs[0].start)
    heads.append(head)

    return heads


def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    tabs = [ a for a in entry.annotations if a.value=="tab" ]
    tabs = sorted(tabs, key=attrgetter('start'))

    if len(tabs) != 1:
        return

    trans_spa_start = tabs[0].end
    trans = entry.fullentry[trans_spa_start:]

    semicolons = []
    for match in re.finditer(";", trans):
        in_bracket = False
        for match_bracket in re.finditer("\([^)]*\)", trans):
            if match_bracket.start(0) < match.start(0) and match_bracket.end(0) > match.end(0):
                in_bracket = True
        if not in_bracket:
            semicolons.append(match.start(0))        

    if len(semicolons) != 1:
        functions.print_error_in_entry(entry, "cannot split at semicolon")
        return
    spa = trans[:semicolons[0]]
    eng = trans[semicolons[0]+1:]

    trans_eng_start = trans_spa_start + len(spa) + 1

    for (start, end) in functions.split_entry_at(entry, u"(?:, |$)", trans_spa_start, trans_eng_start - 1):
        functions.insert_translation(entry, start, end, lang_iso='spa', lang_doculect='Castellano')
 
    for (start, end) in functions.split_entry_at(entry, u"(?:, |$)", trans_eng_start, len(entry.fullentry)):
        functions.insert_translation(entry, start, end, lang_iso='eng', lang_doculect='Inglés')

def main(argv):

    bibtex_key = u"allin1979"
    
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
