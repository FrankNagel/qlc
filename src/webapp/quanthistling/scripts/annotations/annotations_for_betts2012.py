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
        
    # Delete this code and insert your code
    head = None
    heads = []
    
    head_end = functions.get_last_bold_pos_at_start(entry)
    head_all = entry.fullentry[:head_end]
    head_all = head_all.rstrip()

    if "(Tenh)" in head_all or "(K)" in head_all or "(Uru)" in head_all or "(Am)" in head_all:
        return True, []
    
    head = insert_head(entry, 0, head_end)
    heads.append(head)

    return False, heads


def annotate_pos(entry):
    # delete translation annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)

    head_end = functions.get_head_end(entry)
    italic = functions.get_first_italic_in_range(entry, 0, len(entry.fullentry))
    if italic != -1:
        entry.append_annotation(italic[0], italic[1], u'pos', u'dictinterpretation')
    else:
        functions.print_error_in_entry(entry, "Could not find italic for POS")

def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    translation_start = functions.get_pos_or_head_end(entry)
    translation_end = len(entry.fullentry)
    italic = functions.get_first_italic_in_range(entry, translation_start, translation_end)
    if italic != -1:
        translation_end = italic[0] - 1

    for numbered_start, numbered_end in functions.split_entry_at(entry, r'[0-9]\) |$',
                                                                 translation_start, translation_end):
        bold = functions.get_first_bold_in_range(entry, numbered_start, numbered_end)
        if bold != -1:
            numbered_end = bold[0] - 1

        #search for start of examples and end translation there
        ex_match = re.compile(",\s*(e\.\s*g\.|i\.\s*e\.)").search(entry.fullentry, numbered_start, numbered_end)
        if ex_match:
            numbered_end = ex_match.start()

        for start, end in functions.split_entry_at(entry, r'[;,] |$', numbered_start, numbered_end):
            functions.insert_translation(entry, start, end)
 
def main(argv):

    bibtex_key = u"betts2012"
    
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
            is_dialect, heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            if not is_dialect:
                annotate_pos(e)
                annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
