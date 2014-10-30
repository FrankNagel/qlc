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
        
    head = None
    heads = []
    
    head_end = functions.get_last_bold_pos_at_start(entry)
    head_all = entry.fullentry[:head_end]
    head_all = head_all.rstrip()

    head_start = 0
    for match in re.finditer("(?:, ?|$)", head_all):
        head_end = match.start(0)
        head = functions.insert_head(entry, head_start, head_end)
        heads.append(head)
        head_start = match.end(0)

    return heads

def annotate_pos_and_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation' or a.value=='pos' or a.value=='crossreference']
    for a in trans_annotations:
        Session.delete(a)

    translations = []

    italics = functions.get_list_italic_ranges(entry)
    if len(italics) == 0:
        functions.print_error_in_entry(entry, "Could not find italics for pos and translation in entry.")
        return

    translation_start = None
    translation_end = None
    for t in italics:
        if entry.fullentry[t[0]:t[1]].strip() == "V.":
            # a "crossreference" annotation
            entry.append_annotation(t[0], t[1], u"crossreference", u"dictinterpretation")
            translation_end = t[0]
            if translation_start:
                translations.append((translation_start, translation_end))
                translation_start = None
        else:
            # a second pos with a second translation
            entry.append_annotation(t[0], t[1], u"pos", u"dictinterpretation")

            if translation_start:
                translation_end = t[0]
                match_hyphen = re.search(u" — ?$", entry.fullentry[translation_start:translation_end])
                if match_hyphen:
                    translation_end = translation_end - len(match_hyphen.group(0))
                translations.append((translation_start, translation_end))
    
            translation_start = t[1]

    if translation_start:
        translation_end = len(entry.fullentry)
        match_hyphen = re.search(u" — ?$", entry.fullentry[translation_start:translation_end])
        if match_hyphen:
            translation_end = translation_end - len(match_hyphen.group(0))
        translations.append((translation_start, translation_end))

    if len(translations) == 0:
        functions.print_error_in_entry(entry, "Could not find translation in entry.")
        return

    for start, end in translations:
        for num_start, num_end in functions.split_entry_at(entry, r'\d\. |$', start, end):
            for translation_start, translation_end in functions.split_entry_at(entry, r'[,;] |$', num_start, num_end):
                translation = entry.fullentry[translation_start:translation_end].strip()
                if translation and translation[0] != '-':
                    functions.insert_translation(entry, translation_start, translation_end)


def main(argv):

    bibtex_key = u"captain2005"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=13).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            #annotate_pos(e)
            annotate_pos_and_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
