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

#find end of translation as first occurence of '-Usase'
usase_regex = re.compile(u'[-–]Usase')
def find_usase_start(entry, start, end):
    #when a translation contains only a 'usase' this should be used as translation (including the 'usase')
    #according to clinares; accordingly don't dismiss this part.
    #if entry.fullentry[start:].startswith('Usase'): # '-' gets stripped from translation if '-' is in first position
    #    return start
    match = usase_regex.search(entry.fullentry, start)
    if match is None or match.start() >= end:
        return end
    return match.start()

def get_max_head_end(entry):
    max_head_end = -1
    for match_max_head_end in re.finditer(u" [-:–][U ]", entry.fullentry):
        #print match_max_head_end.start(0)
        if re.search(u"\[[^\]]+\]", entry.fullentry):
            for bracket in re.finditer(u"\[[^\]]+\]", entry.fullentry):
                if not (match_max_head_end.start(0) >= bracket.start(0) and match_max_head_end.end(0) <= bracket.end(0)):
                    if max_head_end == -1:
                        max_head_end = match_max_head_end.start(0)
        elif max_head_end == -1:
            max_head_end = match_max_head_end.start(0)
    return max_head_end
    
#def get_max_head_end(entry):
#    examples_start = entry.fullentry.find("‹")
#    if examples_start == -1:
#        examples_start = len(entry.fullentry)
#        
#    head_end = functions.get_last_bold_end_in_range(entry, 0, examples_start)
    
    
def annotate_heads_and_crossrefs(entry):
    # delete head annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='crossreference' or a.value=='boundary' or a.value=='doculect' or a.value=='iso-639-3']
    for a in head_annotations:
        Session.delete(a)
        
    heads = []
    #match_max_head_end = re.search(u"(?<!^)[-:–]", entry.fullentry)
    max_head_end = get_max_head_end(entry)
    
    if max_head_end == -1:
        match_crossref = re.search(u"[Vv]éase(?: bajo)? (.*)", entry.fullentry)
        if match_crossref:
            entry.append_annotation(match_crossref.start(1), match_crossref.end(1), u'crossreference', u'dictinterpretation')
            max_head_end = match_crossref.start(1)
        else:
            print "No head end found for entry: " + entry.fullentry.encode("utf-8")
            print "    Page: %i, Pos: %i" % (entry.startpage, entry.pos_on_page)
            max_head_end = len(entry.fullentry)
            #return heads
    else:
        annotate_additional_crossrefs(entry)

    sorted_annotations = [ a for a in entry.annotations if a.value=='bold' and a.end < max_head_end ]
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    for a in sorted_annotations:        
        head = entry.fullentry[a.start:a.end]
        if head.startswith("-"):
            inserted_head = functions.insert_head(entry, a.start, a.end, head[1:])
            entry.append_annotation(a.start, a.start+1, u'boundary', u'dictinterpretation', u"morpheme boundary")
            heads.append(inserted_head)
        else:
            inserted_head = functions.insert_head(entry, a.start, a.end)
            heads.append(inserted_head)
    
    return heads

def annotate_additional_crossrefs(entry):
    italic = functions.get_list_ranges_for_annotation(entry, 'italic')
    for start, end in italic:
        snip = entry.fullentry[start:end+2].strip()
        if not snip.startswith(u'sino\u0301n. '):
            continue
        start = end+1
        end = entry.fullentry.find('.', start)
        if end == -1:
            end = len(entry.fullentry)
        cr_start = start
        pattern = re.compile(u'; |$| sino\u0301n| sinón')
        for match in pattern.finditer(entry.fullentry, start, end):
            cr_start, cr_end, cr = functions.remove_parts(entry, cr_start, match.start())
            for invalid in  (u'Ve\u0301ase bajo ', u'Ve\u0301ase ', u'Vease ', u'Vea\u0301se ', u'Ve\u0301a\u0301se ', u'-'):
                if cr.startswith(invalid):
                    cr_start += len(invalid)
                    cr = cr[len(invalid):]
            if cr.strip():
                if len(cr) < 35: #constant derived from data to sift out bogus crossrefs
                    entry.append_annotation(cr_start, cr_end, u'crossreference', u'dictinterpretation', cr)
                else:
                    functions.print_error_in_entry(entry, 'skipping long crossref: ' + cr.encode('utf8'))
                    break
            cr_start = match.end()
            
