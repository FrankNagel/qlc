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

    for h_start, h_end in functions.split_entry_at(entry, r', |\(|$', 0, head_end):
        while h_end > 0 and entry.fullentry[h_end-1] in u')- ':
            h_end -= 1
        while h_start < h_end and entry.fullentry[h_start] in u'- ':
            h_start += 1
        head = functions.insert_head(entry, h_start, h_end)
        if head is not None:
            heads.append(head)

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
    trans_annotations = [a for a in entry.annotations if a.value == 'translation']
    for a in trans_annotations:
        Session.delete(a)

    trans_start = max(functions.get_pos_or_head_end(entry) + 1, #skip ')' at end of POS
                      functions.get_first_bold_in_range(entry, 0, len(entry.fullentry))[1])

    newlines = functions.get_list_ranges_for_annotation(entry, 'newline')
    in_brackets = functions.get_in_brackets_func(entry)
    if len(newlines) == 0 or entry.fullentry[trans_start:newlines[0][0]].strip() != '':
        if len(newlines) == 0:
            trans_end = len(entry.fullentry)
        else:
            trans_end = newlines[0][0]
        for t_start, t_end in functions.split_entry_at(entry, r', |$', trans_start, trans_end, in_brackets=in_brackets):
            functions.insert_translation(entry, t_start, t_end)
    else:
        newlines.pop(0)
        for i, n in enumerate(newlines):
            trans_end = n[0]
            digit = re.compile('\d ').search(entry.fullentry, trans_start, trans_end)
            if digit is not None:
                trans_start = digit.end()
                for t_start, t_end in functions.split_entry_at(entry, r', |$', trans_start, trans_end, in_brackets):
                    functions.insert_translation(entry, t_start, t_end)
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
