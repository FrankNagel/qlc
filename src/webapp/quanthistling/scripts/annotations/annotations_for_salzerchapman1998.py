# -*- coding: utf8 -*-

import sys
import os
sys.path.append(os.path.abspath('.'))

# Pylons model init sequence
import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model


from paste.deploy import appconfig

import functions


def annotate_head_and_pos(entry):
    # delete head annotations
    head_annotations = [a for a in entry.annotations if a.value == 'head' or
                        a.value == 'pos' or
                        a.value == 'iso-639-3' or a.value == 'doculect']

    for a in head_annotations:
        Session.delete(a)

    head = None
    heads = []

    head_start = 0

    chars_to_exclude = [u'\'', u'-', u'–']
    chars_to_skip = 0
    for c in entry.fullentry[:5]:
        if c in chars_to_exclude:
            chars_to_skip += 1
        else:
            break

    head_start += chars_to_skip

    first_italic = functions.get_first_italic_range(entry)
    if first_italic != -1:
        head_end = first_italic[0]
    else:
        head_end = functions.get_last_bold_pos_at_start(entry)

    head = functions.insert_head(entry, head_start, head_end)

    if head is not None:
        heads.append(head)

    # add pos
    if first_italic != -1:
        entry.append_annotation(first_italic[0], first_italic[1], u'pos',
                                u'dictinterpretation')

    return heads


def annotate_translation(entry):
    # delete head annotations
    head_annotations = [a for a in entry.annotations if a.value == 'translation']

    for a in head_annotations:
        Session.delete(a)

    trans_start = functions.get_pos_or_head_end(entry)

    trans_end = len(entry.fullentry)
    newlines = functions.get_list_ranges_for_annotation(entry, 'newline')
    if len(newlines) > 0:
        trans_end = newlines[0][0]

    brackets = functions.find_brackets(entry)
    brackets.extend(functions.find_brackets(entry, '[', ']'))
    brackets.sort()
    for t_start, t_end in functions.split_entry_at(entry, '[;,] |$', trans_start, trans_end, False, brackets):
        functions.insert_translation(entry, t_start, t_end)


def main(argv):

    bibtex_key = u'salzerchapman1998'
    
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=45,pos_on_page=2).all()

        startletters = set()
    
        for e in entries:
            # print "current page: %i, pos_on_page: %i" % (e.startpage, e.pos_on_page)
            heads = annotate_head_and_pos(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_translation(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
