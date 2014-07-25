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
    head_annotations = [ a for a in entry.annotations if a.value=='head' or
                         a.value=='iso-639-3' or a.value=='doculect']
    for a in head_annotations:
        Session.delete(a)
        
    # Delete this code and insert your code
    head = None
    heads = []
    
    head_end = functions.get_last_bold_pos_at_start(entry)
    head = functions.insert_head(entry, 0, head_end)

    heads.append(head)

    return heads


def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    head_end = functions.get_head_end(entry)

    bolds = functions.get_list_ranges_for_annotation(entry, 'bold',
                                                     start=head_end)
    if len(bolds) < 2:
        functions.print_error_in_entry(entry, 'less than two translations')
    elif len(bolds) > 2:
        functions.print_error_in_entry(entry, 'more than two translations.'
                                              ' Only "Esp." and "Port." were annotated')
    else:
        for i, bold in enumerate(bolds):
            trans_start = bold[1]
            try:
                trans_end = bolds[i + 1][0]
            except IndexError:
                trans_end = len(entry.fullentry)

            bold_face = entry.fullentry[bold[0]:bold[1]]

            if re.match(r'\s*Esp\.', bold_face):
                functions.insert_translation(entry, trans_start, trans_end,
                                             lang_iso='spa',
                                             lang_doculect='Español')
            elif re.match(r'\s*Port\.', bold_face):
                functions.insert_translation(entry, trans_start, trans_end,
                                             lang_iso='por',
                                             lang_doculect='Português')
            else:
                functions.print_error_in_entry(entry, 'unknown translation')
            trans_start = bold[1]


def main(argv):

    bibtex_key = u'ericksonerickson1993'
    
    if len(argv) < 2:
        print 'call: annotations_for%s.py ini_file' % bibtex_key
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=1,pos_on_page=1).all()

        startletters = set()
    
        for e in entries:
            # print 'current page: %i, pos_on_page: %i' % (e.startpage, e.pos_on_page)
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
