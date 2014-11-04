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

chars_to_exclude = [u' ', u'-', u'–', u')']
exclude_mapping = {ord('-'): None}
trans_exclude = dict((ord(c),None) for c in u'[]')

def _adjust_start(entry, start):
    chars_to_skip = 0
    for c in entry.fullentry[start:]:
        if c in chars_to_exclude:
            chars_to_skip += 1
        else:
            break
    return start + chars_to_skip


def annotate_everything(entry):
    # delete head annotations
    heads = [a for a in entry.annotations if a.value == 'head' or
             a.value == 'iso-639-3' or a.value == 'doculect' or
             a.value == 'translation']
    for a in heads:
        Session.delete(a)
        
    # Delete this code and insert your code
    head = None
    heads = []
    
    head_end = functions.get_last_bold_pos_at_start(entry)
    head_start = _adjust_start(entry, 0)
    head_start, head_end, head = functions.remove_parts(entry, head_start, head_end)
    head = head.translate(exclude_mapping)
    head = functions.insert_head(entry, head_start, head_end, head)
    if head:
        heads.append(head)

    newlines = functions.get_list_ranges_for_annotation(entry, 'newline')
    if len(newlines) > 0:
        entry_end = newlines[0][0]
    else:
        entry_end = len(entry.fullentry)

    italic = functions.get_first_italic_in_range(entry, head_end, entry_end)
    if italic != -1:
        trans_start = italic[1]
    else:
        trans_start = head_end


    for p_start, p_end in functions.split_entry_at(entry, r',|/|$', trans_start, entry_end):
        p_start = _adjust_start(entry, p_start)
        p_start, p_end, translation = functions.remove_parts(entry, p_start, p_end)
        translation = translation.translate(trans_exclude)
        functions.insert_translation(entry, p_start, p_end, translation)
    return heads


def main(argv):

    bibtex_key = u"popovichpopovich2005"
    
    if len(argv) < 2:
        print "call: annotations_for%s.py ini_file" % bibtex_key
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=105,pos_on_page=2).all()

        startletters = set()
    
        for e in entries:
            #print 'current page: %i, pos_on_page: %i' % (e.startpage, e.pos_on_page)

            heads = annotate_everything(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