def annotate_pos(entry):
    # delete pos annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)
        
    for match_pos_range in re.finditer(u"(?:;|^)[^:]+:", entry.fullentry):
        sorted_annotations = [ a for a in entry.annotations if a.value=='italic' and a.start >= match_pos_range.start(0) and a.end <= match_pos_range.end(0) ]
        sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
        for a in sorted_annotations:
            mybreak = False
            for bracket in re.finditer(u"\[[^\]]+\]", entry.fullentry):
                if a.start >= bracket.start(0) and a.end <= bracket.end(0):
                    mybreak = True
            if not mybreak:
                entry.append_annotation(a.start, a.end, u'pos', u'dictinterpretation')

def annotate_translations(entry):
    # delete pos annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    translations_starts = []
    translations_ends = []
    
    
    if re.search(u"\d :", entry.fullentry):
        for match_translation in re.finditer(u"\d :([^‹]+)[‹$]", entry.fullentry):
            translations_starts.append(match_translation.start(1))
            translations_ends.append(match_translation.end(1))
    else:
        max_head_end = get_max_head_end(entry)
        if max_head_end != -1:
            re_translation = re.compile(u"[-:–]([^‹;]+)(?:‹|;|$)")
            match_translation = re_translation.search(entry.fullentry, max_head_end)
            if match_translation:
                translations_starts.append(match_translation.start(1))
                translations_ends.append(match_translation.end(1))
            
    for i in range(len(translations_starts)):
        substr = entry.fullentry[translations_starts[i]:translations_ends[i]]
        start = translations_starts[i]
        for match in re.finditer(u"(?: : ?|$)", substr):
            end = match.start(0) + translations_starts[i]
            subsubstr = entry.fullentry[start:end]
            if not(re.match(r"\s*$", subsubstr)):
                match_star = re.match(" ?\*", subsubstr)
                if match_star:
                    start += len(match_star.group(0))
                end = find_usase_start(entry, start, end)
                functions.insert_translation(entry, start, end)
                
            start = match.end(0) + translations_starts[i]

def annotate_examples(entry):
    # delete example annotations
    ex_annotations = [ a for a in entry.annotations if a.value=='example-src' or a.value=='example-tgt']
    for a in ex_annotations:
        Session.delete(a)
        
    for match in re.finditer(u"‹([^›]+?)›", entry.fullentry):
        sorted_annotations = [ a for a in entry.annotations if a.value=='bold' and a.start >= match.start(0) and a.end <= match.end(0) ]
        sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
        if len(sorted_annotations) > 0:
            last_bold_annotations = sorted_annotations.pop()
            entry.append_annotation(match.start(1), last_bold_annotations.end, u'example-src', u'dictinterpretation')
            entry.append_annotation(last_bold_annotations.end, match.end(1), u'example-tgt', u'dictinterpretation')
        else:
            print "Found example but no bold in: " + entry.fullentry.encode("utf-8")
            print "    Page: %i, Pos: %i" % (entry.startpage, entry.pos_on_page)


def main(argv):
    bibtex_key = u"loriot1993"
    
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
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=92,pos_on_page=8).all()
        #entries = []
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=166,pos_on_page=9).all()
        
        startletters = set()
        for e in entries:
            heads = annotate_heads_and_crossrefs(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            #annotate_pos(e)
            #annotate_translations(e)
            #annotate_examples(e)
            #annotate_crossrefs(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))
        
        Session.commit()

if __name__ == "__main__":
    main(sys.argv)
