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


bracket_pattern = re.compile('[,\d]?\s*(esp|port)?\s*\([^)]*\)')

def annotate_head(entry):
    # delete head annotations
    head_annotations = [a for a in entry.annotations if a.value == 'head' or
                        a.value == 'iso-639-3' or a.value == 'doculect']
    for a in head_annotations:
        Session.delete(a)

    in_brackets = functions.get_in_brackets_func(entry)
    heads = []

    head_start = 0
    smallcaps = functions.get_list_ranges_for_annotation(entry, 'smallcaps')
    trans_end = functions.find_first_point(entry, 0, len(entry.fullentry), in_brackets)
    italics = [i for i in functions.get_list_italic_ranges(entry) if not in_brackets(*i) and i[0]<trans_end]
    if italics:
        head_end = italics[0][0]
    else:
        head_end = functions.get_last_bold_pos_at_start(entry)

    for h_start, h_end in functions.split_entry_at(entry, ',|$', head_start, head_end):
        h_end = functions.find_first(entry, '(', h_start, h_end, in_brackets)
        h_end = next((s[0] for s in smallcaps if s[0]>h_start and s[0] < h_end), h_end)
        h_start, h_end = functions.strip(entry, h_start, h_end, u' -¡¿?!0123456789')
        head = functions.insert_head(entry, h_start, h_end)
        if head:
            heads.append(head)
    return heads


def annotate_pos(entry):
    pos = [a for a in entry.annotations if a.value == 'pos']
    for p in pos:
        Session.delete(p)

    head_end = max(functions.get_head_end(entry),
                   functions.get_last_bold_pos_at_start(entry))
    #ignore a bracket pair
    match = bracket_pattern.match(entry.fullentry, head_end)
    if match:
        head_end = match.end()

    trans_end = functions.find_first_point(entry, 0, len(entry.fullentry))
    italics = [i for i in functions.get_list_italic_ranges(entry, head_end) if i[0] < trans_end]
    if italics and italics[0][0] < head_end+11:
        italic = italics[0]
        entry.append_annotation(italic[0], italic[1], u'pos', u'dictinterpretation')


def annotate_translation(entry):
    # delete translations
    trans = [a for a in entry.annotations if a.value == 'translation']
    for t in trans:
        Session.delete(t)

    trans_start = max(functions.get_pos_or_head_end(entry),
                      functions.get_last_bold_pos_at_start(entry))
    in_brackets = functions.get_in_brackets_func(entry)
    for num_start, num_end in functions.split_entry_at(entry, r'\d |$', trans_start, len(entry.fullentry), True,
                                                       in_brackets):
        num_end = functions.find_first_point(entry, num_start, num_end, in_brackets)
        for t_start, t_end in functions.split_entry_at(entry, r'[,:] |$', num_start, num_end, False, in_brackets):
            t_start, t_end, _ = functions.remove_parts(entry, t_start, t_end)
            t_end = functions.rstrip(entry, t_start, t_end, '0123456789')
            functions.insert_translation(entry, t_start, t_end)
    
 
def main(argv):

    bibtex_key = u"schauer2005"
    
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=22,pos_on_page=1).all()
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=22,pos_on_page=2).all())
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=22,pos_on_page=3).all())

        startletters = set()
    
        for e in entries:
            # print "current page: %i, pos_on_page: %i" % (e.startpage, e.pos_on_page)
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
