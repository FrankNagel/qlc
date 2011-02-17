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
    head_annotations = [ a for a in entry.annotations if a.value=='head']
    for a in head_annotations:
        Session.delete(a)
        
    heads = []

    head_end_pos = functions.get_last_bold_pos_at_start(entry)
    head_start_pos = 0
    
    match_bracket = re.search(u" ?\([^)]*\) ?$", entry.fullentry[head_start_pos:head_end_pos])
    if match_bracket:
        head_end_pos = head_end_pos - len(match_bracket.group(0))

    inserted_head = functions.insert_head(entry, head_start_pos, head_end_pos)
    heads.append(inserted_head)
    
    return heads

def annotate_translations_and_examples(entry):
    # delete pos annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    # delete example annotations
    ex_annotations = [ a for a in entry.annotations if a.value=='example-src' or a.value=='example-tgt']
    for a in ex_annotations:
        Session.delete(a)

    head_end = functions.get_last_bold_pos_at_start(entry)
    if head_end == -1:
        functions.print_error_in_entry(entry, "could not find head")
        
    translation_starts = []
    translation_ends = []

    if re.search(r'\d\.(?!\d)', entry.fullentry):
        for match in re.finditer(r'(?<=\d\.(?!\d))(.*?)(?=\d\.(?!\d)|$)', entry.fullentry):
            end = functions.get_first_bold_start_in_range(entry, match.start(1), match.end(1))
            if end == -1:
                end = match.end(1)
            start = match.start(1)
            translation_starts.append(start)
            translation_ends.append(end)
            annotate_examples_in_range(entry, match.start(1), match.end(1))
    else:        
        end = functions.get_first_bold_start_in_range(entry, head_end, len(entry.fullentry))
        if end == -1:
            end = len(entry.fullentry)
        translation_starts.append(head_end)
        translation_ends.append(end)
        annotate_examples_in_range(entry, head_end, len(entry.fullentry))

    for i in range(len(translation_starts)):
        start = translation_starts[i]
        for match in re.finditer(u"(?:, |$)", entry.fullentry[translation_starts[i]:translation_ends[i]]):
            end = translation_starts[i] + match.start(0)
            functions.insert_translation(entry, start, end)
            start = translation_starts[i] + match.end(0)

def annotate_examples_in_range(entry, start, end):

    sorted_annotations = [ a for a in entry.annotations if a.value=='bold' and a.start >=start and a.end<=end ]
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
                entry.append_annotation(sorted_annotations[end_annotation].end, end, u'example-tgt', u'dictinterpretation')
            start_annotation = i + 1
            end_annotation = i + 1
                
        i = i + 1


def main(argv):
    bibtex_key = u"montag2008"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=13,pos_on_page=11).all()
        #entries = []
        
        startletters = set()
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_translations_and_examples(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))
        
        Session.commit()

if __name__ == "__main__":
    main(sys.argv)