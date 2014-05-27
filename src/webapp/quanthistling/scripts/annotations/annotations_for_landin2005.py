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

def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in head_annotations:
        Session.delete(a)
        
    # Delete this code and insert your code
    heads = []

    head_end = functions.get_last_bold_pos_at_start(entry)

    head = functions.insert_head(entry, 0, head_end)
    if head is None:
        functions.print_error_in_entry(entry, "head is None")
    else:
        heads.append(head)

    return heads

def annotate_pos(entry):
    #delete pos annotations
    pos_annotations = [a for a in entry.annotations if a.value==u'pos']
    for a in pos_annotations:
        Session.delete(a)

    for match in re.finditer(r'(?<=\()(.*?)(?:\) |$)', entry.fullentry):
        pos_start = match.regs[1][0]
        pos_end = match.regs[1][1]
        entry.append_annotation(pos_start, pos_end, u'pos', u'dictinterpretation')


def annotate_translation(entry):
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    poses = functions.get_list_ranges_for_annotation(entry, 'pos')
    poses = [(e[0], e[1]) for e in poses]
    poses = list(set(poses))
    for pos in poses:
        newlines = functions.get_list_ranges_for_annotation(entry, 'newline',
                                                            pos[1])
        trans_start = pos[1]+1
        if len(newlines) > 0:
            trans_end = newlines[0][0]
        else:
            trans_end = len(entry.fullentry)

        for (s, e) in functions.split_entry_at(entry, r"(?:, |$)", trans_start,
                                               trans_end):
            functions.insert_translation(entry, s, e)


def main(argv):

    bibtex_key = u"landin2005"
    
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
        (model.Book, model.Dictdata.book_id==model.Book.id)
        ).filter(model.Book.bibtex_key==bibtex_key).all()

    for dictdata in dictdatas:

        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        # entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=8,pos_on_page=5).all()

        startletters = set()
    
        for e in entries:
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
