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
    if str_head.startswith(" "):
        start += 1
    if str_head.endswith(" "):
        end -= 1

    str_head = entry.fullentry[start:end]
    if str_head.startswith("-"):
        entry.append_annotation(start, start+1, u'boundary', u'dictinterpretation', u"morpheme boundary")
        start += 1
    if str_head.endswith("-"):
        entry.append_annotation(end-1, end, u'boundary', u'dictinterpretation', u"morpheme boundary")
        end -= 1

    return functions.insert_head(entry, start, end)


def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in head_annotations:
        Session.delete(a)
        
    # Delete this code and insert your code
    head = None
    heads = []
    
    head_end = functions.get_last_bold_pos_at_start(entry)
    
    head = insert_head(entry, 0, head_end) 
    heads.append(head)

    return heads


def annotate_pos(entry):
    # delete translation annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)

    head_end = functions.get_head_end(entry)
    italic = functions.get_first_italic_in_range(entry, 0, len(entry.fullentry))
    if italic != -1 and (italic[0]-2) < head_end:
        pos = entry.fullentry[italic[0]:italic[1]]
        pos = re.sub("\. ?$", "", pos)
        entry.append_annotation(italic[0], italic[1], u'pos', u'dictinterpretation', pos)


def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    translation_start = functions.get_pos_or_head_end(entry)
    match_bracket = re.match("\.? ?\([^)]*\)\.? ?", entry.fullentry[translation_start:])
    if match_bracket:
        translation_start += match_bracket.end(0)

    if translation_start >= len(entry.fullentry):
        return

    if re.search("\d\. ", entry.fullentry[translation_start:]):
        for match_number in re.finditer("\d\. ", entry.fullentry[translation_start:]):
            start = translation_start + match_number.end(0)
            match_translation = re.match("([^\.:]*)[\.:]", entry.fullentry[start:])
            end = len(entry.fullentry)
            if match_translation:
                end = start + match_translation.end(1)
            for s, e in functions.split_entry_at(entry, r"(?:[;,] |$)", start, end):
                translation = entry.fullentry[s:e]
                functions.insert_translation(entry, s, e, translation.lower())
    else:
        match_translation = re.match("([^\.:]*)[\.:]", entry.fullentry[translation_start:])
        end = len(entry.fullentry)
        if match_translation:
            end = translation_start + match_translation.end(1)
        for s, e in functions.split_entry_at(entry, r"(?:[;,] |$)", translation_start, end):
            translation = entry.fullentry[s:e]
            functions.insert_translation(entry, s, e, translation.lower())
 
def main(argv):

    bibtex_key = u"dooley2006"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=1,pos_on_page=4).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e)
            annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
