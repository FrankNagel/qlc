# -*- coding: utf8 -*-

import sys, os

sys.path.append(os.path.abspath('.'))

import re

# Pylons model init sequence
import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

from paste.deploy import appconfig

import functions


def _split_translations(entry, s, e):
    #get brackets
    match_brackets = re.search(r'\(.*\)$', entry.fullentry[s:e])
    if match_brackets is not None:
        bracket_start = s + match_brackets.start(0)
    else:
        bracket_start = e

    start = s
    for match_comma in re.finditer("(?:, ?|$)", entry.fullentry[s:e]):
        end = s + match_comma.start(0)
        if end < bracket_start or end == e:
            while start<end and entry.fullentry[start] in ' -':
                start += 1
            functions.insert_translation(entry, start, end)
            start = s + match_comma.end(0)


def annotate_head(entry):
    # delete head annotations
    annotations = [a for a in entry.annotations if a.value == 'head' or
                   a.value == 'iso-639-3' or a.value == 'doculect']
    for a in annotations:
        Session.delete(a)

    # Delete this code and insert your code
    head = None
    heads = []

    head_end = functions.get_last_bold_pos_at_start(entry)
    head_start = 0

    for h_start, h_end in functions.split_entry_at(entry, r',|$', head_start, head_end):
        h_start, h_end, head = functions.remove_parts(entry, h_start, h_end)
        head = head.replace('-', '')
        head = functions.insert_head(entry, h_start, h_end, head)
        if head:
            heads.append(head)

    return heads


def annotate_translation(entry):
    # delete translation annotations
    annotations = [a for a in entry.annotations if a.value == 'translation']
    for a in annotations:
        Session.delete(a)

    trans_start = functions.get_head_end(entry)
    trans = entry.fullentry[trans_start:]

    # ignoring brackets at start of translation
    bracket_at_start = re.search(r'^\s+\(.*\)', trans)
    if bracket_at_start:
        trans_start += bracket_at_start.end(0)

    #ignoring brackets at end of translation
    trans = entry.fullentry[trans_start:]
    bracket_at_end = re.search(r'\(.*\)$', trans)
    if bracket_at_end:
        trans_end = trans_start + bracket_at_end.start(0)
    else:
        trans_end = len(entry.fullentry)

    _split_translations(entry, trans_start, trans_end)


def main(argv):
    bibtex_key = u'buenaventura1993'

    if len(argv) < 2:
        print "call: annotations_for_%s.py ini_file" % bibtex_key
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id, startpage=53, pos_on_page=21).all()
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id, startpage=53, pos_on_page=33).all())

        startletters = set()

        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_translation(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()


if __name__ == "__main__":
    main(sys.argv)
