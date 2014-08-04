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


def _handle_translation(entry, s, e):
    #ignoring brackets at the end of the translation
    trans = entry.fullentry[s:e]
    bracket_at_end = re.search(r'\(.*\)\s*$', trans)
    if bracket_at_end:
        e = s + bracket_at_end.start(0)

    functions.insert_translation(entry, s, e)


def annotate_head(entry):
    # delete head annotations
    head_annotations = [a for a in entry.annotations if a.value == 'head' or
                         a.value == 'iso-639-3' or a.value == 'doculect']
    for a in head_annotations:
        Session.delete(a)

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
    # delete pos annotations
    trans_annotations = [a for a in entry.annotations if a.value == 'pos']
    for a in trans_annotations:
        Session.delete(a)

    italics = functions.get_list_italic_ranges(entry)
    for italic in italics:
        italic_string = entry.fullentry[italic[0]:italic[1]]
        if re.match(r'\w+\.', italic_string) and italic_string != 'ej.':
            entry.append_annotation(italic[0], italic[1], u'pos',
                                u'dictinterpretation')


def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [a for a in entry.annotations if a.value == 'translation']
    for a in trans_annotations:
        Session.delete(a)

    poses = functions.get_list_ranges_for_annotation(entry, 'pos')

    for i, pos in enumerate(poses):
        trans_start = pos[1]
        try:
            trans_end = poses[i+1][0]
        except IndexError:
            trans_end = len(entry.fullentry)

        if re.search("\d\. ", entry.fullentry[trans_start:trans_end]):
            for match in re.finditer("(?<=\d\.)(.*?)(?=\d\.|ej\.|$)", entry.fullentry[trans_start:trans_end]):
                start = trans_start + match.start(1)
                end = trans_start + match.end(0)
                _handle_translation(entry, start, end)
        else:
            example = entry.fullentry[trans_start:trans_end].find('ej.')
            if example != -1:
                trans_end = trans_start + example
            _handle_translation(entry, trans_start, trans_end)


def main(argv):

    bibtex_key = u'headland1997'
    
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=216,pos_on_page=16).all()
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=62,pos_on_page=7).all())
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=61,pos_on_page=1).all())

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
