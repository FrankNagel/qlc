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
from manualannotations_for_fastmowitz2008 import manual_entries

def annotate_dialect(entry):
    # delete head annotations
    dialect_annotations = [ a for a in entry.annotations if a.value=='dialectidentification']
    for a in dialect_annotations:
        Session.delete(a)

    for match in re.finditer(u'\((AN|C|HUA|HUI|P)\)', entry.fullentry):
        if match.group(1) == u'AN':
            entry.append_annotation(match.start(0), match.end(0), u'dialectidentification', u'dictinterpretation', u'Dialecto del río Anasu')
        elif match.group(1) == u'C':
            entry.append_annotation(match.start(0), match.end(0), u'dialectidentification', u'dictinterpretation', u'Dialecto del río Corrientes')
        elif match.group(1) == u'HUA':
            entry.append_annotation(match.start(0), match.end(0), u'dialectidentification', u'dictinterpretation', u'Dialecto del río Huasaga.')
        elif match.group(1) == u'HUI':
            entry.append_annotation(match.start(0), match.end(0), u'dialectidentification', u'dictinterpretation', u'Dialecto del río Huitoyacu')
        elif match.group(1) == u'P':
            entry.append_annotation(match.start(0), match.end(0), u'dialectidentification', u'dictinterpretation', u'Dialecto de Puránchim')

def annotate_stratum(entry):
    # delete stratum annotations
    dialect_annotations = [ a for a in entry.annotations if a.value=='stratum']
    for a in dialect_annotations:
        Session.delete(a)

    for match in re.finditer(u'\(del (?:cast\.( ?[^)]*)|quechua)\)', entry.fullentry):
        if match.group(0) == u'del quechua':
            entry.append_annotation(match.start(0), match.end(0), u'stratum', u'dictinterpretation', u'Quechua loanword')
        elif match.group(1) == u'':
            entry.append_annotation(match.start(0), match.end(0), u'stratum', u'dictinterpretation', u'Spanish loanword')
        else:
            entry.append_annotation(match.start(0), match.end(0), u'stratum', u'dictinterpretation', u'Spanish loanword {0}'.format(match.group(1)))
    
def get_head_end(entry):
    first_italic = functions.get_first_italic_start_in_range(entry, 0, len(entry.fullentry))
    if first_italic == -1:
        pattern = re.compile(u'\((?:sinón\.|vea) ?.*?\)')
        match_link = pattern.search(entry.fullentry)
        if match_link:
            first_italic = match_link.start(0)
        else:
            first_italic = len(entry.fullentry)

    sorted_annotations = [ a for a in entry.annotations if a.value=='bold' and a.start <= first_italic]
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))

    last_bold_end = -1
    at_start = True

    for a in sorted_annotations:
        if at_start and(a.start <= (last_bold_end + 8)):
            last_bold_end = a.end
        else:
            at_start = False
        
    # brackets after head belong to head, if they are not spanish loanword indication
    for m in re.finditer(u"\((?!del cast\.)[^)]*?\)", entry.fullentry[:first_italic]):
        if m.start(0) <= (last_bold_end + 1) and m.end(0) > last_bold_end:
            last_bold_end = m.end(0)
            
    return last_bold_end
    

def annotate_crossrefs(entry):
    # delete crossref annotations
    crossref_annotations = [ a for a in entry.annotations if a.value=='crossreference']
    for a in crossref_annotations:
        Session.delete(a)

    for match_crossref in re.finditer(u'\((?:vea|sinón\.) (.*?)\)', entry.fullentry):
        start = match_crossref.start(1)
        substr = entry.fullentry[match_crossref.start(1):match_crossref.end(1)]
        for match in re.finditer(r', ?', substr):
            end = match.start(0) + match_crossref.start(1)
            entry.append_annotation(start, end, u'crossreference', u'dictinterpretation')
            start = match.end(0) + match_crossref.start(1)
        end = match_crossref.end(1)
        entry.append_annotation(start, end, u'crossreference', u'dictinterpretation')
        #entry.append_annotation(match.start(1), match.end(1), u'crossreference', u'dictinterpretation')

def annotate_head(entry):
    # delete pos annotations
    head_annotations = [ a for a in entry.annotations if a.value=='head' or a.value=='doculect' or a.value=='iso-639-3']
    for a in head_annotations:
        Session.delete(a)
        
    heads = []

    head_end = get_head_end(entry)
    if head_end == -1:
        return []
    
    substr = entry.fullentry[:head_end]

    start = 0
    for match in re.finditer(r' ?(?:, ?|; ?|$)', substr):
        mybreak = False
        # are we in a bracket?
        for m in re.finditer(r'\(.*?\)', substr):
            if match.start(0) >= m.start(0) and match.end(0) < m.end(0):
                mybreak = True
            
        if not mybreak:
            end = match.start(0)
            match_dialect = re.search(u"\((?:HUI|AN|C|HUA|P)\) ?$", entry.fullentry[start:end])
            if match_dialect:
                end = start + match_dialect.start(0)
            functions.insert_head(entry, start, end)
            #entry.append_annotation(start, end, u'head', u'dictinterpretation')
            heads.append(entry.fullentry[start:end])
            start = match.end(0)
        
    return heads
                
