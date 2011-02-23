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

def annotate_crossrefs(entry):
    # delete head annotations
    crossreference_annotations = [ a for a in entry.annotations if a.value=='crossreference']
    for a in crossreference_annotations:
        Session.delete(a)
    
    crossreference_match = re.search(u"\(Vea ([^)]*)\)", entry.fullentry)
    if crossreference_match:
        entry.append_annotation(crossreference_match.start(1), crossreference_match.end(1), u'crossreference', u'dictinterpretation')


def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head']
    for a in head_annotations:
        Session.delete(a)
        
    heads = []

    head_end_pos = functions.get_last_bold_pos_at_start(entry)
    head_start_pos = 0

    if entry.fullentry[0] == "*":
        head_start_pos = 1
        
    if entry.fullentry[head_end_pos-1] == ":":
        head_end_pos = head_end_pos - 1

    start = head_start_pos
    for match in re.finditer(u"(?:, |$)", entry.fullentry[head_start_pos:head_end_pos]):
        end = head_start_pos + match.start(0)
        inserted_head = functions.insert_head(entry, start, end)
        heads.append(inserted_head)
        start = head_start_pos + match.end(0)
    
    return heads

def annotate_pos(entry):
    # delete pos annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)

    head_end_pos = functions.get_last_bold_pos_at_start(entry)
    re_bracket = re.compile(u"\(.*?\)")
    match_bracket = re_bracket.search(entry.fullentry, head_end_pos)
    if match_bracket and match_bracket.start(0) < (head_end_pos + 2) and not re.match(u" =\(Vea ", entry.fullentry[head_end_pos:]):
        entry.append_annotation(match_bracket.start(0)+1, match_bracket.end(0)-1, u'pos', u'dictinterpretation')

def annotate_translations_and_examples(entry):
    # delete pos annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    # delete example annotations
    ex_annotations = [ a for a in entry.annotations if a.value=='example-src' or a.value=='example-tgt']
    for a in ex_annotations:
        Session.delete(a)

    head_end = functions.get_pos_or_head_end(entry)
    if head_end == -1:
        functions.print_error_in_entry(entry, "could not find head")
        return
    
    if head_end >= len(entry.fullentry):
        functions.print_error_in_entry(entry, "head length exceeds entry length")
        return
        
    if entry.fullentry[head_end] == ")":
        head_end = head_end + 1
    
    if head_end < len(entry.fullentry) and entry.fullentry[head_end] == ":":
        head_end = head_end + 1
        
    translation_starts = []
    translation_ends = []

    entry_end = len(entry.fullentry)
    match_crossref = re.search("\(Vea [^\)]*\) ?$", entry.fullentry)
    if match_crossref:
        entry_end = entry_end - len(match_crossref.group(0))

    end = functions.get_first_bold_start_in_range(entry, head_end, entry_end)
    if end == -1:
        end = entry_end
    translation_starts.append(head_end)
    translation_ends.append(end)
    annotate_examples_in_range(entry, head_end, entry_end)

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
    bibtex_key = u"hyde2008"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=95,pos_on_page=8).all()
        #entries = []
        
        startletters = set()
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e)
            annotate_crossrefs(e)
            annotate_translations_and_examples(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))
        
        Session.commit()

if __name__ == "__main__":
    main(sys.argv)