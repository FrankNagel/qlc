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

chars_to_exclude = [u' ', u'.']


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
        
    head = None
    heads = []
    head_start = 0
    head_end = functions.get_last_bold_pos_at_start(entry)

    starting_brackets = re.search(r'^\(.*\)', entry.fullentry[head_start:head_end])
    ending_brackets = re.search(r'\(.*\)$', entry.fullentry[head_start:head_end])

    if starting_brackets is not None:
        head_start += starting_brackets.end(0)

    if ending_brackets is not None:
        head_end = 0 + ending_brackets.start(0)

    head = functions.insert_head(entry, head_start, head_end)
    heads.append(head)

    return heads


def annotate_pos(entry):
    pos = [a for a in entry.annotations if a.value == 'pos']
    for a in pos:
        Session.delete(a)

    # annotate pos
    italic = functions.get_first_italic_range(entry)

    pos_start = italic[0]
    pos_end = italic[1]

    starting_brackets = re.search(r'^\(.*\)', entry.fullentry[pos_start:pos_end])
    ending_brackets = re.search(r'\(.*\)$', entry.fullentry[pos_start:pos_end])

    if starting_brackets is not None:
        pos_start = italic[0] + starting_brackets.end(0)

    if ending_brackets is not None:
        pos_end = italic[0] + ending_brackets.start(0)

    functions.insert_pos(entry, pos_start, pos_end)


def annotate_translations(entry):
    # delete translation annotations
    trans = [a for a in entry.annotations if a.value == 'translation']
    for a in trans:
        Session.delete(a)

    trans_start = functions.get_pos_or_head_end(entry)
    trans_end = len(entry.fullentry)

    start = trans_start
    for match_colon in re.finditer('(?:; ?|$)', entry.fullentry[
                                                trans_start:trans_end]):

        end = trans_start + match_colon.start(0)
        start = _adjust_start(entry, start)

        starting_brackets = re.search(r'^\(.*\)', entry.fullentry[start:end])
        ending_brackets = re.search(r'\(.*\)$', entry.fullentry[start:end])

        if ending_brackets is not None:
            end = start + ending_brackets.start(0)

        if starting_brackets is not None:
            start += starting_brackets.end(0)

        functions.insert_translation(entry, start, end)
        start = trans_start + match_colon.end(0)


def main(argv):

    bibtex_key = u'peeke2009'
    
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
            annotate_pos(e)
            annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == '__main__':
    main(sys.argv)
