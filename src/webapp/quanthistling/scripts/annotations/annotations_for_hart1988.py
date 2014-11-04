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

        match_bracket = re.search(" ?\([^)]*\) ?$", entry.fullentry[start:end])
        if match_bracket:
            end = end - len(match_bracket.group(0))

        head = functions.insert_head(entry, start, end)
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
        # remove italics
        italics = functions.get_list_italic_ranges(entry)
        for i in reversed(italics):
            if i[0] >= last_bold_end and i[1] <= b[0]:
                between = re.sub(entry.fullentry[i[0]:i[1]], "", between)
        # remove brackets
        between = re.sub("\([^)]*\)", "", between)
        between = re.sub(",", "", between)
        between = re.sub("\s+", "", between)
        if between != "":
            break
        heads += _add_head_with_comma(entry, b[0], b[1])
        last_bold_end = b[1]

    return heads

def _add_translation_until_bold(entry, s, e):
    bold_ranges = functions.get_list_ranges_for_annotation(entry, 'bold', s)
    in_brackets = functions.get_in_brackets_func(entry)
    for bold in bold_ranges:
        if not in_brackets(*bold):
            e = min(e, bold[0])
            break
    for t_start, t_end in functions.split_entry_at(entry, ',|$', s, e):
        t_start, t_end, trans = functions.remove_parts(entry, t_start, t_end)
        trans = trans.translate(dict( (ord(c), None) for c in u'?!¿¡'))
        functions.insert_translation(entry, t_start, t_end, trans)

def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    translation_start = functions.get_pos_or_head_end(entry)
    
    # remove brackets at start
    match = re.match(" ?\([^)]*\) ?", entry.fullentry[translation_start:])
    while match:
        translation_start += len(match.group(0))
        match = re.match(" ?\([^)]*\) ?", entry.fullentry[translation_start:])

    # remove italics at start
    italic = functions.get_list_ranges_for_annotation(entry, 'italic', translation_start)
    if italic and italic[0][0]-1 <= translation_start:
        translation_start = italic[0][1]

    # remove brackets at start
    match = re.match(" ?\([^)]*\) ?", entry.fullentry[translation_start:])
    while match:
        translation_start += len(match.group(0))
        match = re.match(" ?\([^)]*\) ?", entry.fullentry[translation_start:])

    for trans_start, trans_end in functions.split_entry_at(entry, r'\d\)|$', translation_start, len(entry.fullentry),
                                                           True):
        _add_translation_until_bold(entry, trans_start, trans_end)

 
def main(argv):

    bibtex_key = u"hart1988"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=30,pos_on_page=19).all()

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
