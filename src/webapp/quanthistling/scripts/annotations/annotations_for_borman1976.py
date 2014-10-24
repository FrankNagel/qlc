# -*- coding: utf8 -*-

import sys
import os
sys.path.append(os.path.abspath('.'))

import re

# Pylons model init sequence
import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

from paste.deploy import appconfig

import functions

chars_to_exclude = [u' ', u'-', u'–', u')', u'"']


def _adjust_start(entry, start):
    chars_to_skip = 0
    for c in entry.fullentry[start:]:
        if c in chars_to_exclude:
            chars_to_skip += 1
        else:
            break
    return start + chars_to_skip


def annotate_head(entry):
    # delete head annotations
    head_annotations = [a for a in entry.annotations if a.value == 'head' or
                        a.value == 'iso-639-3' or a.value == 'doculect']
    for a in head_annotations:
        Session.delete(a)
        
    # Delete this code and insert your code
    head = None
    heads = []

    first_bold = functions.get_first_bold_in_range(entry, 0, entry.fullentry)
    head_start = first_bold[0]
    head_end = first_bold[1]
    start = head_start
    for match_comma in re.finditer('(?:; ?|$)', entry.fullentry[
                                                 head_start:head_end]):
        end = head_start + match_comma.start(0)
        start = _adjust_start(entry, start)
        head = functions.insert_head(entry, start, end)
        start = head_start + match_comma.end(0)
        heads.append(head)
    
    return heads


def _split_translations(entry, s, e):
    #get brackets
    match_brackets = re.search(r'\(.*\)$', entry.fullentry[s:e])
    if match_brackets is not None:
        bracket_start = s + match_brackets.start(0)
    else:
        bracket_start = e

    start = s
    for match_ord in re.finditer('(?:\d\) ?|$)', entry.fullentry[
                                                 s:bracket_start]):
        end = s + match_ord.start(0)
        if end <= bracket_start or end == e:
            functions.insert_translation(entry, start, end)
            start = s + match_ord.end(0)


def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [a for a in entry.annotations if a.value ==
                         'translation']
    for a in trans_annotations:
        Session.delete(a)

    trans_start = functions.get_head_end(entry)
    trans_end = len(entry.fullentry)
    italic = functions.get_list_ranges_for_annotation(entry, 'italic',
                                                      trans_start, trans_end)
    if len(italic) > 0:
        trans_end = italic[-1][0]

    _split_translations(entry, trans_start, trans_end)

 
def main(argv):

    bibtex_key = u'borman1976'
    
    if len(argv) < 2:
        print 'call: annotations_for_%s.py ini_file' % bibtex_key
        exit(1)

    ini_file = argv[1]    
    conf = appconfig('config:' + ini_file, relative_to='.')
    if not pylons.test.pylonsapp:
        load_environment(conf.global_conf, conf.local_conf)
    
    # Create the tables if they don't already exist
    metadata.create_all(bind=Session.bind)

    dictdatas = Session.query(model.Dictdata).join(
        (model.Book, model.Dictdata.book_id == model.Book.id)
        ).filter(model.Book.bibtex_key == bibtex_key).all()

    for dictdata in dictdatas:

        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id, startpage=1, pos_on_page=1).all()

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
