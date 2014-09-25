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


def annotate_head(entry):
    # delete head annotations
    head_annotations = [a for a in entry.annotations if a.value == 'head' or
                        a.value == "iso-639-3" or a.value == "doculect" or
                        a.value == 'translation']
    for a in head_annotations:
        Session.delete(a)

    # Delete this code and insert your code
    head = None
    heads = []

    first_italic = functions.get_first_italic_range(entry)
    if first_italic != -1:
        head_end = first_italic[0]
        head = functions.insert_head(entry, 0, head_end)
        heads.append(head)
        trans_start = head_end
        trans_end = len(entry.fullentry)
        trans = entry.fullentry[trans_start:]
        if trans.startswith(u'“') and trans.endswith(u'”'):
            trans_start += 1
            trans_end -= 1

        functions.insert_translation(entry, trans_start, trans_end)

    return heads


def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [a for a in entry.annotations if
                         a.value == 'translation']
    for a in trans_annotations:
        Session.delete(a)


def main(argv):
    bibtex_key = u'harms1993'

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

        entries = Session.query(model.Entry).filter_by(
            dictdata_id=dictdata.id).all()
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=105,pos_on_page=2).all()

        startletters = set()

        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            # annotate_translations(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()


if __name__ == "__main__":
    main(sys.argv)
