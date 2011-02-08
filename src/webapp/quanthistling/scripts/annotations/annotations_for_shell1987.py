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
#from manualannotations_for_aguiar1994 import manual_entries

def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head']
    for a in head_annotations:
        Session.delete(a)
        
    heads = []

    head_end_pos = functions.get_last_bold_pos_at_start(entry)
    head_start_pos = 0
    
    substr = entry.fullentry[head_start_pos:head_end_pos]
    start = head_start_pos
    for match in re.finditer(r'(?:, ?|$)', substr):
        end = match.start(0)
        inserted_head = functions.insert_head(entry, start, end)
        heads.append(inserted_head)
        start = match.end(0)
    
    return heads

def annotate_pos(entry):
    # delete pos annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)

    head_end_pos = functions.get_last_bold_pos_at_start(entry)
    re_bracket = re.compile(u"\(.*?\)")
    match_bracket = re_bracket.search(entry.fullentry, head_end_pos)
    if match_bracket and match_bracket.start(0) < (head_end_pos + 2):
        entry.append_annotation(match_bracket.start(0)+1, match_bracket.end(0)-1, u'pos', u'dictinterpretation')


def annotate_translations(entry):
    # delete pos annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)
        
    translations_start = functions.get_pos_or_head_end(entry) + 1
    translations_end = len(entry.fullentry)
    
    first_bold_after_pos = functions.get_first_bold_start_in_range(entry, translations_start, translations_end)
    if first_bold_after_pos != -1:
        translations_end = first_bold_after_pos

    start = translations_start
    for match in re.finditer(u"(?:[,;] ?|$)", entry.fullentry[translations_start:translations_end]):
        mybreak = False
        # are we in a bracket?
        for m in re.finditer(r'\(.*?\)', entry.fullentry[translations_start:translations_end]):
            if match.start(0) >= m.start(0) and match.end(0) <= m.end(0):
                mybreak = True
            
        if not mybreak:
            end = match.start(0) + translations_start
            subsubstr = entry.fullentry[start:end]
            if not(re.match(r"\s*$", subsubstr)):
                functions.insert_translation(entry, start, end)
                
            start = match.end(0) + translations_start   

def annotate_examples(entry):
    # delete example annotations
    ex_annotations = [ a for a in entry.annotations if a.value=='example-src' or a.value=='example-tgt']
    for a in ex_annotations:
        Session.delete(a)

    after_head_or_pos = functions.get_pos_or_head_end(entry) + 1
    first_bold_after_pos = functions.get_first_bold_start_in_range(entry, after_head_or_pos, len(entry.fullentry))
    if first_bold_after_pos == -1:
        return
    
    sorted_annotations = [ a for a in entry.annotations if a.value=='bold' and a.start > after_head_or_pos ]
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    i = 0
    start_annotation = i
    end_annotation = i
    while i < len(sorted_annotations):
        # concat successive annotations
        next = False
        if ( i < (len(sorted_annotations))-1 ):
            if ((sorted_annotations[i].end == sorted_annotations[i+1].start) or (sorted_annotations[i].end == (sorted_annotations[i+1].start-1))):
                end_annotation = i + 1
                next = True
        if not next:
            # is there another bold annotation after this one?
            if end_annotation < (len(sorted_annotations)-1):
                entry.append_annotation(sorted_annotations[start_annotation].start, sorted_annotations[end_annotation].end, u'example-src', u'dictinterpretation')
                entry.append_annotation(sorted_annotations[end_annotation].end, sorted_annotations[end_annotation+1].start, u'example-tgt', u'dictinterpretation')
            else:
                entry.append_annotation(sorted_annotations[start_annotation].start, sorted_annotations[end_annotation].end, u'example-src', u'dictinterpretation')
                entry.append_annotation(sorted_annotations[end_annotation].end, len(entry.fullentry), u'example-tgt', u'dictinterpretation')
            start_annotation = i + 1
            end_annotation = i + 1
                
        i = i + 1

def main(argv):
    bibtex_key = u"shell1987"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=9,pos_on_page=2).all()
        #entries = []
        
        startletters = set()
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e)
            annotate_translations(e)
            annotate_examples(e)
            #annotate_crossrefs(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))
        
        Session.commit()

if __name__ == "__main__":
    main(sys.argv)