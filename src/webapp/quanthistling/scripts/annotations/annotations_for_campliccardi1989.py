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
#        t_start, t_end, _ = functions.remove_parts(entry, t_start, t_end)
#        t_start, t_end = functions.strip(entry, t_start, t_end, u'
        
        functions.insert_translation(entry, t_start, t_end)

    ## start = s
    ## for match_comma in re.finditer(r'(?:; ?|$)', entry.fullentry[s:e]):
    ##     end = s + match_comma.start(0)
    ##     functions.insert_translation(entry, start, end)
    ##     start = s + match_comma.end(0)


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
    offset = 0
    ignore_this = [u'-']
    for c in entry.fullentry[:head_end]:
        if c in ignore_this:
            offset += 1
        else:
            break
    head_start += offset
    head = functions.insert_head(entry, head_start, head_end)

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
