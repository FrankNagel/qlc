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
    head_annotations = [a for a in entry.annotations if a.value=='head' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in head_annotations:
        Session.delete(a)
        
    # Delete this code and insert your code
    heads = []

    head_end = functions.get_last_bold_pos_at_start(entry)

    if head_end == -1:
        functions.print_error_in_entry(entry, 'No bold at start. Cannot get head.')
        return heads

    functions.insert_head(entry, 0, head_end)
    return heads


def annotate_pos(entry):
    # delete pos annotations
    head_annotations = [a for a in entry.annotations if a.value=='pos']
    for a in head_annotations:
        Session.delete(a)

    italic = functions.get_first_italic_range(entry)
    if italic is not None:
        (pos_start, pos_end) = italic
        start = pos_start
        for match_comma in re.finditer("(?:, ?|$)", entry.fullentry[pos_start:pos_end]):
            end = pos_start + match_comma.start(0)
            entry.append_annotation(start, end, u'pos', u'dictinterpretation')
            start = pos_start + match_comma.end(0)


def _add_translation_until_bold(entry, s, e):
    bold = functions.get_first_bold_start_in_range(entry, s, e)
    if bold != -1:
        e = bold

    match_bracket = re.match('\w.*\(.*\)$', entry.fullentry[s:e])
    if match_bracket is not None:
        e = s + 0

    start = s
    for match_comma in re.finditer("(?:, ?|$)", entry.fullentry[s:e]):
        end = s + match_comma.start(0)
        functions.insert_translation(entry, start, end)
        start = s + match_comma.end(0)


def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    head_ends = list(set(functions.get_head_ends(entry)))

    for head_end in head_ends:
        translation_start = head_end
        # remove italics at start
        italic = functions.get_first_italic_in_range(entry, translation_start, len(entry.fullentry))
        if italic != -1 and italic[0]-1 <= translation_start:
            translation_start = italic[1]

        if re.search("\d\. ", entry.fullentry[translation_start:]):
            for match_translation in re.finditer("(?<=\d\.)(.*?)(?=\d\.|$)", entry.fullentry[translation_start:]):
                _add_translation_until_bold(entry, translation_start + match_translation.start(1), translation_start + match_translation.end(0))
        else:
            _add_translation_until_bold(entry, translation_start, len(entry.fullentry))

 
def main(argv):

    bibtex_key = u"tripp1995"
    
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=21,pos_on_page=1).all()
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=21,pos_on_page=2).all())
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=21,pos_on_page=4).all())
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=22,pos_on_page=25).all())
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=23,pos_on_page=14).all())
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=32,pos_on_page=16).all()

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