def annotate_pos(entry):
    # delete pos annotations
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    for a in pos_annotations:
        Session.delete(a)
    
    sorted_annotations = [ a for a in entry.annotations if a.value=='italic']
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    if len(sorted_annotations) > 0:
        italic_annotation = sorted_annotations[0]
    else:
        return
    
    # get end of bold
    bold_end_pos = get_head_end(entry)
    # is pos if after head and before italic is only empty space or one or more brackets
    if re.match(r'( ?\(.*?\))* *$', entry.fullentry[bold_end_pos:italic_annotation.start]):
        pos_start = italic_annotation.start
        pos_end = italic_annotation.end
        start = pos_start
        substr = entry.fullentry[pos_start:pos_end]
        for match in re.finditer(r', ?', substr):
            end = match.start(0) + pos_start
            entry.append_annotation(start, end, u'pos', u'dictinterpretation')
            start = match.end(0) + pos_start
        end = pos_end
        entry.append_annotation(start, end, u'pos', u'dictinterpretation')

def annotate_examples_in_range(entry, start, end):

    sorted_annotations = [ a for a in entry.annotations if a.value=='bold' and a.start >=start and a.end<=end ]
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    i = 0
    start_annotation = i
    end_annotation = i
    while i < len(sorted_annotations):
        # concat successive bold annotations
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

def annotate_translations(entry):
    # delete translation annotations
    trans_annotations = [ a for a in entry.annotations if a.value=='translation']
    for a in trans_annotations:
        Session.delete(a)

    ex_annotations = [ a for a in entry.annotations if a.value=='example-src' or a.value=='example-tgt']
    #print entry.fullentry.encode('utf-8')
    for a in ex_annotations:
        #print a.string
        Session.delete(a)

    head_and_pos_end = 0
    pos_annotations = [ a for a in entry.annotations if a.value=='pos']
    if (len(pos_annotations) > 0):
        head_and_pos_end = pos_annotations[-1].end
    else:
        head_and_pos_end = get_head_end(entry)
        if head_and_pos_end == -1:
            print "no head and pos end found"
            print entry.fullentry.encode('utf-8')
            head_and_pos_end = len(entry.fullentry)
    
    # get all bold annotations after head
    sorted_annotations = [ a for a in entry.annotations if a.value=='bold' and a.start >=  head_and_pos_end ]
    sorted_annotations = sorted(sorted_annotations, key=attrgetter('start'))
    
    #print head_and_pos_end 
    translation_starts = []
    translation_ends = []
    
    example_starts = []
    example_ends = []

    if re.search(r'\d\.(?!\d)', entry.fullentry):
        for match in re.finditer(r'(?<=\d\.(?!\d))(?: ?\(.*?\) ?)?(.*?)(?:\d\.(?!\d)|$)', entry.fullentry):
            end = match.end(1)
            start = match.start(1)
            translation_starts.append(start)
            translation_ends.append(end)
    else:        
        translation_starts.append(head_and_pos_end)
        translation_ends.append(len(entry.fullentry))

    for i in range(len(translation_starts)):
        start = translation_starts[i]
        end = translation_ends[i]
        # remove sinon and vea brackets
        pattern = re.compile(u'\((?:sinón\.|vea) ?.*?\)')
        match_link = pattern.search(entry.fullentry, start, end)
        if match_link:
            end = match_link.start(0)
    
        first_bold_in_translation = functions.get_first_bold_start_in_range(entry, start, end)
        if first_bold_in_translation > -1:
            annotate_examples_in_range(entry, first_bold_in_translation, end)
            end = first_bold_in_translation
            
        substr = entry.fullentry[start:end]
        
        current_start = translation_starts[i]
        current_end = 0

        for match in re.finditer(r'[;,] ?', substr):
            mybreak = False
            #print "match in " + substr
            # are we in a bracket?
            for m in re.finditer(r'\(.*?\)', substr):
                if match.start(0) >= m.start(0) and match.end(0) <= m.end(0):
                    mybreak = True
                
            if not mybreak:
                current_end = match.start(0) + translation_starts[i]
                subsubstr = entry.fullentry[current_start:current_end]
                if not(re.match(r"\s*$", subsubstr)):
                    functions.insert_translation(entry, current_start, current_end)
                    
                current_start = match.end(0) + translation_starts[i]
        current_end = end
        subsubstr = entry.fullentry[current_start:current_end]
        #print "after post: " + subsubstr.encode('utf-8')
        if not(re.match(r"\s*$", subsubstr)):
            functions.insert_translation(entry, current_start, current_end)
            

def main(argv):
    bibtex_key = u"fastmowitz2008"
    
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

        #print "Processing %s - %s dictdata..." %(dictdata.src_language.langcode, dictdata.tgt_language.langcode)
        entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id).all()
        print len(entries)
        
        #entries = Session.query(model.Entry).filter_by(dictdata_id=dictdata.id,startpage=300,pos_on_page=12).all()
        #entries = []
        
        startletters = set()
        for e in entries:
            heads = annotate_head(e)
            if not e.is_subentry:
                for h in heads:
                    if len(h) > 0:
                        startletters.add(h[0].lower())
            annotate_pos(e)
            #Session.commit()
            annotate_translations(e)
            annotate_crossrefs(e)
            annotate_dialect(e)
            annotate_stratum(e)
            #annotate_examples(e)

        dictdata.startletters = unicode(repr(sorted(list(startletters))))
    
        Session.commit()
    
if __name__ == "__main__":
    main(sys.argv)
