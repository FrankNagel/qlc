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


def get_first_italic_start_in_range(entry, s, e):
    sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    #re_brackets = re.compile(u"\[.*?\]")

    matches_bracket = re.finditer(u"\[.*?\]", entry.fullentry)
    
    for a in sorted_annotations:
        if a.start >= s and a.start <=e:
            next = False
            for match in matches_bracket:
                if a.start > match.start(0) and a.end < match.end(0):
                    next = True
            if not next:
                return a.start

    return -1

def annotate_crossrefs(entry):
    # delete crossref annotations
    crossref_annotations = [ a for a in entry.annotations if a.value=='crossreference']
    for a in crossref_annotations:
        Session.delete(a)

    match_crossref = re.search(u" ?V\.(.*?)\.?$", entry.fullentry)
    if match_crossref:
        entry.append_annotation(match_crossref.start(1), match_crossref.end(1), u'crossreference', u'dictinterpretation')


def annotate_head(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='boundary' or a.value=="iso-639-3" or a.value=="doculect"]
    for a in head_annotations:
        Session.delete(a)
        
    heads = []

    head_end_pos = functions.get_last_bold_pos_at_start(entry)
    if head_end_pos == -1:
        functions.print_error_in_entry(entry)
    head_start_pos = 0
    
    head = entry.fullentry[head_start_pos:head_end_pos]
    
    match_number = re.search("\d ?", entry.fullentry[head_start_pos:head_end_pos])
    if match_number:
        head_end_pos = head_end_pos - len(match_number.group(0))
        
    match_boundary = re.match("- ?", head)
    match_boundary2 = re.match(".*(-$) ?", head)
    if match_boundary:
        entry.append_annotation(head_start_pos, head_start_pos + len(match_boundary.group(0)), u'boundary', u'dictinterpretation', u"morpheme boundary")
        head = re.sub("^- ?", "", head)
        inserted_head = functions.insert_head(entry, head_start_pos, head_end_pos, head)
    elif match_boundary2:
        entry.append_annotation(head_end_pos - len(match_boundary2.group(1)), head_end_pos, u'boundary', u'dictinterpretation', u"morpheme boundary")
        head = re.sub("-$ ?", "", head)
        inserted_head = functions.insert_head(entry, head_start_pos, head_end_pos, head)
    else:    
        inserted_head = functions.insert_head(entry, head_start_pos, head_end_pos)
    
    if inserted_head != None:
        heads.append(inserted_head)
    
    heads.append(inserted_head)
    
    return heads

def annotate_pos(entry):
    # delete pos annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)
    
    head_end = functions.get_head_end(entry)
    if re.match(" ?\d ?", entry.fullentry[head_end:]):
        for match_number in re.finditer(" ?\d ?", entry.fullentry[head_end:]):
            pos_start = head_end + match_number.end(0)
            match_dot = re.search(u"\.(?= )", entry.fullentry[pos_start:])
            if match_dot:
                pos_end = pos_start + match_dot.end(0)
        
                match_spaces = re.match(u" +", entry.fullentry[pos_start:pos_end])
                if match_spaces:
                    pos_start = pos_start + len(match_spaces.group(0))
                
                match_spaces = re.search(u" +$", entry.fullentry[pos_start:pos_end])
                if match_spaces:
                    pos_end = pos_end - len(match_spaces.group(0))
            
                entry.append_annotation(pos_start, pos_end, u'pos', u'dictinterpretation')
    else:
        pos_start = head_end
        match_dot = re.search(u"\.(?= )", entry.fullentry[pos_start:])
        if match_dot:
            pos_end = pos_start + match_dot.end(0)
    
            match_spaces = re.match(u" +", entry.fullentry[pos_start:pos_end])
            if match_spaces:
                pos_start = pos_start + len(match_spaces.group(0))
            
            match_spaces = re.search(u" +$", entry.fullentry[pos_start:pos_end])
            if match_spaces:
                pos_end = pos_end - len(match_spaces.group(0))
        
            entry.append_annotation(pos_start, pos_end, u'pos', u'dictinterpretation')


def annotate_translations_and_examples(entry):
    # delete pos annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    # delete example annotations
    ex_annotations = [ a for a in entry.annotations if a.value=='example-src' or a.value=='example-tgt']
    for a in ex_annotations:
        Session.delete(a)
        
    match_number = re.search(u"\d ", entry.fullentry)
    if match_number:
        translations_start = match_number.start(0)
    else:
        translations_start = functions.get_pos_or_head_end(entry) + 1

    match_brackets = re.search(u"(?:\d)?\[.*?\] ?", entry.fullentry[translations_start:])
    if match_brackets:
        translations_start = translations_start + len(match_brackets.group(0))
    
    translations_end = len(entry.fullentry)
    
    match_crossref = re.search(u" ?V\..*?$", entry.fullentry)
    if match_crossref:
        translations_end = match_crossref.start(0)
            
    start = translations_start
    
    translation_substring = entry.fullentry[translations_start:translations_end]
    
    translation_starts = []
    translation_ends = []
    if re.search(u"\d ", translation_substring):
        for match in re.finditer(u"\d (?:\w{2,4}\.)?(.*?)(?=\d|$)", entry.fullentry):
            translation_starts.append(match.start(1))
            translation_ends.append(match.end(1))
    else:
        translation_starts.append(translations_start)
        translation_ends.append(translations_end)
        
    for i in range(len(translation_starts)):
        translations_start = translation_starts[i]
        translations_end = translation_ends[i]

        first_italic = get_first_italic_start_in_range(entry, translations_start, translations_end)
        if first_italic != -1:
            annotate_examples_in_range(entry, first_italic, translations_end)
            translations_end = first_italic

        start = translations_start
        for match in re.finditer(u"(?:, ?|$)", entry.fullentry[translations_start:translations_end]):
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


def annotate_examples_in_range(entry, start, end):

    sorted_annotations = [ a for a in entry.annotations if a.value=='italic' and a.start >=start and a.end<=end ]
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
    bibtex_key = u"walton1997"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=101,pos_on_page=23).all()
        #entries = []
        
        startletters = set()
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e)
            annotate_translations_and_examples(e)
            #annotate_examples(e)
            annotate_crossrefs(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))
        
        Session.commit()

if __name__ == "__main__":
    main(sys.argv)