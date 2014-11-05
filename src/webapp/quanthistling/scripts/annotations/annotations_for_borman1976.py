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
    for match_comma in re.finditer('[,;] ?|$', entry.fullentry[head_start:head_end]):
        end = head_start + match_comma.start(0)
        start = functions.lstrip(entry, start, end, u' -–)"')
        end = functions.rstrip(entry, start, end, ' :-')
        head = entry.fullentry[start:end].replace('-', '')
        head = functions.insert_head(entry, start, end, head)
        start = head_start + match_comma.end(0)
        if head:
            heads.append(head)
    
    return heads


def _split_translations(entry, s, e):
    in_brackets = functions.get_in_brackets_func(entry)
    for num_start, num_end in functions.split_entry_at(entry, r'\d\)|$', s, e, True, in_brackets):
        for t_start, t_end in functions.split_entry_at(entry, r',|:|$', num_start, num_end, False, in_brackets):
#            t_end = functions.rstrip(entry, t_start, t_end, ' :')
            t_start, t_end = functions.strip(entry, t_start, t_end, u' ¡¿"', ' .!?"')
            translation = entry.fullentry[t_start:t_end].replace('"', '')
            functions.insert_translation(entry, t_start, t_end, translation)

def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [a for a in entry.annotations if a.value == 'translation']
    for a in trans_annotations:
        Session.delete(a)

    trans_start = max(functions.get_head_end(entry),
                      functions.get_first_bold_in_range(entry, 0, len(entry.fullentry))[1])
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
