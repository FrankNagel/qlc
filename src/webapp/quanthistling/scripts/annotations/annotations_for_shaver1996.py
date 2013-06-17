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
    head = None
    heads = []
    
    head_end = functions.get_last_bold_pos_at_start(entry)
    head_all = entry.fullentry[:head_end]
    head_all = head_all.rstrip()
    
    head_start = 0
    for match in re.finditer("(?:/|$)", head_all):
        head_end = match.start(0)
        h = functions.insert_head(entry, head_start, head_end)
        heads.append(h)
        head_start = match.end(0)

    return heads


def annotate_pos(entry):
    # delete pos annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)

    # Delete this code and insert your code
    newline_annotations = [ a for a in entry.annotations if a.value=='newline']
    newline_annotations = sorted(newline_annotations, key=attrgetter('start'))
    
    if len(newline_annotations) < 2:
        functions.print_error_in_entry(entry)
        return
    else:
        first_newline = newline_annotations[1]
    
    first_line = entry.fullentry[:first_newline.start]
    
    match_pos = re.search("\(([^)]{1,8})\)", first_line)
    
    if match_pos:
        entry.append_annotation(match_pos.start(1), match_pos.end(1), u"pos", u"dictinterpretation")
    else:
        functions.print_error_in_entry(entry)


def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

 
def main(argv):

    bibtex_key = u"shaver1996"
    
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

        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=73,pos_on_page=2).all()

        startletters = set()
    
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            #annotate_pos(e)
            #annotate_translations(e)
        
        dictdata.startletters = unicode(repr(sorted(list(startletters))))

        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
