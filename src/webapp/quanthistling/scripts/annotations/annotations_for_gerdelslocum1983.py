# -*- coding: utf8 -*-

import sys
import os
sys.path.append(os.path.abspath('.'))

import re

from operator import attrgetter
import difflib

# Pylons model init sequence
import pylons.test

from quanthistling.config.environment import load_environment
from quanthistling.model.meta import Session, metadata
from quanthistling import model

from paste.deploy import appconfig

import functions


def annotate_head(entry):
    # delete head annotations
    annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='doculect' or a.value=='iso-639-3']
    for a in annotations:
        Session.delete(a)

    head = None
    heads = []

    head_end = functions.get_last_bold_pos_at_start(entry)

    part_start = 0
    for separate_head in re.finditer("(?:[,] ?|$)", entry.fullentry[:head_end]):
        part_end = separate_head.start(0)
        #adjust the start of head
        match = re.search(r'[^\W*\-].*[^\W]', entry.fullentry[part_start:part_end])
        if match:
            part_start += match.start(0)
            part_end = part_start + len(match.group(0))
        # ignore_this = ['(', '-']
        # offset = 0
        # if entry.fullentry[part_start:part_end].startswith('-'):
        #     part_start += 1
        # # for c in entry.fullentry[part_start:part_end]:
        # #     if c in ignore_this:
        # #         offset += 1
        # #     else:
        # #         break
        # # part_start += offset
        head = functions.insert_head(entry, part_start, part_end)
        if head is not None:
            heads.append(head)
        part_start = separate_head.end(0)
        
    return heads


def annotate_pos(entry):
    #delete previous existing annotations
    annotations = [a for a in entry.annotations if a.value == 'pos']
    for a in annotations:
        Session.delete(a)

    head_end = functions.get_head_end(entry)
    brackets = re.search(r'\(.*\)', entry.fullentry[head_end:head_end + 20])
    if brackets is not None:
        pos_start = head_end + (brackets.start(0) + 1)
        pos_end = head_end + (brackets.end(0) - 1)
        entry.append_annotation(pos_start, pos_end, u'pos', u'dictinterpretation')


def annotate_translation(entry):
    trans_annotations = [a for a in entry.annotations
                         if a.value == 'translation']

    for a in trans_annotations:
        Session.delete(a)

    trans_start = functions.get_pos_or_head_end(entry)
    if entry.fullentry[trans_start:].startswith(')'):
        trans_start += 1

    newlines = functions.get_list_ranges_for_annotation(entry, 'newline')
    if len(newlines) == 0:
        functions.insert_translation(entry, trans_start, len(entry.fullentry))
    else:
        for i, n in enumerate(newlines):
            period = entry.fullentry.find('.', trans_start, n[0])
            if period == -1:
                trans_end = n[0]
            else:
                trans_end = trans_start + period
            if i == 0:
                functions.insert_translation(entry, trans_start, trans_end)
            else:
                digit = re.search('\d ', entry.fullentry[trans_start:n[0]])
                if digit is not None:
                    trans_start += digit.end(0)
                    functions.insert_translation(entry, trans_start, trans_end)

            trans_start = n[1]


def main(argv):
    bibtex_key = u"gerdelslocum1983"
    
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
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=21,pos_on_page=3).all()
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=2,pos_on_page=2).all())
        # entries.extend(Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=2,pos_on_page=7).all())

        startletters = set()
    
        for e in entries:
            try:
                heads = annotate_head(e)
                if not e.is_subentry:
                    for h in heads:
                        if len(h) > 0:
                            startletters.add(h[0].lower())
                annotate_pos(e)
                annotate_translation(e)
            except TypeError:
                print "   error on startpage: %i, pos_on_page: %i" % (e.startpage, e.pos_on_page)
                raise
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()
    

if __name__ == "__main__":
    main(sys.argv)