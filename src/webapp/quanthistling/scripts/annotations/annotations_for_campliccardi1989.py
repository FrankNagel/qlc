# -*- coding: utf8 -*-

import sys,os

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
    #ignoring brackets at the end of the translation
    trans = entry.fullentry[s:e]
    at_end = re.search(r' V\. |\(.*\)$', trans)
    if at_end:
        e = s + at_end.start(0)

    for t_start, t_end in functions.split_entry_at(entry, '[,;?] |$', s, e):
        functions.insert_translation(entry, t_start, t_end)


def annotate_head(entry):
    # delete head annotations
    annotations = [a for a in entry.annotations if a.value == 'head' or
                   a.value == 'iso-639-3' or a.value == 'doculect']
    for a in annotations:
        Session.delete(a)

    heads = []

    head_end = functions.get_last_bold_pos_at_start(entry)
    head_start = 0
    for h_start, h_end in functions.split_entry_at(entry, r'[,;] |$', head_start, head_end):
        h_start = functions.lstrip(entry, h_start, h_end, ' -')
        head = functions.insert_head(entry, h_start, h_end)
        if head:
            heads.append(head)
    return heads


def annotate_pos(entry):
    annotations = [a for a in entry.annotations if a.value == 'pos']
    for a in annotations:
        Session.delete(a)

    first_italic = functions.get_first_italic_range(entry)
    if first_italic != -1:
        entry.append_annotation(first_italic[0], first_italic[1], u'pos',
                                u'dictinterpretation')


def annotate_translation(entry):
    # delete translation annotations
    annotations = [a for a in entry.annotations if a.value == 'translation']
    for a in annotations:
        Session.delete(a)

    trans_start = functions.get_pos_or_head_end(entry)
    trans_end = len(entry.fullentry)
    newlines = functions.get_list_ranges_for_annotation(entry, 'newline',
                                                        trans_start)
    if len(newlines) > 0:
        trans_end = newlines[0][0]

    _split_translations(entry, trans_start, trans_end)


def main(argv):
    bibtex_key = u'campliccardi1989'

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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id, startpage=1, pos_on_page=1).all()

        startletters = set()

        for e in entries:
            # print 'current page: %i, pos_on_page: %i' % (e.startpage, e.pos_on_page)
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e)
            annotate_translation(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()


if __name__ == "__main__":
    main(sys.argv)
